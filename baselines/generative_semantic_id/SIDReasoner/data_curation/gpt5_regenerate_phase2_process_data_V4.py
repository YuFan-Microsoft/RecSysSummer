"""
Generate two-step Phase-2 user-interest traces with GPT-5.4.

V4 keeps exactly two reasoning stages:

    <history_summary>
    - <history SID> => one concise, verifiable history summary
    </history_summary>
    <future_interests>
    - [exploit or explore] <history SID> => one possible future user interest
    </future_interests>

The first stage summarizes what is present in history. The second predicts one to
four possible future interests. Exploit denotes continuation of an observed interest;
explore denotes a plausible adjacent interest. Their balance is selected dynamically.

The current ReasoningActivationDataset adds the outer ``<think>...</think>`` and
the target SID, so no Phase-2 training-loop change is required.

The generator and reviewer see the held-out target, but the target may guide only
a future interest with a natural, explicit bridge from history. When no such bridge
exists, the target is ignored and the history-grounded trace is retained.

Production input comes from ``yufan/recsys-genrec-dataset-refresh-gpt5.4-candidateV1``:

    <Category>_reasoning / train
    <Category>_catalog / train

The V3 production contract is retained for source columns, ``reasoning_path``,
resume-safe JSONL, and CSV filenames. V4-specific auxiliary columns use the new
``history_summary`` and ``future_interests`` names.

Examples:

    # Show one real HF prompt without calling GPT
    python gpt5_regenerate_phase2_process_data_V4.py \
        --category Video_Games --limit 1 --dry-run

    # Generate a 20-row pilot
    python gpt5_regenerate_phase2_process_data_V4.py \
        --category Video_Games --limit 20

    # Full production run
    python gpt5_regenerate_phase2_process_data_V4.py \
        --category Video_Games --out-dir ./regen_phase2_process_V4

Outputs are resume-safe and updated after every completed inference:

    <out-dir>/<Category>.phase2_process.jsonl
    <out-dir>/<Category>.phase2_process.csv
    <out-dir>/<Category>.integrated_narrative.csv
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


HF_REPO = "yufan/recsys-genrec-dataset-refresh-gpt5.4-candidateV1"
CATEGORY = v2.CATEGORY
DEFAULT_MODEL = v2.DEFAULT_MODEL
DEFAULT_PER_ENDPOINT = v2.DEFAULT_PER_ENDPOINT
REASONING_EFFORT = v2.REASONING_EFFORT
MAX_COMPLETION_TOKENS = v2.MAX_COMPLETION_TOKENS
MAX_REPAIR_ATTEMPTS = v2.MAX_REPAIR_ATTEMPTS
SCHEMA_VERSION = "phase2_process_v21_candidate_v1_production_io"

ITEM_SID_RE = v2.ITEM_SID_RE
TraceValidationError = v2.TraceValidationError
SECTION_PATTERNS = {
    tag: re.compile(fr"<{tag}>\s*(.*?)\s*</{tag}>", re.DOTALL)
    for tag in ("history_summary", "future_interests")
}
HISTORY_SUMMARY_LINE_RE = re.compile(
    r"^-\s+(?P<evidence>.+?)\s*=>\s*(?P<text>\S.*)$"
)
FUTURE_INTEREST_LINE_RE = re.compile(
    r"^-\s+\[(?P<mode>exploit|explore)\]\s+"
    r"(?P<evidence>.+?)\s*=>\s*(?P<text>\S.*)$",
    re.IGNORECASE,
)


OUTPUT_FORMAT = """<history_summary>
- HISTORY_SID[, HISTORY_SID...] => concise history pattern grounded in cited metadata
</history_summary>
<future_interests>
- [MODE] HISTORY_SID[, HISTORY_SID...] => possible future user interest and its history bridge
</future_interests>"""


GENERATOR_SYSTEM_PROMPT = (
    "Produce exactly two stages: summarize the user history, then predict possible future "
    "user interests. Label each future interest exploit for a continuation or explore for "
    "a bold but defensible adjacent interest. Include at least one exploit and one explore, while "
    "choosing any additional lines dynamically from the evidence. The history summary is "
    "factual compression only: it must not "
    "infer user interest, preference, intent, likelihood, or future behavior. Only the future "
    "interests stage may move beyond observed facts. Exploration should make a meaningful, "
    "non-obvious transfer through one explicit semantic bridge rather than merely repeat a "
    "platform, brand, or product type. "
    "from cited HISTORY. Describe the user, not recommendation actions. The visible target "
    "may guide one future interest only through a natural history bridge, and must never "
    "affect the history summary. Every line must cite exact full history SID tokens. Output "
    "only the required two-block trace."
)


GENERATOR_PROMPT = """Given the chronological user history (oldest to newest) and held-out
target below, write a concise two-stage user-interest trace.

