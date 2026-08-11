"""
Generate decomposed, target-aware Phase-2 rationales with GPT-5.4.

V3 separates verifiable historical evidence from predicted next-interest
directions. The generated ``reasoning_path`` has two blocks:

    <history_evidence>
    - <history SID> => one verifiable observation from history metadata
    </history_evidence>
    <next_interest>
    - [exploit] <history SID> => one strong continuation
    - [explore] <history SID> => one plausible broadening
    - [explore] <history SID> => another distinct broadening
    </next_interest>

The current ReasoningActivationDataset adds the outer ``<think>...</think>`` and
the target SID, so no Phase-2 training-loop change is required.

The generator and reviewer see the held-out target, but the target may guide only
directions naturally supported by history. When no natural bridge exists, the target
is ignored and the history-grounded trace is retained.

Examples:

    # Show one real HF prompt without calling GPT
    python gpt5_regenerate_phase2_process_data_V3.py \
        --category Video_Games --limit 1 --dry-run

    # Generate a 20-row pilot
    python gpt5_regenerate_phase2_process_data_V3.py \
        --category Video_Games --limit 20

    # Full production run
    python gpt5_regenerate_phase2_process_data_V3.py \
        --category Video_Games --out-dir ./regen_phase2_process_V3

Outputs are resume-safe and updated after every completed inference:

    <out-dir>/<Category>.phase2_process.jsonl
    <out-dir>/<Category>.phase2_process.csv
    <out-dir>/<Category>.integrated_narrative.csv

The training-critical columns and filenames remain compatible with V2. The default
output directory is separate so V3 generations cannot overwrite earlier results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from typing import Any

if __package__:
    from . import gpt5_regenerate_phase2_process_data_V2 as v2
else:
    import gpt5_regenerate_phase2_process_data_V2 as v2


HF_REPO = v2.HF_REPO
CATEGORY = v2.CATEGORY
DEFAULT_MODEL = v2.DEFAULT_MODEL
DEFAULT_PER_ENDPOINT = v2.DEFAULT_PER_ENDPOINT
REASONING_EFFORT = v2.REASONING_EFFORT
MAX_COMPLETION_TOKENS = v2.MAX_COMPLETION_TOKENS
MAX_REPAIR_ATTEMPTS = v2.MAX_REPAIR_ATTEMPTS
SCHEMA_VERSION = "phase2_process_v13_history_evidence_next_interest"

ITEM_SID_RE = v2.ITEM_SID_RE
TraceValidationError = v2.TraceValidationError
SECTION_PATTERNS = {
    tag: re.compile(fr"<{tag}>\s*(.*?)\s*</{tag}>", re.DOTALL)
    for tag in ("history_evidence", "next_interest")
}


OUTPUT_FORMAT = """<history_evidence>
- HISTORY_SID(S) => verifiable observation from the cited history metadata
</history_evidence>
<next_interest>
- [exploit] HISTORY_SID(S) => strongest supported continuation
- [explore] HISTORY_SID(S) => distinct plausible broadening
- [explore] HISTORY_SID(S) => another distinct broadening
</next_interest>"""


GENERATOR_SYSTEM_PROMPT = (
    "Separate verifiable historical evidence from predicted next-interest directions. "
    "The evidence block must be entailed only by HISTORY and must contain no user-level "
    "preference inference. The visible target may guide one natural next-interest "
    "direction but must never affect the evidence block or dominate the prediction. "
    "Every output line must cite exact full SID tokens copied verbatim from HISTORY; "
    "positional references are forbidden. Output only the required two-block trace."
)


GENERATOR_PROMPT = """Given the user history and held-out target below, write a concise
two-stage reasoning trace.

HISTORY:
{history_block}

HELD-OUT TARGET (visible to the teacher; never identify it in the output):
{target_block}

Use this structure:
{output_format}

Requirements:
1. <history_evidence> normally contains 1-3 concise, independently verifiable observations
    grounded only in cited HISTORY and its supplied metadata. Describe item attributes and
    explicit repetition or co-occurrence. Do not infer user preference, interest, openness,
    motivation, engagement strength, or likely next behavior. Never imply purchase or
    ownership. TARGET must not influence this block.
2. <next_interest> normally contains three genuinely different predicted interest directions
    and includes both
   [exploit] and [explore]. Add a fourth only for a clearly independent history-supported
   direction. Let the evidence determine the mode balance; do not add filler.
