"""
Generate simple, target-blind Phase-2 reasoning traces with GPT-5.4.

The generated ``reasoning_path`` has three blocks:

    <behavior>
    - <history SID> => one observed fact
    </behavior>
    <interest>
    - <history SID> => one cautious interest
    </interest>
    <intent>
    - [continue] <history SID> => one likely continuation
    - [adjacent] <history SID> => one related direction
    - [explore] <history SID> => one exploratory direction
    </intent>

The current ReasoningActivationDataset adds the outer ``<think>...</think>`` and
the target SID, so no Phase-2 training-loop change is required.

The held-out target is never passed to the generator or reviewer as a target field.
If the same item already appears in history, it remains visible only as history.

Examples:

    # Show one real HF prompt without calling GPT
    python gpt5_regenerate_phase2_process_data.py \
        --category Video_Games --limit 1 --dry-run

    # Generate a 20-row pilot
    python gpt5_regenerate_phase2_process_data.py \
        --category Video_Games --limit 20

Outputs are resume-safe:

    <out-dir>/<Category>.phase2_process.jsonl
    <out-dir>/<Category>.phase2_process.csv
    <out-dir>/<Category>.integrated_narrative.csv
"""

from __future__ import annotations

import argparse
import ast
import fcntl
import hashlib
import json
import os
import queue
import re
import threading
import time
from typing import Any

import pandas as pd
from datasets import load_dataset


HF_REPO = "yufan/recsys-genrec-dataset"
CATEGORIES = ["Video_Games", "Office_Products", "Industrial_and_Scientific"]
DEFAULT_MODEL = "gpt-5.4"
DEFAULT_PER_ENDPOINT = 8

MAX_COMPLETION_TOKENS = 1100
REASONING_EFFORT = "low"
MAX_DESCRIPTION_CHARS = 900
MAX_REASONING_CHARS = 4000
MAX_API_ATTEMPTS = 4
MAX_REPAIR_ATTEMPTS = 2
LOG_EVERY_SEC = 10
SCHEMA_VERSION = "phase2_process_v2"

ITEM_SID_RE = re.compile(r"<a_[^<>\s]+><b_[^<>\s]+><c_[^<>\s]+>")
SECTION_PATTERNS = {
    tag: re.compile(fr"<{tag}>\s*(.*?)\s*</{tag}>", re.DOTALL)
    for tag in ("behavior", "interest", "intent")
}
STAGE_LINE_RE = re.compile(r"^-\s*(.*?)\s*=>\s*(.+?)\s*$")
INTENT_LINE_RE = re.compile(
    r"^-\s*\[(continue|adjacent|explore)\]\s*(.*?)\s*=>\s*(.+?)\s*$",
    re.IGNORECASE,
)
INTENT_MODES = ("continue", "adjacent", "explore")

_write_lock = threading.Lock()


OUTPUT_FORMAT = """<behavior>
- HISTORY_SID(S) => one observed fact
</behavior>
<interest>
- HISTORY_SID(S) => one cautious interest
</interest>
<intent>
- [continue] HISTORY_SID(S) => one likely continuation
- [adjacent] HISTORY_SID(S) => one related but different direction
- [explore] HISTORY_SID(S) => one broader exploratory direction
</intent>"""


GENERATOR_SYSTEM_PROMPT = (
    "You create target-blind reasoning data for a recommendation model. "
    "Use only the supplied history. Output only the requested format."
)


GENERATOR_PROMPT = """Given the user history below, write a short reasoning trace.

HISTORY:
{history_block}

Use exactly this format:
{output_format}

Requirements:
1. Use only history evidence. Do not predict one exact next item.
2. Cite only full SIDs from the history. Do not write item titles in the output.
3. <behavior> contains facts, not preferences.
4. <interest> contains cautious interests supported by the cited SIDs.
5. With one history item, do not claim a strong or long-term preference.
6. The three <intent> lines must be different. Keep the explore line broad.
7. Output only the three blocks."""