HISTORY:
{history_block}

HELD-OUT TARGET (visible to the teacher; never identify it in the output):
{target_block}

Use this structure:
{output_format}

Requirements:
1. <history_summary> contains 1-3 concise observations grounded only in cited HISTORY
    metadata. Summarize repeated patterns, important attributes, and recent transitions.
    State only what the cited items and metadata explicitly establish. Do not infer or mention
    user interest, preference, intent, likelihood, recommendation, or future behavior. Do not
    use predictive language such as may, might, likely, suggests, or appears. TARGET must not
    influence this block.
2. <future_interests> contains 2-4 genuinely different possible future user interests derived
    from HISTORY. Replace [MODE] with exactly [exploit] or [explore]. Include at least one of
    each mode. Beyond that minimum, choose the number of lines and label balance dynamically
    from the evidence.
3. Assign each mode by direct instantiation:
     - [exploit]: the predicted interest is already directly instantiated by at least one
         HISTORY item; the prediction continues or narrows it.
     - [explore]: the predicted interest is not directly instantiated in HISTORY and is reached
         through one explicit shared attribute. Be bold: use a distinctive mechanic, theme,
         fantasy, skill, social pattern, or use case to infer a genuinely new neighboring
         interest, including across genres or product types when the bridge is strong.
     Prefer a non-obvious but defensible transfer over generic "other items" on the same
     platform. Platform or brand alone is not a sufficient bridge. Do not chain multiple
     speculative transitions.
4. Scale predictions to evidence: usually 1-2 future interests for one history item, 1-3 for
    two or three items, and 2-4 for four to ten items when genuinely distinct. Even with a
    short history, make the required explore meaningful by expanding from the most distinctive
    observed attribute rather than from a generic platform or product category.
5. Every future-interest line must describe what the user may be interested in and state the
    shared theme, mechanic, use case, or attribute linking it to the cited HISTORY item(s).
    An explore line must name both the explicit bridge and the genuinely new interest reached
    through it. The prediction may move one bold semantic step beyond the cited evidence, but
    no farther. Do not tell a recommender what to recommend, prioritize, serve, offer, or test.
6. TARGET may guide at most one future interest only when the bridge attribute is independently
    explicit in HISTORY and the prediction remains plausible if TARGET is hidden. TARGET may
    help select a novel direction reached through that bridge, but platform or brand overlap
    alone is insufficient. If the bridge is weak, ignore TARGET. Never cite the target SID,
    reveal item titles or identifying names, or predict an exact next item.
7. Every line must begin with one or more exact full SIDs copied verbatim from HISTORY,
    followed by "=>" after any mode label. Separate multiple SIDs with commas. Never use
    positions, aliases, or abbreviated SIDs. HISTORY records interactions only; never claim
    purchase, ownership, possession, or investment. Keep each line to one main claim in one
    sentence. Output only <history_summary> and <future_interests>."""


REVIEWER_SYSTEM_PROMPT = (
    "Audit an exactly two-stage user-interest trace: history summary, then future interests. "
    "The summary must be factual and target-blind, with no user-interest, preference, intent, "
    "likelihood, or future inference. Only future_interests may move beyond observed facts, "
    "and each prediction may make one bold but defensible semantic transfer through an "
    "explicit history bridge. Exploration should be genuinely new rather than generic "
    "same-platform or same-brand continuation. Require at least one exploit and one explore, "
    "without enforcing a fixed ratio "
    "for any additional lines. Remove recommendation-action, purchase, and ownership language; "
    "use exact full history SIDs. Output only corrected history_summary and future_interests "
    "blocks."
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
1. Use 1-3 concise history-summary lines grounded only in cited HISTORY metadata. Summarize
    patterns, attributes, or recent transitions. Remove user interest, preference, intent,
    likelihood, recommendation, and future-behavior inference, including may, might, likely,
    suggests, or appears. TARGET must not influence this block.
2. Use 2-4 distinct future interests. Replace [MODE] with exactly [exploit] or [explore].
    Include at least one of each mode. Beyond that minimum, choose the number and balance
    dynamically from the evidence.
3. Reclassify every line using direct instantiation:
     - [exploit]: the predicted interest is already directly instantiated by at least one
         HISTORY item; the prediction continues or narrows it.
     - [explore]: the predicted interest is not directly instantiated in HISTORY and is reached
         through one explicit shared attribute. Make it bold but defensible by transferring a
         distinctive mechanic, theme, fantasy, skill, social pattern, or use case into a genuinely
         new neighboring interest, including across genres or product types when justified.
     Reject generic "other items" based only on platform or brand. Remove chained, random, or
     unsupported broadening.
4. Scale predictions to evidence: usually 1-2 future interests for one history item, 1-3 for
    two or three items, and 2-4 for four to ten items when genuinely distinct. For short
    histories, derive explore from the most distinctive observed attribute, not a generic
    platform or product category.
5. Make each future interest state its history bridge and describe what the user may be
    interested in. Every explore must name both its explicit bridge and its genuinely new
    destination. Allow one bold semantic step beyond the cited evidence. Remove instructions
    to recommend, prioritize, serve, offer, or test items. TARGET may guide at most one novel
    direction only when the bridge attribute is explicit in HISTORY and the direction remains
    plausible with TARGET hidden. Ignore it when the bridge is weak.
6. Every line must begin with exact full HISTORY SIDs, followed by "=>" after any mode label.
    Separate multiple SIDs with commas. Replace positions, aliases, or abbreviated SIDs.
7. Keep each line to one claim. Do not reveal item names or TARGET, cite the target SID,
    predict an exact item, claim purchase or ownership, or return another block. Always return
    nonempty <history_summary> and <future_interests> blocks."""