3. TARGET may inform a direction only when HISTORY supports it. It must not suppress other
   reasonable history-supported directions. If the connection is weak, ignore TARGET rather
   than forcing an explanation; always retain an honest trace.
4. Be concise: each line states one main claim in one sentence. Keep only discriminative
    attributes, merge overlapping evidence, and avoid feature inventories, repeated
    qualifications, or restating evidence as a prediction.
5. Every history-evidence line and every next-interest line after its [exploit]/[explore]
    label must begin with one or more exact full SIDs copied verbatim from HISTORY, followed
    by "=>". Use the complete <a_...><b_...><c_...> token sequence each time. Never use
    positions or aliases such as "1", "1, 2", "HISTORY_4", or "item 3"; never abbreviate a
    SID.
6. Do not cite the target SID, reveal item titles or identifying names, predict an exact next
    item, or emit behavior/interest/intent blocks. Output only <history_evidence> and
    <next_interest>."""


REVIEWER_SYSTEM_PROMPT = (
    "Audit a two-stage recommendation trace for factual history grounding, calibrated "
    "next-interest predictions, target bias, and exact history-SID citations. Evidence "
    "must be verifiable from HISTORY alone and contain no user-level inference. Replace "
    "every positional reference with the corresponding full SID copied verbatim from "
    "HISTORY. Always output only corrected history_evidence and next_interest blocks."
)


REVIEWER_PROMPT = """Fix the candidate trace.

HISTORY:
{history_block}

HELD-OUT TARGET (visible to the teacher; never identify it in the output):
{target_block}

CANDIDATE:
{candidate}

VALIDATION ISSUE:
{validation_issue}

For an accepted row, use exactly this format:
{output_format}

Audit and repair these conditions:
1. Use 1-3 history-evidence lines containing only facts verifiable from cited HISTORY and its
    metadata. Remove every user-level preference, interest, openness, motivation, engagement,
    or future-behavior inference from this block. TARGET must not influence the evidence.
2. Prefer three genuinely distinct next-interest predictions containing both [exploit] and
    [explore]. Retain an extra line only for an independent history-supported direction.
3. Preserve reasonable history-supported alternatives. Let TARGET inform only a natural
   direction; if its bridge is weak, ignore it instead of distorting the trace.
4. Every history-evidence line and every next-interest line after its mode label must start
    with one or more exact <a_...><b_...><c_...> SIDs copied verbatim from HISTORY, then
    "=>". Replace numeric positions, HISTORY_N aliases, item labels, or abbreviated SIDs.
    Never cite the target SID.
5. Compress each line to one main claim: merge overlap, retain only discriminative details,
   and remove repeated qualifications or feature lists.