REVIEWER_SYSTEM_PROMPT = (
    "You fix target-blind recommendation reasoning data. "
    "Use only the supplied history. Output only the requested format."
)


REVIEWER_PROMPT = """Fix the candidate trace.

HISTORY:
{history_block}

CANDIDATE:
{candidate}

VALIDATION ISSUE:
{validation_issue}

Use exactly this format:
{output_format}

Keep only supported facts and interests. Use only history SIDs, no item titles,
no exact next item, and three different intents: continue, adjacent, explore.
Output only the three blocks."""


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


def _normalize_title(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def build_catalog_title_index(
    catalog: dict[str, dict[str, str]],
) -> dict[int, set[str]]:
    """Index only specific titles; generic item-type phrases remain allowed."""
    index: dict[int, set[str]] = {}
    for meta in catalog.values():
        title = _normalize_title(str(meta.get("title") or ""))
        if not title:
            continue
        token_count = len(title.split())
        if len(title) < 12 and not (token_count == 1 and len(title) >= 8):
            continue
        index.setdefault(token_count, set()).add(title)
    return index


def find_catalog_title(
    text: str,
    title_index: dict[int, set[str]],
) -> str | None:
    tokens = _normalize_title(text).split()
    for size, titles in title_index.items():
        if size > len(tokens):
            continue
        for start in range(len(tokens) - size + 1):
            candidate = " ".join(tokens[start : start + size])
            if candidate in titles:
                return candidate
    return None


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


def generator_prompt(history_block: str) -> str:
    return GENERATOR_PROMPT.format(
        history_block=history_block,
        output_format=OUTPUT_FORMAT,
    )


def reviewer_prompt(
    history_block: str,
    candidate: str,
    validation_issue: str,
) -> str:
    return REVIEWER_PROMPT.format(
        history_block=history_block,
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


def _parse_evidence(raw: str, path: str) -> list[str]:
    sids = ITEM_SID_RE.findall(raw)
    if not sids:
        raise TraceValidationError(f"{path} has no full item SID")
    remainder = raw
    for sid in sids:
        remainder = remainder.replace(sid, "", 1)
    if remainder.replace(",", "").strip():
        raise TraceValidationError(
            f"{path} evidence must contain only comma-separated full item SIDs"
        )
    return list(dict.fromkeys(sids))


def _parse_stage_lines(raw: str, stage: str) -> list[dict[str, Any]]:
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        raise TraceValidationError(f"<{stage}> is empty")
    entries = []
    for index, line in enumerate(lines):
        match = STAGE_LINE_RE.fullmatch(line)
        if match is None:
            raise TraceValidationError(
                f"{stage}[{index}] must use '- SID(S) => text'"
            )
        entries.append(
            {
                "evidence_sids": _parse_evidence(
                    match.group(1),
                    f"{stage}[{index}]",
                ),
                "text": " ".join(match.group(2).split()),
            }
        )
    return entries


def _parse_intent_lines(raw: str) -> list[dict[str, Any]]:
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(lines) != 3:
        raise TraceValidationError("<intent> must contain exactly three lines")
    entries = []
    for index, line in enumerate(lines):
        match = INTENT_LINE_RE.fullmatch(line)
        if match is None:
            raise TraceValidationError(
                "intent lines must use '- [continue|adjacent|explore] SID(S) => text'"
            )
        entries.append(
            {
                "mode": match.group(1).casefold(),
                "evidence_sids": _parse_evidence(
                    match.group(2),
                    f"intent[{index}]",
                ),
                "text": " ".join(match.group(3).split()),
            }
        )
    return entries


def parse_trace(raw: str) -> dict[str, list[dict[str, Any]]]:
    sections = _extract_sections(raw)
    return {
        "behavior": _parse_stage_lines(sections["behavior"], "behavior"),
        "interest": _parse_stage_lines(sections["interest"], "interest"),
        "intent": _parse_intent_lines(sections["intent"]),
    }


def _clean_text(
    text: str,
    path: str,
    history_titles: list[str],
    title_index: dict[int, set[str]],
) -> str:
    if not 3 <= len(text) <= 220:
        raise TraceValidationError(f"{path} must contain 3-220 characters")
    if "<" in text or ">" in text:
        raise TraceValidationError(f"{path} must not contain an SID or tag")
    lowered = text.casefold()
    for title in history_titles:
        title = " ".join(str(title).split())
        if len(title) >= 5 and title.casefold() in lowered:
            raise TraceValidationError(f"{path} copies item title {title!r}")
    catalog_title = find_catalog_title(text, title_index)
    if catalog_title:
        raise TraceValidationError(
            f"{path} names a catalog item: {catalog_title!r}"
        )
    return text


def _validate_evidence(
    evidence_sids: list[str],
    path: str,
    history_sid_set: set[str],
) -> list[str]:
    for sid in evidence_sids:
        if sid not in history_sid_set:
            raise TraceValidationError(
                f"{path} cites a non-history SID: {sid}"
            )
    return evidence_sids


def _meaningful_tokens(text: str) -> set[str]:
    stopwords = {
        "a", "an", "and", "another", "for", "in", "of", "or", "related",
        "that", "the", "to", "with",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.casefold())
        if len(token) > 2 and token not in stopwords
    }


def validate_trace(
    trace: dict[str, list[dict[str, Any]]],
    history_sids: list[str],
    history_titles: list[str],
    title_index: dict[int, set[str]],
) -> dict[str, list[dict[str, Any]]]:
    history_sid_set = set(history_sids)
    if not 1 <= len(trace["behavior"]) <= 5:
        raise TraceValidationError("<behavior> must contain 1-5 lines")
    if not 1 <= len(trace["interest"]) <= 4:
        raise TraceValidationError("<interest> must contain 1-4 lines")

    cleaned = {"behavior": [], "interest": [], "intent": []}
    for stage in ("behavior", "interest"):
        for index, entry in enumerate(trace[stage]):
            text = _clean_text(
                entry["text"],
                f"{stage}[{index}]",
                history_titles,
                title_index,
            )
            if stage == "interest" and len(history_sids) == 1:
                banned = (
                    "strong preference",
                    "clear preference",
                    "consistent preference",
                    "long-term preference",
                    "long term preference",
                )
                if any(phrase in text.casefold() for phrase in banned):
                    raise TraceValidationError(
                        "one-item history overstates the user's preference"
                    )
            cleaned[stage].append(
                {
                    "evidence_sids": _validate_evidence(
                        entry["evidence_sids"],
                        f"{stage}[{index}]",
                        history_sid_set,
                    ),
                    "text": text,
                }
            )

    modes = [entry["mode"] for entry in trace["intent"]]
    if set(modes) != set(INTENT_MODES) or len(set(modes)) != 3:
        raise TraceValidationError(
            "<intent> must contain continue, adjacent, and explore once each"
        )
    token_sets = []
    for index, entry in enumerate(trace["intent"]):
        text = _clean_text(
            entry["text"],
            f"intent[{index}]",
            history_titles,
            title_index,
        )
        tokens = _meaningful_tokens(text)
        for previous in token_sets:
            union = tokens | previous
            similarity = len(tokens & previous) / len(union) if union else 1.0
            if similarity > 0.75:
                raise TraceValidationError("two intent lines are too similar")
        token_sets.append(tokens)
        cleaned["intent"].append(
            {
                "mode": entry["mode"],
                "evidence_sids": _validate_evidence(
                    entry["evidence_sids"],
                    f"intent[{index}]",
                    history_sid_set,
                ),
                "text": text,
            }
        )
    cleaned["intent"].sort(
        key=lambda entry: INTENT_MODES.index(entry["mode"])
    )

    rendered = render_trace(cleaned)
    if len(rendered) > MAX_REASONING_CHARS:
        raise TraceValidationError(
            f"reasoning_path exceeds {MAX_REASONING_CHARS} characters"
        )
    return cleaned


def parse_and_validate_trace(
    raw: str,
    history_sids: list[str],
    history_titles: list[str],
    title_index: dict[int, set[str]],
) -> dict[str, list[dict[str, Any]]]:
    return validate_trace(
        parse_trace(raw),
        history_sids,
        history_titles,
        title_index,
    )


def render_trace(trace: dict[str, list[dict[str, Any]]]) -> str:
    behavior = "\n".join(
        f"- {', '.join(entry['evidence_sids'])} => {entry['text']}"
        for entry in trace["behavior"]
    )
    interest = "\n".join(
        f"- {', '.join(entry['evidence_sids'])} => {entry['text']}"
        for entry in trace["interest"]
    )
    intent = "\n".join(
        f"- [{entry['mode']}] {', '.join(entry['evidence_sids'])} => "
        f"{entry['text']}"
        for entry in trace["intent"]
    )
    return (
        f"<behavior>\n{behavior}\n</behavior>\n"
        f"<interest>\n{interest}\n</interest>\n"
        f"<intent>\n{intent}\n</intent>"
    )


def validate_no_target_leakage(
    reasoning_path: str,
    row: dict[str, Any],
    history_sids: list[str],
    history_titles: list[str],
) -> None:
    target_sid = str(row.get("item_sid") or "")
    if (
        target_sid
        and target_sid not in set(history_sids)
        and target_sid in reasoning_path
    ):
        raise TraceValidationError("reasoning contains the held-out target SID")

    target_title = " ".join(str(row.get("item_title") or "").split())
    history_title_set = {
        " ".join(str(title).split()).casefold()
        for title in history_titles
    }
    if (
        len(target_title) >= 5
        and target_title.casefold() not in history_title_set
        and target_title.casefold() in reasoning_path.casefold()
    ):
        raise TraceValidationError("reasoning contains the held-out target title")


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
    raise RuntimeError(
        f"GPT request failed after {MAX_API_ATTEMPTS} attempts"
    ) from last_error


def validation_issue(
    raw: str,
    history_sids: list[str],
    history_titles: list[str],
    title_index: dict[int, set[str]],
) -> str:
    try:
        parse_and_validate_trace(
            raw,
            history_sids,
            history_titles,
            title_index,
        )
    except TraceValidationError as error:
        return str(error)
    return "No format error. Check that every claim is supported."


def generate_trace(
    client: Any,
    model: str,
    history_block: str,
    history_sids: list[str],
    history_titles: list[str],
    title_index: dict[int, set[str]],
    review: bool,
) -> dict[str, list[dict[str, Any]]]:
    candidate = chat(
        client,
        model,
        GENERATOR_SYSTEM_PROMPT,
        generator_prompt(history_block),
    )
    current = candidate
    if review:
        current = chat(
            client,
            model,
            REVIEWER_SYSTEM_PROMPT,
            reviewer_prompt(
                history_block,
                candidate,
                validation_issue(
                    candidate,
                    history_sids,
                    history_titles,
                    title_index,
                ),
            ),
        )

    for repair_index in range(MAX_REPAIR_ATTEMPTS + 1):
        try:
            return parse_and_validate_trace(
                current,
                history_sids,
                history_titles,
                title_index,
            )
        except TraceValidationError as error:
            if repair_index == MAX_REPAIR_ATTEMPTS:
                raise
            current = chat(
                client,
                model,
                REVIEWER_SYSTEM_PROMPT,
                reviewer_prompt(history_block, current, str(error)),
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


def acquire_run_lock(out_path: str) -> Any:
    lock_path = out_path + ".run.lock"
    handle = open(lock_path, "a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        handle.close()
        raise RuntimeError(
            f"another generation process is already using {out_path}"
        ) from error
    return handle


def release_run_lock(handle: Any) -> None:
    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    handle.close()


def build_output_row(
    row_key: str,
    source_index: int,
    row: dict[str, Any],
    trace: dict[str, list[dict[str, Any]]],
    model: str,
    review: bool,
    signature: str,
) -> dict[str, Any]:
    reasoning_path = render_trace(trace)
    return {
        "row_key": row_key,
        "source_index": source_index,
        "user_id": row.get("user_id"),
        "history_item_title": row.get("history_item_title"),
        "item_title": row.get("item_title"),
        "history_item_sid": row.get("history_item_sid"),
        "item_sid": row.get("item_sid"),
        "reasoning_path": reasoning_path,
        "behavior_json": json.dumps(
            trace["behavior"], ensure_ascii=False, separators=(",", ":")
        ),
        "interest_json": json.dumps(
            trace["interest"], ensure_ascii=False, separators=(",", ":")
        ),
        "intent_json": json.dumps(
            trace["intent"], ensure_ascii=False, separators=(",", ":")
        ),
        "process_trace_json": json.dumps(
            trace, ensure_ascii=False, separators=(",", ":")
        ),
        "process_schema_version": SCHEMA_VERSION,
        "generation_signature": signature,
        "generation_model": model,
        "generator_target_visible": False,
        "reviewer_target_visible": False,
        "reviewed": review,
    }


def run_pool(
    tasks: list[tuple[str, int, dict[str, Any]]],
    process_fn: Any,
    out_path: str,
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
                append_jsonl(
                    out_path,
                    process_fn(client, row_key, source_index, row),
                )
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


def regenerate(
    category: str,
    out_path: str,
    endpoints: list[str],
    per_endpoint: int,
    limit: int,
    model: str,
    review: bool,
    dry_run: bool,
    get_client: Any = None,
) -> None:
    source = load_dataset(HF_REPO, f"{category}_reasoning", split="train")
    if limit > 0:
        source = source.select(range(min(limit, len(source))))
    catalog = build_catalog(category)
    title_index = build_catalog_title_index(catalog)
    signature = generation_signature(model, review)
    done = load_done_keys(out_path, signature)

    tasks = []
    for source_index, dataset_row in enumerate(source):
        row = dict(dataset_row)
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
        _, _, row = tasks[0]
        _, _, history_block = history_from_row(row, catalog)
        print(generator_prompt(history_block))
        return

    def process(
        client: Any,
        row_key: str,
        source_index: int,
        row: dict[str, Any],
    ) -> dict[str, Any]:
        history_sids, history_titles, history_block = history_from_row(
            row, catalog
        )
        trace = generate_trace(
            client,
            model,
            history_block,
            history_sids,
            history_titles,
            title_index,
            review,
        )
        reasoning_path = render_trace(trace)
        validate_no_target_leakage(
            reasoning_path,
            row,
            history_sids,
            history_titles,
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
    run_pool(tasks, process, out_path, endpoints, per_endpoint, get_client)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate simple target-blind Phase-2 process traces."
    )
    parser.add_argument("--category", default="Video_Games", choices=CATEGORIES)
    parser.add_argument("--out-dir", default="./regen_phase2_process")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--per-endpoint", type=int, default=DEFAULT_PER_ENDPOINT)
    parser.add_argument("--endpoints", nargs="*", default=None)
    parser.add_argument("--limit", type=int, default=-1)
    parser.add_argument(
        "--review",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.per_endpoint < 1:
        parser.error("--per-endpoint must be at least 1")

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

    os.makedirs(args.out_dir, exist_ok=True)
    output_jsonl = os.path.join(
        args.out_dir,
        f"{args.category}.phase2_process.jsonl",
    )
    run_lock = None
    if not args.dry_run:
        run_lock = acquire_run_lock(output_jsonl)
    try:
        regenerate(
            category=args.category,
            out_path=output_jsonl,
            endpoints=endpoints,
            per_endpoint=args.per_endpoint,
            limit=args.limit,
            model=args.model,
            review=args.review,
            dry_run=args.dry_run,
            get_client=get_client,
        )
    finally:
        if run_lock is not None:
            release_run_lock(run_lock)
    if not args.dry_run:
        jsonl_to_csv(
            output_jsonl,
            output_jsonl.replace(".jsonl", ".csv"),
        )
        jsonl_to_csv(
            output_jsonl,
            os.path.join(
                args.out_dir,
                f"{args.category}.integrated_narrative.csv",
            ),
        )


if __name__ == "__main__":
    main()