def generation_signature(model: str, review: bool) -> str:
    payload = {
        "schema": SCHEMA_VERSION,
        "hf_repo": HF_REPO,
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


def build_catalog(category: str) -> dict[str, dict[str, str]]:
    dataset = v2.load_dataset(HF_REPO, f"{category}_catalog", split="train")
    catalog = {}
    for row in dataset:
        sid = str(row["sid"])
        title = str(row.get("title") or "")
        catalog[sid] = {
            "title": title,
            "brand": str(row.get("brand") or ""),
            "description": v2.process_description(row.get("description"), title),
        }
    return catalog


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
        "history_summary",
        "future_interests",
    ]:
        raise TraceValidationError(
            "blocks must appear in history_summary, future_interests order"
        )
    if remainder.strip():
        raise TraceValidationError("text exists outside the two required blocks")
    return sections


def _validate_sid_expression(
    raw: str,
    path: str,
    history_sid_set: set[str] | None,
) -> None:
    sids = ITEM_SID_RE.findall(raw)
    if not sids:
        raise TraceValidationError(f"{path} has no full history SID")
    remainder = ITEM_SID_RE.sub("", raw)
    if remainder.replace(",", "").strip():
        raise TraceValidationError(
            f"{path} must contain only comma-separated full history SIDs"
        )
    if history_sid_set is not None:
        for sid in sids:
            if sid not in history_sid_set:
                raise TraceValidationError(f"{path} cites a non-history SID: {sid}")


def parse_and_validate_generation(
    raw: str,
    history_sids: list[str] | None = None,
) -> dict[str, str]:
    sections = _extract_sections(raw)
    for tag, content in sections.items():
        if not content:
            raise TraceValidationError(f"<{tag}> is empty")

    history_sid_set = set(history_sids) if history_sids is not None else None
    summary_lines = [
        line.strip()
        for line in sections["history_summary"].splitlines()
        if line.strip()
    ]
    if not 1 <= len(summary_lines) <= 3:
        raise TraceValidationError(
            "<history_summary> must contain 1-3 nonempty lines"
        )
    for index, line in enumerate(summary_lines):
        match = HISTORY_SUMMARY_LINE_RE.fullmatch(line)
        if match is None:
            raise TraceValidationError(
                f"history_summary[{index}] must use '- SID(S) => text'"
            )
        _validate_sid_expression(
            match.group("evidence"),
            f"history_summary[{index}]",
            history_sid_set,
        )

    interest_lines = [
        line.strip()
        for line in sections["future_interests"].splitlines()
        if line.strip()
    ]
    if not 2 <= len(interest_lines) <= 4:
        raise TraceValidationError(
            "<future_interests> must contain 2-4 nonempty lines"
        )
    modes = set()
    for index, line in enumerate(interest_lines):
        match = FUTURE_INTEREST_LINE_RE.fullmatch(line)
        if match is None:
            raise TraceValidationError(
                "future_interests["
                f"{index}] must use '- [exploit|explore] SID(S) => text'"
            )
        _validate_sid_expression(
            match.group("evidence"),
            f"future_interests[{index}]",
            history_sid_set,
        )
        modes.add(match.group("mode").casefold())
    if modes != {"exploit", "explore"}:
        raise TraceValidationError(
            "<future_interests> must contain at least one [exploit] and one [explore]"
        )
    return sections


