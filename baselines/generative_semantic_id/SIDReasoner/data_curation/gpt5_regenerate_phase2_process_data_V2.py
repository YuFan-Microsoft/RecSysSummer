"""
Generate target-aware, history-grounded Phase-2 rationales with GPT-5.4.

The generated ``reasoning_path`` has three blocks:

    <behavior>
    - <history SID> => one observed fact
    </behavior>
    <interest>
    - <history SID> => one cautious interest
    </interest>
    <intent>
    - [exploit] <history SID> => one strong continuation
    - [explore] <history SID> => one plausible broadening
    - [explore] <history SID> => another distinct broadening
    </intent>

The current ReasoningActivationDataset adds the outer ``<think>...</think>`` and
the target SID, so no Phase-2 training-loop change is required.

The generator and reviewer see the held-out target, but the target may guide only the
directions that history can naturally support. The trace must also preserve other strong
history-supported exploit and explore directions rather than collapsing around the target.
When no natural target bridge exists, the target is ignored and the history-grounded trace
is still retained.

Examples:

    # Show one real HF prompt without calling GPT
    python gpt5_regenerate_phase2_process_data_V2.py \
        --category Video_Games --limit 1 --dry-run

    # Generate a 20-row pilot
    python gpt5_regenerate_phase2_process_data_V2.py \
        --category Video_Games --limit 20

    # Full production run. By default this uses every configured endpoint with
    # 8 client-bound worker threads per endpoint and resumes from the JSONL.
    python gpt5_regenerate_phase2_process_data_V2.py \
        --category Video_Games --out-dir ./regen_phase2_process_V2

Outputs are resume-safe and updated after every completed inference:

    <out-dir>/<Category>.phase2_process.jsonl
    <out-dir>/<Category>.phase2_process.csv
    <out-dir>/<Category>.integrated_narrative.csv

The filenames and core columns match the V1 production pipeline. The default output
directory remains separate so V2 generations cannot overwrite V1 results.
"""

from __future__ import annotations

import argparse
import ast
import csv
import fcntl
import hashlib
import json
import os
import queue
import random
import re
import threading
import time
from contextlib import contextmanager
from typing import Any

import pandas as pd
from datasets import load_dataset


HF_REPO = "yufan/recsys-genrec-dataset"
CATEGORY = "Video_Games"
DEFAULT_MODEL = "gpt-5.4"
DEFAULT_PER_ENDPOINT = 8

MAX_COMPLETION_TOKENS = 1100
REASONING_EFFORT = "low"
MAX_DESCRIPTION_CHARS = 900
MAX_API_ATTEMPTS = 4
MAX_REPAIR_ATTEMPTS = 2
LOG_EVERY_SEC = 10
SCHEMA_VERSION = "phase2_process_v12_concise_freetext"

ITEM_SID_RE = re.compile(r"<a_[^<>\s]+><b_[^<>\s]+><c_[^<>\s]+>")
SECTION_PATTERNS = {
    tag: re.compile(fr"<{tag}>\s*(.*?)\s*</{tag}>", re.DOTALL)
    for tag in ("behavior", "interest", "intent")
}

_write_lock = threading.Lock()


