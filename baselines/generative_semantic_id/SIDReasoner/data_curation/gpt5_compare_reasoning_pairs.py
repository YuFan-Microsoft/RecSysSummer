"""Blind pairwise GPT-5.4 evaluation of aligned reasoning-result JSONL files."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import multiprocessing as mp
import os
import queue
import random
import re
import time
from typing import Any

from gpt5_endpoint_test import ENDPOINTS, get_GPT5_client


MODEL = "gpt-5.4"
MAX_API_ATTEMPTS = 4
MAX_COMPLETION_TOKENS = 1400
SCORE_KEYS = (
    "history_factuality",
    "future_interest_grounding",
    "exploit_quality",
    "explore_quality",
    "specificity",
    "conciseness",
    "target_bridge_quality",
    "overall_quality",
)

SYSTEM_PROMPT = """You are a strict, neutral evaluator of recommendation reasoning traces.
Compare two anonymized traces for the same chronological user history and held-out next item.
Do not infer system identity from writing style or candidate order. Judge reasoning quality, not
whether a decoder happened to retrieve the exact target SID. The held-out target is visible only
to assess whether a future-interest bridge is plausible; a good trace must remain grounded in
history and must not leak or simply name the target.

Score each candidate from 1 (very poor) to 5 (excellent) on:
- history_factuality: summary claims are supported by the cited history titles.
- future_interest_grounding: predicted interests follow from cited history evidence.
- exploit_quality: exploit lines continue interests directly instantiated in history.
- explore_quality: explore lines make a specific, defensible one-step semantic transfer.
- specificity: claims use concrete attributes rather than generic platform/category language.
- conciseness: claims are nonredundant and economical without omitting needed bridges.
- target_bridge_quality: the trace contains a natural history-to-target-interest bridge without leakage.
- overall_quality: holistic reasoning usefulness and faithfulness.

Choose overall_winner as exactly A, B, or tie. A tie is appropriate when differences are negligible.
Return ONLY one JSON object with exactly this structure:
{
  "A": {"history_factuality": 1, "future_interest_grounding": 1, "exploit_quality": 1,
        "explore_quality": 1, "specificity": 1, "conciseness": 1,
        "target_bridge_quality": 1, "overall_quality": 1},
  "B": {"history_factuality": 1, "future_interest_grounding": 1, "exploit_quality": 1,
        "explore_quality": 1, "specificity": 1, "conciseness": 1,
        "target_bridge_quality": 1, "overall_quality": 1},
  "overall_winner": "tie",
  "decisive_difference": "one concise comparison",
  "candidate_a_weakness": "one concise weakness",
  "candidate_b_weakness": "one concise weakness"
}"""

USER_TEMPLATE = """CHRONOLOGICAL HISTORY (title [SID]):
{history}

HELD-OUT NEXT ITEM (for bridge assessment only):
{target_title} [{target_sid}]

TARGET TYPE:
{target_type}

CANDIDATE A:
{candidate_a}

CANDIDATE B:
{candidate_b}