def render_trace(trace: dict[str, str]) -> str:
    return (
        f"<history_summary>\n{trace['history_summary']}\n</history_summary>\n"
        "<future_interests>\n"
        f"{trace['future_interests']}\n"
        "</future_interests>"
    )


def validation_issue(raw: str, history_sids: list[str] | None = None) -> str:
    try:
        parse_and_validate_generation(raw, history_sids)
    except TraceValidationError as error:
        return str(error)
    return "No format error. Check history grounding and future-interest bridges."


def generate_trace(
    client: Any,
    model: str,
    history_sids: list[str],
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
                validation_issue(candidate, history_sids),
            ),
        )

    for repair_index in range(MAX_REPAIR_ATTEMPTS + 1):
        try:
            return parse_and_validate_generation(current, history_sids)
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
    history_summary = trace["history_summary"]
    future_interests = trace["future_interests"]
    history_summary_records = v2.block_to_records(history_summary)
    future_interest_records = v2.block_to_records(
        future_interests,
        include_mode=True,
    )
    future_interest_modes = list(
        dict.fromkeys(
            mode.casefold()
            for mode in re.findall(
                r"\[(exploit|explore)\]",
                future_interests,
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
        "history_summary_text": history_summary,
        "future_interests_text": future_interests,
        "history_summary_json": json.dumps(
            history_summary_records,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "future_interests_json": json.dumps(
            future_interest_records,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "process_trace_json": json.dumps(
            {
                "history_summary": history_summary_records,
                "future_interests": future_interest_records,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "future_interest_modes_json": json.dumps(
            future_interest_modes,
            separators=(",", ":"),
        ),
        "process_schema_version": SCHEMA_VERSION,
        "generation_signature": signature,
        "generation_model": model,
        "generator_target_visible": True,
        "reviewer_target_visible": True,
        "target_guidance_policy": (
            "history_summary_target_blind_future_interests_guided"
        ),
        "reviewed": review,
    }


def jsonl_to_check_json(jsonl_path: str, json_path: str) -> None:
    checks = []
    with open(jsonl_path, "r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            history_sids = [
                str(value)
                for value in v2._maybe_list(row.get("history_item_sid"))
            ]
            history_titles = [
                str(value)
                for value in v2._maybe_list(row.get("history_item_title"))
            ]
            checks.append(
                {
                    "source_index": row.get("source_index"),
                    "history": [
                        {
                            "sid": sid,
                            "title": (
                                history_titles[index]
                                if index < len(history_titles)
                                else ""
                            ),
                        }
                        for index, sid in enumerate(history_sids)
                    ],
                    "target": {
                        "sid": row.get("item_sid"),
                        "title": row.get("item_title"),
                    },
                    "reasoning_path": row.get("reasoning_path"),
                }
            )
    checks.sort(key=lambda row: row["source_index"])
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(checks, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


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
    catalog = build_catalog(category)
    signature = generation_signature(model, review)
    done = v2.load_done_keys(out_path, signature)

    tasks = []
    for source_index in source_indices:
        row = dict(source[source_index])
        row_key = v2.row_key_for(row, source_index)
        if row_key not in done:
            tasks.append((row_key, source_index, row))
    print(
        f"[phase2-process-v4] {category}: {len(tasks)} to generate "
        f"({len(done)} already done)"
    )

    if dry_run:
        if not tasks:
            print("[phase2-process-v4] no pending row available")
            return
        _, source_index, row = tasks[0]
        print(f"[phase2-process-v4] dry-run source_index={source_index}")
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
        history_sids, _, history_block = v2.history_from_row(row, catalog)
        target_block = v2.target_guidance_from_row(row, catalog)
        trace = generate_trace(
            client,
            model,
            history_sids,
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
        description="Generate evidence-linked Video Games user-interest traces at scale."
    )
    parser.add_argument(
        "--category",
        default=CATEGORY,
        choices=[CATEGORY],
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--out-dir", default="./regen_phase2_process_V4")
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
        "--check-json",
        default=None,
        help="Write a compact readable JSON array with only history, target, and reasoning.",
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
            if args.check_json is not None:
                jsonl_to_check_json(output_jsonl, args.check_json)


if __name__ == "__main__":
    main()
