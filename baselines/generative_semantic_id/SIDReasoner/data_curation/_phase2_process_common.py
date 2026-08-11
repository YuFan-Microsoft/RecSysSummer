"""Internal HF, Azure, concurrency, resume, and output helpers for Phase-2 V4."""

from __future__ import annotations

import ast
import csv
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

try:
    import fcntl
except ModuleNotFoundError:
    fcntl = None
    import msvcrt
else:
    msvcrt = None


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

ITEM_SID_RE = re.compile(r"<a_[^<>\s]+><b_[^<>\s]+><c_[^<>\s]+>")

_write_lock = threading.Lock()


@contextmanager
def single_process_lock(path: str):
    """Allow only one process to generate a category into an output directory."""
    handle = open(path, "a+", encoding="utf-8")
    try:
        try:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(" ")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except (BlockingIOError, OSError) as error:
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
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            else:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            handle.close()


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
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())


def append_csv_row(path: str, value: dict[str, Any]) -> None:
    """Append one result to a live CSV mirror and force it to disk."""
    with _write_lock:
        write_header = not os.path.exists(path) or os.path.getsize(path) == 0
        with open(path, "a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(value))
            if write_header:
                writer.writeheader()
            writer.writerow(value)
            handle.flush()
            os.fsync(handle.fileno())


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