Evaluate both traces independently, then make the pairwise decision. Return only JSON."""


def load_jsonl(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sample_pairs(
    left_rows: list[dict[str, Any]],
    right_rows: list[dict[str, Any]],
    limit: int,
    seed: int,
    swap_orientation: bool = False,
) -> list[dict[str, Any]]:
    if len(left_rows) != len(right_rows):
        raise ValueError("Input files contain different row counts")

    aligned = []
    for left, right in zip(left_rows, right_rows):
        alignment_key = (left.get("source_index"), left.get("user_id"), left.get("item_sid"))
        right_key = (right.get("source_index"), right.get("user_id"), right.get("item_sid"))
        if alignment_key != right_key:
            raise ValueError(f"Inputs are not aligned at {alignment_key!r} vs {right_key!r}")
        aligned.append((left, right))

    repeats = [pair for pair in aligned if pair[0]["item_sid"] in pair[0]["history_sid_list"]]
    novel = [pair for pair in aligned if pair[0]["item_sid"] not in pair[0]["history_sid_list"]]
    randomizer = random.Random(seed)
    if limit < len(repeats):
        selected = randomizer.sample(repeats, limit)
    else:
        selected = repeats + randomizer.sample(novel, min(limit - len(repeats), len(novel)))
    randomizer.shuffle(selected)

    tasks = []
    for left, right in selected:
        source_index = int(left["source_index"])
        orientation = "left_is_A" if random.Random(f"{seed}:{source_index}").random() < 0.5 else "right_is_A"
        if swap_orientation:
            orientation = "right_is_A" if orientation == "left_is_A" else "left_is_A"
        candidate_a = left if orientation == "left_is_A" else right
        candidate_b = right if orientation == "left_is_A" else left
        history = "\n".join(
            f"{index}. {title} [{sid}]"
            for index, (sid, title) in enumerate(
                zip(left["history_sid_list"], left["history_title_list"]), start=1
            )
        )
        target_repeat_count = left["history_sid_list"].count(left["item_sid"])
        target_type = (
            f"repeat target; appears {target_repeat_count} time(s) in history; "
            f"is_latest={left['history_sid_list'][-1] == left['item_sid']}"
            if target_repeat_count
            else "novel target; does not appear in history"
        )
        prompt = USER_TEMPLATE.format(
            history=history,
            target_title=left["item_title"],
            target_sid=left["item_sid"],
            target_type=target_type,
            candidate_a=candidate_a["generated_reasoning_path"],
            candidate_b=candidate_b["generated_reasoning_path"],
        )
        task_id = hashlib.sha256(
            f"{seed}:{source_index}:{left['item_sid']}:swap={swap_orientation}".encode("utf-8")
        ).hexdigest()[:20]
        tasks.append(
            {
                "task_id": task_id,
                "source_index": source_index,
                "user_id": left.get("user_id"),
                "target_sid": left["item_sid"],
                "target_title": left["item_title"],
                "target_type": "repeat" if target_repeat_count else "novel",
                "target_repeat_count": target_repeat_count,
                "target_is_latest": left["history_sid_list"][-1] == left["item_sid"],
                "orientation": orientation,
                "prompt": prompt,
            }
        )
    return tasks


def parse_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match is None:
            raise
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("Judge response is not a JSON object")
    return value


def validate_judgment(value: dict[str, Any]) -> dict[str, Any]:
    for candidate in ("A", "B"):
        scores = value.get(candidate)
        if not isinstance(scores, dict):
            raise ValueError(f"Missing candidate score object {candidate}")
        if set(scores) != set(SCORE_KEYS):
            raise ValueError(f"Candidate {candidate} score keys do not match schema")
        for key in SCORE_KEYS:
            score = scores[key]
            if not isinstance(score, int) or not 1 <= score <= 5:
                raise ValueError(f"Invalid {candidate}.{key}: {score!r}")
    if value.get("overall_winner") not in {"A", "B", "tie"}:
        raise ValueError("overall_winner must be A, B, or tie")
    for key in ("decisive_difference", "candidate_a_weakness", "candidate_b_weakness"):
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise ValueError(f"Missing nonempty {key}")
    return value


def judge(client: Any, task: dict[str, Any], reasoning_effort: str) -> dict[str, Any]:
    last_error = None
    for attempt in range(1, MAX_API_ATTEMPTS + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": task["prompt"]},
                ],
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                reasoning_effort=reasoning_effort,
            )
            return validate_judgment(parse_json_object(response.choices[0].message.content or ""))
        except Exception as error:
            last_error = error
            if attempt < MAX_API_ATTEMPTS:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(f"GPT judge failed after {MAX_API_ATTEMPTS} attempts: {last_error}")


def worker(
    task_queue: Any,
    result_queue: Any,
    endpoint: str,
    reasoning_effort: str,
) -> None:
    try:
        client = get_GPT5_client(endpoint)
    except Exception as error:
        result_queue.put(("worker_error", endpoint, str(error)[:1000]))
        return
    while True:
        task = task_queue.get()
        if task is None:
            return
        try:
            judgment = judge(client, task, reasoning_effort)
            result_queue.put(("ok", task, judgment, endpoint))
        except Exception as error:
            result_queue.put(("fail", task["task_id"], endpoint, str(error)[:1000]))


def load_done(path: str) -> set[str]:
    if not os.path.exists(path):
        return set()
    done = set()
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            try:
                done.add(json.loads(line)["task_id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def append_jsonl(path: str, value: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def canonicalize(task: dict[str, Any], judgment: dict[str, Any], endpoint: str) -> dict[str, Any]:
    left_label = "SOTA"
    right_label = "OTHER"
    a_label = left_label if task["orientation"] == "left_is_A" else right_label
    b_label = right_label if task["orientation"] == "left_is_A" else left_label
    winner = judgment["overall_winner"]
    canonical_winner = "tie" if winner == "tie" else (a_label if winner == "A" else b_label)
    return {
        key: value for key, value in task.items() if key not in {"prompt", "orientation"}
    } | {
        "a_label": a_label,
        "b_label": b_label,
        "SOTA_scores": judgment["A"] if a_label == "SOTA" else judgment["B"],
        "OTHER_scores": judgment["B"] if b_label == "OTHER" else judgment["A"],
        "winner": canonical_winner,
        "decisive_difference": judgment["decisive_difference"],
        "SOTA_weakness": (
            judgment["candidate_a_weakness"] if a_label == "SOTA" else judgment["candidate_b_weakness"]
        ),
        "OTHER_weakness": (
            judgment["candidate_b_weakness"] if b_label == "OTHER" else judgment["candidate_a_weakness"]
        ),
        "endpoint": endpoint,
    }


def run_pool(
    tasks: list[dict[str, Any]],
    output: str,
    endpoints: list[str],
    per_endpoint: int,
    reasoning_effort: str,
) -> None:
    done_ids = load_done(output)
    pending = [task for task in tasks if task["task_id"] not in done_ids]
    if not pending:
        print("Nothing to do")
        return
    context = mp.get_context("spawn")
    task_queue = context.Queue()
    result_queue = context.Queue()
    worker_endpoints = [endpoint for endpoint in endpoints for _ in range(per_endpoint)]
    workers = [
        context.Process(
            target=worker,
            args=(task_queue, result_queue, endpoint, reasoning_effort),
            daemon=True,
        )
        for endpoint in worker_endpoints
    ]
    for process in workers:
        process.start()
    for task in pending:
        task_queue.put(task)
    for _ in workers:
        task_queue.put(None)

    started = time.time()
    completed = 0
    failed = 0
    print(
        f"{len(pending)} tasks / {len(endpoints)} endpoints x {per_endpoint} "
        f"= {len(workers)} processes",
        flush=True,
    )
    try:
        while completed + failed < len(pending):
            try:
                message = result_queue.get(timeout=1)
            except queue.Empty:
                if not any(process.is_alive() for process in workers):
                    raise RuntimeError("All workers exited before completing the task queue")
                continue
            if message[0] == "ok":
                append_jsonl(output, canonicalize(message[1], message[2], message[3]))
                completed += 1
            elif message[0] == "fail":
                failed += 1
                print(f"FAIL {message[1]} on {message[2]}: {message[3]}", flush=True)
            else:
                print(f"WORKER ERROR {message[1]}: {message[2]}", flush=True)
            finished = completed + failed
            if finished % 25 == 0 or finished == len(pending):
                elapsed = time.time() - started
                rate = finished / elapsed if elapsed else 0.0
                eta = (len(pending) - finished) / rate if rate else math.inf
                print(
                    f"{finished}/{len(pending)} | {rate:.2f} rows/s | "
                    f"ETA {eta / 60:.1f} min | failed={failed}",
                    flush=True,
                )
    finally:
        for process in workers:
            process.join(timeout=5)
        for process in workers:
            if process.is_alive():
                process.terminate()


def summarize(output: str, summary_path: str) -> dict[str, Any]:
    rows = load_jsonl(output)
    summary: dict[str, Any] = {"rows": len(rows), "strata": {}}
    for stratum, selected in (
        ("all_sampled", rows),
        ("repeat", [row for row in rows if row["target_type"] == "repeat"]),
        ("novel", [row for row in rows if row["target_type"] == "novel"]),
    ):
        if not selected:
            continue
        wins = Counter(row["winner"] for row in selected)
        score_means = {}
        for model_label in ("SOTA", "OTHER"):
            score_means[model_label] = {
                key: sum(row[f"{model_label}_scores"][key] for row in selected) / len(selected)
                for key in SCORE_KEYS
            }
        summary["strata"][stratum] = {
            "rows": len(selected),
            "wins": dict(wins),
            "win_rates": {key: value / len(selected) for key, value in wins.items()},
            "score_means": score_means,
            "score_delta_SOTA_minus_OTHER": {
                key: score_means["SOTA"][key] - score_means["OTHER"][key]
                for key in SCORE_KEYS
            },
        }
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sota", required=True)
    parser.add_argument("--other", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--per-endpoint", type=int, default=2)
    parser.add_argument("--endpoints", nargs="*", default=None)
    parser.add_argument("--reasoning-effort", choices=("low", "medium", "high"), default="low")
    parser.add_argument("--swap-orientation", action="store_true")
    args = parser.parse_args()

    endpoints = args.endpoints or list(ENDPOINTS)
    unknown = [endpoint for endpoint in endpoints if endpoint not in ENDPOINTS]
    if unknown:
        parser.error(f"Unknown endpoints: {unknown}")
    if args.limit < 1 or args.per_endpoint < 1:
        parser.error("--limit and --per-endpoint must be positive")

    tasks = sample_pairs(
        load_jsonl(args.sota),
        load_jsonl(args.other),
        args.limit,
        args.seed,
        swap_orientation=args.swap_orientation,
    )
    run_pool(tasks, args.output, endpoints, args.per_endpoint, args.reasoning_effort)
    summary = summarize(args.output, args.summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()