6. Do not imply purchase/ownership, reveal identifying item names or TARGET, or predict an
    exact item. Remove behavior/interest/intent blocks and always return nonempty
    <history_evidence> and <next_interest> blocks."""


def generation_signature(model: str, review: bool) -> str:
    payload = {
        "schema": SCHEMA_VERSION,
        "model": model,
        "review": review,
        "reasoning_effort": REASONING_EFFORT,
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
        "generator": GENERATOR_SYSTEM_PROMPT + GENERATOR_PROMPT,
        "reviewer": REVIEWER_SYSTEM_PROMPT + REVIEWER_PROMPT,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:20]


def generator_prompt(history_block: str, target_block: str) -> str:
    return GENERATOR_PROMPT.format(
        history_block=history_block,
        target_block=target_block,
        output_format=OUTPUT_FORMAT,
    )


def reviewer_prompt(
    history_block: str,
    target_block: str,
    candidate: str,
    validation_issue: str,
) -> str:
    return REVIEWER_PROMPT.format(
        history_block=history_block,
        target_block=target_block,
        candidate=candidate,
        validation_issue=validation_issue,
        output_format=OUTPUT_FORMAT,
    )


def _extract_sections(raw: str) -> dict[str, str]:
    text = raw.strip()
    sections = {}
    positions = []
    remainder = text
    for tag, pattern in SECTION_PATTERNS.items():
        matches = list(pattern.finditer(text))
        if len(matches) != 1:
            raise TraceValidationError(f"expected one <{tag}>...</{tag}> block")
        match = matches[0]
        sections[tag] = match.group(1).strip()
        positions.append((tag, match.start()))
        remainder = pattern.sub("", remainder, count=1)
    if [tag for tag, _ in sorted(positions, key=lambda item: item[1])] != [
        "history_evidence",
        "next_interest",
    ]:
        raise TraceValidationError(
            "blocks must appear in history_evidence, next_interest order"
        )
    if remainder.strip():
        raise TraceValidationError("text exists outside the two required blocks")
    return sections


def parse_and_validate_generation(raw: str) -> dict[str, str]:
    sections = _extract_sections(raw)
    for tag, content in sections.items():
        if not content:
            raise TraceValidationError(f"<{tag}> is empty")
    next_interest_modes = {
        mode.casefold()
        for mode in re.findall(
            r"\[(exploit|explore)\]",
            sections["next_interest"],
            re.IGNORECASE,
        )
    }
    if next_interest_modes != {"exploit", "explore"}:
        raise TraceValidationError(
            "<next_interest> must contain both [exploit] and [explore]"
        )
    return sections


def render_trace(trace: dict[str, str]) -> str:
    return (
        f"<history_evidence>\n{trace['history_evidence']}\n</history_evidence>\n"
        f"<next_interest>\n{trace['next_interest']}\n</next_interest>"
    )


def validation_issue(raw: str) -> str:
    try:
        parse_and_validate_generation(raw)
    except TraceValidationError as error:
        return str(error)
    return "No format error. Check that every claim is supported."


def generate_trace(
    client: Any,
    model: str,
    history_block: str,
    target_block: str,
    review: bool,
) -> dict[str, str]:
    candidate = v2.chat(
        client,
        model,
        GENERATOR_SYSTEM_PROMPT,
        generator_prompt(history_block, target_block),
    )
    current = candidate
    if review:
        current = v2.chat(
            client,
            model,
            REVIEWER_SYSTEM_PROMPT,
            reviewer_prompt(
                history_block,
                target_block,
                candidate,
                validation_issue(candidate),
            ),
        )

    for repair_index in range(MAX_REPAIR_ATTEMPTS + 1):
        try:
            return parse_and_validate_generation(current)
        except TraceValidationError as error:
            if repair_index == MAX_REPAIR_ATTEMPTS:
                raise
            current = v2.chat(
                client,
                model,
                REVIEWER_SYSTEM_PROMPT,
                reviewer_prompt(
                    history_block,
                    target_block,
                    current,
                    str(error),
                ),
            )
    raise AssertionError("unreachable")


def build_output_row(
    row_key: str,
    source_index: int,
    row: dict[str, Any],
    trace: dict[str, str],
    model: str,
    review: bool,
    signature: str,
) -> dict[str, Any]:
    reasoning_path = render_trace(trace)
    history_evidence = trace["history_evidence"]
    next_interest = trace["next_interest"]
    history_evidence_records = v2.block_to_records(history_evidence)
    next_interest_records = v2.block_to_records(next_interest, include_mode=True)
    next_interest_modes = list(
        dict.fromkeys(
            mode.casefold()
            for mode in re.findall(
                r"\[(exploit|explore)\]",
                next_interest,
                re.IGNORECASE,
            )
        )
    )
    return {
        "row_key": row_key,
        "source_index": source_index,
        "user_id": row.get("user_id"),
        "history_item_title": row.get("history_item_title"),
        "item_title": row.get("item_title"),
        "history_item_sid": row.get("history_item_sid"),
        "item_sid": row.get("item_sid"),
        "reasoning_path": reasoning_path,
        "history_evidence_text": history_evidence,
        "next_interest_text": next_interest,
        "history_evidence_json": json.dumps(
            history_evidence_records,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "next_interest_json": json.dumps(
            next_interest_records,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "process_trace_json": json.dumps(
            {
                "history_evidence": history_evidence_records,
                "next_interest": next_interest_records,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "next_interest_modes_json": json.dumps(
            next_interest_modes,
            separators=(",", ":"),
        ),
        "process_schema_version": SCHEMA_VERSION,
        "generation_signature": signature,
        "generation_model": model,
        "generator_target_visible": True,
        "reviewer_target_visible": True,
        "target_guidance_policy": "history_evidence_target_blind_next_interest_guided",
        "reviewed": review,
    }


def regenerate(
    category: str,
    out_path: str,
    csv_paths: list[str],
    endpoints: list[str],
    per_endpoint: int,
    limit: int,
    random_sample: bool,
    seed: int,
    model: str,
    review: bool,
    dry_run: bool,
    get_client: Any = None,
) -> None:
    source = v2.load_dataset(HF_REPO, f"{category}_reasoning", split="train")
    source_indices = v2.select_source_indices(
        len(source),
        limit,
        random_sample,
        seed,
    )
    catalog = v2.build_catalog(category)
    signature = generation_signature(model, review)
    done = v2.load_done_keys(out_path, signature)

    tasks = []
    for source_index in source_indices:
        row = dict(source[source_index])
        row_key = v2.row_key_for(row, source_index)
        if row_key not in done:
            tasks.append((row_key, source_index, row))
    print(
        f"[phase2-process-v3] {category}: {len(tasks)} to generate "
        f"({len(done)} already done)"
    )

    if dry_run:
        if not tasks:
            print("[phase2-process-v3] no pending row available")
            return
        _, source_index, row = tasks[0]
        print(f"[phase2-process-v3] dry-run source_index={source_index}")
        _, _, history_block = v2.history_from_row(row, catalog)
        target_block = v2.target_guidance_from_row(row, catalog)
        print(generator_prompt(history_block, target_block))
        return

    def process(
        client: Any,
        row_key: str,
        source_index: int,
        row: dict[str, Any],
    ) -> dict[str, Any]:
        _, _, history_block = v2.history_from_row(row, catalog)
        target_block = v2.target_guidance_from_row(row, catalog)
        trace = generate_trace(
            client,
            model,
            history_block,
            target_block,
            review,
        )
        return build_output_row(
            row_key,
            source_index,
            row,
            trace,
            model,
            review,
            signature,
        )

    if get_client is None:
        raise RuntimeError("generation requires an Azure client factory")
    v2.run_pool(
        tasks,
        process,
        out_path,
        csv_paths,
        endpoints,
        per_endpoint,
        get_client,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate simplified Video Games Phase-2 rationales at scale."
    )
    parser.add_argument(
        "--category",
        default=CATEGORY,
        choices=[CATEGORY],
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--out-dir", default="./regen_phase2_process_V3")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--per-endpoint", type=int, default=DEFAULT_PER_ENDPOINT)
    parser.add_argument("--endpoints", nargs="*", default=None)
    parser.add_argument("--limit", type=int, default=-1)
    parser.add_argument("--random-sample", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--pretty-json",
        action="store_true",
        help="Write an indented JSON mirror for debugging (disabled for full runs).",
    )
    parser.add_argument(
        "--review",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.per_endpoint < 1:
        parser.error("--per-endpoint must be at least 1")

    os.makedirs(args.out_dir, exist_ok=True)
    output_jsonl = os.path.join(
        args.out_dir,
        f"{args.category}.phase2_process.jsonl",
    )
    output_csvs = [
        output_jsonl.replace(".jsonl", ".csv"),
        os.path.join(
            args.out_dir,
            f"{args.category}.integrated_narrative.csv",
        ),
    ]
    output_pretty_json = (
        output_jsonl.replace(".jsonl", ".pretty.json")
        if args.pretty_json
        else None
    )
    lock_path = os.path.join(
        args.out_dir,
        f".{args.category}.phase2_process.lock",
    )
    with v2.single_process_lock(lock_path):
        get_client = None
        endpoints = []
        if not args.dry_run:
            configured_endpoints, get_client = v2.load_endpoint_helpers()
            endpoints = args.endpoints or configured_endpoints
            unknown = [
                endpoint
                for endpoint in endpoints
                if endpoint not in configured_endpoints
            ]
            if unknown:
                parser.error(f"unknown endpoint(s): {unknown}")

            v2.reconcile_output_mirrors(
                output_jsonl,
                output_csvs,
                output_pretty_json,
            )
        regenerate(
            category=args.category,
            out_path=output_jsonl,
            csv_paths=output_csvs,
            endpoints=endpoints,
            per_endpoint=args.per_endpoint,
            limit=args.limit,
            random_sample=args.random_sample,
            seed=args.seed,
            model=args.model,
            review=args.review,
            dry_run=args.dry_run,
            get_client=get_client,
        )
        if not args.dry_run:
            for output_csv in output_csvs:
                v2.jsonl_to_csv(output_jsonl, output_csv)
            if output_pretty_json is not None:
                v2.jsonl_to_pretty_json(output_jsonl, output_pretty_json)


if __name__ == "__main__":
    main()