@contextmanager
def single_process_lock(path: str):
    """Allow only one process to generate a category into an output directory."""
    handle = open(path, "a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            handle.seek(0)
            owner = handle.read().strip() or "unknown owner"
            raise RuntimeError(
                f"another generation process holds {path}: {owner}"
            ) from error

        handle.seek(0)
        handle.truncate()
        json.dump(
            {
                "pid": os.getpid(),
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            handle,
        )
        handle.flush()
        os.fsync(handle.fileno())
        yield
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


OUTPUT_FORMAT = """<behavior>
- HISTORY_SID(S) => concrete history-grounded observation
</behavior>
<interest>
- HISTORY_SID(S) => cautious history-grounded interest
</interest>
<intent>
- [exploit] HISTORY_SID(S) => strongest supported continuation
- [explore] HISTORY_SID(S) => distinct plausible broadening
- [explore] HISTORY_SID(S) => another distinct broadening
</intent>"""


GENERATOR_SYSTEM_PROMPT = (
    "Generate a diverse, history-grounded recommendation intent set. The visible target "
    "may guide one natural direction but must not dominate the trace. Every output line "
    "must cite exact full SID tokens copied verbatim from HISTORY; positional references "
    "are forbidden. Output only the required trace."
)


GENERATOR_PROMPT = """Given the user history and held-out target below, write a concise
reasoning trace with a diverse set of plausible next-interest directions.

HISTORY:
{history_block}

HELD-OUT TARGET (visible to the teacher; never identify it in the output):
{target_block}

Use this structure:
{output_format}

Requirements:
1. <behavior> normally contains 1-2 concrete observations grounded in HISTORY; use a third
    only when it captures a separate important pattern. Preserve useful item
    semantics instead of reducing everything to generic platform or era labels. Describe
    only the observed items, their attributes, and explicit repetition/co-occurrence. Move
    every claim about user interest, preference, openness, motivation, engagement strength,
    or what the history suggests into <interest>. Never imply purchase or ownership.
2. <interest> normally contains 1-2 cautious inferences supported by cited HISTORY; use a
    third only for a separate evidence cluster. Keep confidence proportional to evidence.
3. <intent> normally contains three genuinely different directions and includes both
    [exploit] and [explore]. Add a fourth only for a clearly independent history-supported
    direction. Let the evidence determine the mode balance; do not add filler.
4. TARGET may inform a direction only when HISTORY supports it. It must not suppress other
   reasonable history-supported directions. If the connection is weak, ignore TARGET
   rather than forcing an explanation; always retain an honest trace.
5. Be concise: each line states one main claim in one sentence. Keep only the most
    discriminative attributes, merge overlapping evidence, and avoid feature inventories,
    repeated qualifications, or restating the same idea across blocks.
6. Every line in all three blocks must begin with one or more exact full SIDs copied
    verbatim from HISTORY, followed by "=>". Use the complete
    <a_...><b_...><c_...> token sequence each time. Never use positions or aliases such as
    "1", "1, 2", "HISTORY_4", or "item 3"; never abbreviate a SID. Do not cite the target
    SID, reveal item titles or identifying names, or predict an exact next item. Output only
    the three blocks."""


REVIEWER_SYSTEM_PROMPT = (
    "Audit a target-aware recommendation trace for history grounding, intent diversity, "
    "target bias, and exact history-SID citations. Replace every positional reference with "
    "the corresponding full SID copied verbatim from HISTORY. Always output a corrected "
    "history-grounded trace."
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
1. Ground every claim in cited HISTORY. Behavior contains only item facts and explicit
    repetition/co-occurrence; move all user-level inference, preference, openness, or
    engagement-strength language to Interest.
2. Prefer 1-2 behavior lines, 1-2 interest lines, and three genuinely distinct intent lines
    containing both [exploit] and [explore]. Retain an extra line only for an independent
    evidence cluster or direction.
3. Preserve reasonable history-supported alternatives. Let TARGET inform only a natural
   direction; if its bridge is weak, ignore it instead of distorting the trace.
4. Every line must start with one or more exact <a_...><b_...><c_...> SIDs copied verbatim
    from HISTORY, then "=>". Replace numeric positions, HISTORY_N aliases, item labels, or
    abbreviated SIDs with the corresponding full history SID. Never cite the target SID.
5. Compress each line to one main claim: merge overlap, retain only discriminative details,
    and remove repeated qualifications or feature lists.
6. Do not imply purchase/ownership, reveal identifying item names or TARGET, or predict an
    exact item. Always return a nonempty corrected three-block trace."""


class TraceValidationError(ValueError):
    """The generated trace does not follow the required process format."""


def load_endpoint_helpers() -> tuple[list[str], Any]:
    try:
        from gpt5_endpoint_test import ENDPOINTS, get_GPT5_client
    except ModuleNotFoundError as error:
        if error.name and error.name.startswith("azure"):
            raise RuntimeError(
                "Generation requires azure-identity and openai. "
                "Install them and run `az login`."
            ) from error
        raise
    return list(ENDPOINTS), get_GPT5_client


def _fmt(seconds: float) -> str:
    seconds = int(max(0, seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def _clip(value: Any, limit: int) -> str:
    text = "" if value is None else str(value).strip()
    return text if len(text) <= limit else text[:limit] + "..."


def _maybe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str):
        text = value.strip()
        if text.startswith(("[", "(")):
            try:
                parsed = ast.literal_eval(text)
            except (ValueError, SyntaxError):
                return [value]
            if isinstance(parsed, (list, tuple)):
                return list(parsed)
        return [value]
    if value is None:
        return []
    return [value]


def process_description(description: Any, title: str) -> str:
    if description is None or description == "":
        return title
    values = _maybe_list(description)
    non_empty = [str(value).strip() for value in values if str(value).strip()]
    return max(non_empty, key=len) if non_empty else title


def row_key_for(row: dict[str, Any], source_index: int) -> str:
    payload = {
        "source_index": source_index,
        "user_id": row.get("user_id"),
        "history_item_sid": _maybe_list(row.get("history_item_sid")),
        "item_sid": row.get("item_sid"),
    }
    digest = hashlib.sha1(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    return f"{row.get('user_id', 'unknown')}::{digest}"


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


def build_catalog(category: str) -> dict[str, dict[str, str]]:
    dataset = load_dataset(HF_REPO, f"{category}_catalog", split="train")
    catalog = {}
    for row in dataset:
        sid = str(row["sid"])
        title = str(row.get("title") or "")
        catalog[sid] = {
            "title": title,
            "brand": str(row.get("brand") or ""),
            "description": process_description(row.get("description"), title),
        }
    return catalog


def history_from_row(
    row: dict[str, Any],
    catalog: dict[str, dict[str, str]],
) -> tuple[list[str], list[str], str]:
    history_sids = [str(value) for value in _maybe_list(row.get("history_item_sid"))]
    row_titles = [str(value) for value in _maybe_list(row.get("history_item_title"))]
    if not history_sids:
        raise TraceValidationError("history_item_sid is empty")

    history_titles = []
    lines = []
    for index, sid in enumerate(history_sids, start=1):
        if ITEM_SID_RE.fullmatch(sid) is None:
            raise TraceValidationError(f"malformed history SID: {sid}")
        meta = catalog.get(sid, {})
        fallback_title = row_titles[index - 1] if index - 1 < len(row_titles) else ""
        title = str(meta.get("title") or fallback_title or "(missing title)")
        history_titles.append(title)
        parts = [f"{index}. {sid}", f"Title: {title}"]
        brand = str(meta.get("brand") or "")
        if brand:
            parts.append(f"Brand: {brand}")
        parts.append(
            "Description: "
            + _clip(meta.get("description") or title, MAX_DESCRIPTION_CHARS)
        )
        lines.append("\n".join(parts))
    return history_sids, history_titles, "\n".join(lines)


def target_guidance_from_row(
    row: dict[str, Any],
    catalog: dict[str, dict[str, str]],
) -> str:
    """Render private target semantics without exposing its SID to GPT."""
    target_sid = str(row.get("item_sid") or "")
    meta = catalog.get(target_sid, {})
    title = str(row.get("item_title") or meta.get("title") or "(missing title)")
    parts = [f"Title: {title}"]
    brand = str(meta.get("brand") or "")
    if brand:
        parts.append(f"Brand: {brand}")
    parts.append(
        "Description: "
        + _clip(meta.get("description") or title, MAX_DESCRIPTION_CHARS)
    )
    return "\n".join(parts)


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
            raise TraceValidationError(
                f"expected one <{tag}>...</{tag}> block"
            )
        match = matches[0]
        sections[tag] = match.group(1).strip()
        positions.append((tag, match.start()))
        remainder = pattern.sub("", remainder, count=1)
    if [tag for tag, _ in sorted(positions, key=lambda item: item[1])] != [
        "behavior",
        "interest",
        "intent",
    ]:
        raise TraceValidationError(
            "blocks must appear in behavior, interest, intent order"
        )
    if remainder.strip():
        raise TraceValidationError("text exists outside the three required blocks")
    return sections


def parse_trace(raw: str) -> dict[str, str]:
    sections = _extract_sections(raw)
    for tag, content in sections.items():
        if not content:
            raise TraceValidationError(f"<{tag}> is empty")
    return sections


def parse_and_validate_trace(raw: str) -> dict[str, str]:
    return parse_trace(raw)


def parse_and_validate_generation(raw: str) -> dict[str, str]:
    return parse_and_validate_trace(raw)


def render_trace(trace: dict[str, str]) -> str:
    return (
        f"<behavior>\n{trace['behavior']}\n</behavior>\n"
        f"<interest>\n{trace['interest']}\n</interest>\n"
        f"<intent>\n{trace['intent']}\n</intent>"
    )


def chat(
    client: Any,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    last_error: Exception | None = None
    for attempt in range(1, MAX_API_ATTEMPTS + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                reasoning_effort=REASONING_EFFORT,
            )
            content = (response.choices[0].message.content or "").strip()
            if not content:
                raise RuntimeError("GPT returned an empty response")
            return content
        except Exception as error:
            last_error = error
            if attempt == MAX_API_ATTEMPTS:
                break
            time.sleep(min(2 ** (attempt - 1), 8))
    detail = (
        f"{type(last_error).__name__}: {str(last_error)[:500]}"
        if last_error is not None
        else "unknown error"
    )
    raise RuntimeError(
        f"GPT request failed after {MAX_API_ATTEMPTS} attempts; last error: {detail}"
    ) from last_error


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
    candidate = chat(
        client,
        model,
        GENERATOR_SYSTEM_PROMPT,
        generator_prompt(history_block, target_block),
    )
    current = candidate
    if review:
        current = chat(
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
            current = chat(
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


def load_done_keys(path: str, expected_signature: str) -> set[str]:
    done = set()
    if not os.path.exists(path):
        return done
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            signature = row.get("generation_signature")
            if signature != expected_signature:
                raise RuntimeError(
                    f"{path} was created with a different prompt/model. "
                    "Use a new output directory."
                )
            row_key = row.get("row_key")
            if isinstance(row_key, str):
                done.add(row_key)
    return done


def append_jsonl(path: str, value: dict[str, Any]) -> None:
    line = json.dumps(value, ensure_ascii=False) + "\n"
    with _write_lock:
        with open(path, "a", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                handle.write(line)
                handle.flush()
                os.fsync(handle.fileno())
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def append_csv_row(path: str, value: dict[str, Any]) -> None:
    """Append one result to a live CSV mirror and force it to disk."""
    with _write_lock:
        write_header = not os.path.exists(path) or os.path.getsize(path) == 0
        with open(path, "a", encoding="utf-8", newline="") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                writer = csv.DictWriter(handle, fieldnames=list(value))
                if write_header:
                    writer.writeheader()
                writer.writerow(value)
                handle.flush()
                os.fsync(handle.fileno())
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def block_to_records(
    block: str,
    include_mode: bool = False,
) -> list[dict[str, Any]]:
    """Best-effort V1-compatible records without rejecting free-text blocks."""
    records = []
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        content = line[1:].strip() if line.startswith("-") else line
        evidence, separator, text = content.partition("=>")
        if not separator:
            evidence, text = "", content
        record = {
            "evidence_sids": list(dict.fromkeys(ITEM_SID_RE.findall(evidence))),
            "text": " ".join(text.split()),
        }
        if include_mode:
            mode_match = re.search(r"\[(exploit|explore)\]", evidence, re.IGNORECASE)
            record["mode"] = (
                mode_match.group(1).casefold() if mode_match else "unknown"
            )
        records.append(record)
    return records


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
    behavior = trace["behavior"]
    interest = trace["interest"]
    intent = trace["intent"]
    behavior_records = block_to_records(behavior)
    interest_records = block_to_records(interest)
    intent_records = block_to_records(intent, include_mode=True)
    intent_modes = list(dict.fromkeys(
        mode.casefold()
        for mode in re.findall(r"\[(exploit|explore)\]", intent, re.IGNORECASE)
    ))
    return {
        "row_key": row_key,
        "source_index": source_index,
        "user_id": row.get("user_id"),
        "history_item_title": row.get("history_item_title"),
        "item_title": row.get("item_title"),
        "history_item_sid": row.get("history_item_sid"),
        "item_sid": row.get("item_sid"),
        "reasoning_path": reasoning_path,
        "behavior_text": behavior,
        "interest_text": interest,
        "intent_text": intent,
        "behavior_json": json.dumps(
            behavior_records, ensure_ascii=False, separators=(",", ":")
        ),
        "interest_json": json.dumps(
            interest_records, ensure_ascii=False, separators=(",", ":")
        ),
        "intent_json": json.dumps(
            intent_records, ensure_ascii=False, separators=(",", ":")
        ),
        "process_trace_json": json.dumps(
            {
                "behavior": behavior_records,
                "interest": interest_records,
                "intent": intent_records,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "intent_modes_json": json.dumps(intent_modes, separators=(",", ":")),
        "process_schema_version": SCHEMA_VERSION,
        "generation_signature": signature,
        "generation_model": model,
        "generator_target_visible": True,
        "reviewer_target_visible": True,
        "target_guidance_policy": "free_text_blocks_llm_judged",
        "reviewed": review,
    }


def run_pool(
    tasks: list[tuple[str, int, dict[str, Any]]],
    process_fn: Any,
    out_path: str,
    csv_paths: list[str],
    endpoints: list[str],
    per_endpoint: int,
    get_client: Any,
) -> None:
    total = len(tasks)
    if total == 0:
        print("[phase2-process] nothing to do")
        return

    task_queue: queue.Queue[tuple[str, int, dict[str, Any]]] = queue.Queue()
    for task in tasks:
        task_queue.put(task)

    failure_path = out_path.replace(".jsonl", ".failures.jsonl")
    counter = {"done": 0, "failed": 0}
    counter_lock = threading.Lock()
    log_lock = threading.Lock()
    started_at = time.time()
    last_log = {"time": 0.0}

    def emit(force: bool = False) -> None:
        now = time.time()
        with log_lock:
            if not force and now - last_log["time"] < LOG_EVERY_SEC:
                return
            last_log["time"] = now
        with counter_lock:
            done = counter["done"]
            failed = counter["failed"]
        elapsed = now - started_at
        rate = done / elapsed if elapsed > 0 else 0.0
        eta = (total - done) / rate if rate > 0 else 0.0
        print(
            f"  [phase2-process] {done}/{total} "
            f"({done / total * 100:.1f}%) | {rate:.2f} rows/s | "
            f"elapsed {_fmt(elapsed)} | ETA {_fmt(eta)} | {failed} failed",
            flush=True,
        )

    def worker(endpoint: str) -> None:
        client = get_client(endpoint)
        while True:
            try:
                task = task_queue.get_nowait()
            except queue.Empty:
                return
            row_key, source_index, row = task
            try:
                result = process_fn(client, row_key, source_index, row)
                append_jsonl(out_path, result)
                for csv_path in csv_paths:
                    append_csv_row(csv_path, result)
                with counter_lock:
                    counter["done"] += 1
                    done = counter["done"]
                emit(force=(done == total))
            except Exception as error:
                append_jsonl(
                    failure_path,
                    {
                        "row_key": row_key,
                        "source_index": source_index,
                        "endpoint": endpoint,
                        "error_type": type(error).__name__,
                        "error": str(error)[:1000],
                    },
                )
                with counter_lock:
                    counter["failed"] += 1
                print(
                    f"  [phase2-process] FAIL row={row_key}: "
                    f"{type(error).__name__}: {str(error)[:180]}",
                    flush=True,
                )
            finally:
                task_queue.task_done()

    threads = []
    for endpoint in endpoints:
        for _ in range(per_endpoint):
            thread = threading.Thread(
                target=worker,
                args=(endpoint,),
                daemon=True,
            )
            thread.start()
            threads.append(thread)
    print(
        f"  [phase2-process] {total} tasks / {len(endpoints)} endpoints x "
        f"{per_endpoint} = {len(threads)} workers"
    )
    for thread in threads:
        thread.join()
    emit(force=True)


def jsonl_to_csv(jsonl_path: str, csv_path: str) -> None:
    if not os.path.exists(jsonl_path):
        return
    records = []
    with open(jsonl_path, "r", encoding="utf-8") as handle:
        for line in handle:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if not records:
        return
    frame = pd.DataFrame(records)
    frame = frame.drop_duplicates("row_key", keep="last")
    frame = frame.sort_values("source_index")
    frame.to_csv(csv_path, index=False)
    print(f"  wrote {csv_path} ({len(frame)} rows)")


def jsonl_to_pretty_json(jsonl_path: str, json_path: str) -> None:
    """Write an indented JSON-array mirror for human inspection."""
    if not os.path.exists(jsonl_path):
        return
    records_by_key = {}
    with open(jsonl_path, "r", encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            records_by_key[record["row_key"]] = record
    records = sorted(
        records_by_key.values(),
        key=lambda record: record["source_index"],
    )
    if not records:
        return
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"  wrote {json_path} ({len(records)} rows)")


def reconcile_output_mirrors(
    jsonl_path: str,
    csv_paths: list[str],
    pretty_json_path: str | None,
) -> None:
    """Make human-readable mirrors agree with canonical JSONL before resuming."""
    if os.path.exists(jsonl_path):
        for csv_path in csv_paths:
            jsonl_to_csv(jsonl_path, csv_path)
        if pretty_json_path is not None:
            jsonl_to_pretty_json(jsonl_path, pretty_json_path)
        return
    mirror_paths = list(csv_paths)
    if pretty_json_path is not None:
        mirror_paths.append(pretty_json_path)
    for mirror_path in mirror_paths:
        if os.path.exists(mirror_path):
            os.remove(mirror_path)


def select_source_indices(
    total: int,
    limit: int,
    random_sample: bool,
    seed: int,
) -> list[int] | range:
    if limit <= 0 or limit >= total:
        return range(total)
    if random_sample:
        return random.Random(seed).sample(range(total), limit)
    return range(limit)


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
    source = load_dataset(HF_REPO, f"{category}_reasoning", split="train")
    source_indices = select_source_indices(
        len(source),
        limit,
        random_sample,
        seed,
    )
    catalog = build_catalog(category)
    signature = generation_signature(model, review)
    done = load_done_keys(out_path, signature)

    tasks = []
    for source_index in source_indices:
        row = dict(source[source_index])
        row_key = row_key_for(row, source_index)
        if row_key not in done:
            tasks.append((row_key, source_index, row))
    print(
        f"[phase2-process] {category}: {len(tasks)} to generate "
        f"({len(done)} already done)"
    )

    if dry_run:
        if not tasks:
            print("[phase2-process] no pending row available")
            return
        _, source_index, row = tasks[0]
        print(f"[phase2-process] dry-run source_index={source_index}")
        _, _, history_block = history_from_row(row, catalog)
        target_block = target_guidance_from_row(row, catalog)
        print(generator_prompt(history_block, target_block))
        return

    def process(
        client: Any,
        row_key: str,
        source_index: int,
        row: dict[str, Any],
    ) -> dict[str, Any]:
        _, _, history_block = history_from_row(
            row, catalog
        )
        target_block = target_guidance_from_row(row, catalog)
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
    run_pool(
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
        description="Generate Video Games Phase-2 rationales at production scale."
    )
    parser.add_argument(
        "--category",
        default=CATEGORY,
        choices=[CATEGORY],
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--out-dir", default="./regen_phase2_process_V2")
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
    output_pretty_json = output_jsonl.replace(
        ".jsonl",
        ".pretty.json",
    ) if args.pretty_json else None
    lock_path = os.path.join(
        args.out_dir,
        f".{args.category}.phase2_process.lock",
    )
    with single_process_lock(lock_path):
        get_client = None
        endpoints = []
        if not args.dry_run:
            configured_endpoints, get_client = load_endpoint_helpers()
            endpoints = args.endpoints or configured_endpoints
            unknown = [
                endpoint
                for endpoint in endpoints
                if endpoint not in configured_endpoints
            ]
            if unknown:
                parser.error(f"unknown endpoint(s): {unknown}")

            reconcile_output_mirrors(
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
                jsonl_to_csv(output_jsonl, output_csv)
            if output_pretty_json is not None:
                jsonl_to_pretty_json(output_jsonl, output_pretty_json)


if __name__ == "__main__":
    main()
