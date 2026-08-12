"""Run Phase-3 rejection-sampling inference on eight single-GPU workers.

The input rows follow ``gpt5_regenerate_phase2_process_data_V4.py``:
``Video_Games_reasoning/train`` from
``yufan/recsys-genrec-dataset-refresh-gpt5.4-candidateV1``.  Only the history
is placed in the model prompt; the existing ``reasoning_path`` and target SID
are retained as references in the output.

Each worker owns one GPU and one contiguous eighth of the selected rows. The
worker samples a fixed number of target-blind reasoning traces, deduplicates
exact reasoning strings, and runs constrained SID beam search for each
unique candidate. The best rule-valid target hit is retained downstream.

Phase-3 VERL/FSDP checkpoints must be merged to Hugging Face format first:

    python phase3_rl/merge_fsdp_checkpoint.py \
        --checkpoint /path/to/global_step_300

Example (launches eight processes on GPUs 0-7):

    python data_curation/rejection_sampling/distributed_phase3_inference.py \
        --checkpoint /path/to/global_step_300/actor_merged \
        --category Video_Games \
        --num-samples 1000 \
        --samples-per-prompt 4 \
        --num-beams 100 \
        --output-dir ./rejection_sampling_output
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import multiprocessing as mp
import os
import queue
import random
import shutil
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_CURATION_DIR = SCRIPT_DIR.parent
REPO_ROOT = DATA_CURATION_DIR.parent
for import_root in (str(REPO_ROOT), str(DATA_CURATION_DIR)):
    if import_root not in sys.path:
        sys.path.insert(0, import_root)


HF_REPO = "yufan/recsys-genrec-dataset-refresh-gpt5.4-candidateV2"
CATEGORIES = ("Video_Games",)
SYSTEM_INSTRUCTION = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.
Can you recommend the next item for the user based on their interaction history?
"""


@dataclass(frozen=True)
class WorkerConfig:
    checkpoint: str
    dataset_repo: str
    category: str
    split: str
    start_index: int
    num_rows: int
    world_size: int
    output_dir: str
    batch_size: int
    samples_per_prompt: int
    max_target_rank: int
    seed: int
    max_prompt_length: int
    max_new_tokens: int
    num_beams: int
    sid_length: int
    temperature: float
    top_p: float
    top_k: int
    min_p: float
    gpu_memory_utilization: float
    max_num_batched_tokens: int
    max_num_seqs: int
    enforce_eager: bool


def _maybe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str):
        text = value.strip()
        if text.startswith(("[", "(")):
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                return [value]
            if isinstance(parsed, (list, tuple)):
                return list(parsed)
        return [value]
    if value is None:
        return []
    return [value]


def _batched(values: list[Any], batch_size: int):
    for start in range(0, len(values), batch_size):
        yield values[start : start + batch_size]


def _rank_bucket(rank: int | None, beam_width: int) -> str:
    if rank is None:
        return "miss"
    if rank == 1:
        return "rank_1"
    for upper in (5, 10, 20, 50, 100):
        if rank <= min(upper, beam_width):
            lower = 2 if upper == 5 else {10: 6, 20: 11, 50: 21, 100: 51}[upper]
            return f"rank_{lower}_{upper}"
    return f"rank_101_{beam_width}"


def _best_target_rank(records: list[dict[str, Any]]) -> int | None:
    ranks = [
        int(record["target_rank"])
        for record in records
        if record.get("format_valid")
        and record.get("rule_quality_valid")
        and record.get("target_rank") is not None
    ]
    return min(ranks) if ranks else None


def _candidate_sort_key(record: dict[str, Any]) -> tuple[float, int]:
    rank = record.get("target_rank")
    return (
        float(rank) if rank is not None else math.inf,
        int(record["sample_index"]),
    )


def _normalize_claim(text: str) -> str:
    return " ".join(text.casefold().split())


def _reasoning_rule_checks(
    trace: dict[str, str],
    target_sid: str,
    target_title: str,
    history_sids: list[str],
    phase2_v4: Any,
) -> dict[str, Any]:
    """Apply deterministic checks that do not require catalog semantics or an LLM."""
    errors = []
    summary_claims = []
    for line in trace["history_summary"].splitlines():
        match = phase2_v4.HISTORY_SUMMARY_LINE_RE.fullmatch(line.strip())
        if match is not None:
            summary_claims.append(_normalize_claim(match.group("text")))
    future_claims = []
    for line in trace["future_interests"].splitlines():
        match = phase2_v4.FUTURE_INTEREST_LINE_RE.fullmatch(line.strip())
        if match is not None:
            future_claims.append(_normalize_claim(match.group("text")))

    duplicate_summary_claims = len(summary_claims) != len(set(summary_claims))
    duplicate_future_interests = len(future_claims) != len(set(future_claims))
    if duplicate_summary_claims:
        errors.append("duplicate_history_summary_claim")
    if duplicate_future_interests:
        errors.append("duplicate_future_interest")

    history_sid_set = set(history_sids)
    target_sid_leakage = bool(
        target_sid
        and target_sid not in history_sid_set
        and target_sid in phase2_v4.render_trace(trace)
    )
    if target_sid_leakage:
        errors.append("target_sid_leakage")

    normalized_reasoning = _normalize_claim(phase2_v4.render_trace(trace))
    normalized_target_title = _normalize_claim(target_title)
    target_title_leakage = bool(
        normalized_target_title
        and len(normalized_target_title) >= 8
        and normalized_target_title in normalized_reasoning
    )
    if target_title_leakage:
        errors.append("target_title_leakage")

    return {
        "rule_quality_valid": not errors,
        "rule_quality_errors": errors,
        "rule_duplicate_summary_claims": duplicate_summary_claims,
        "rule_duplicate_future_interests": duplicate_future_interests,
        "rule_target_sid_leakage": target_sid_leakage,
        "rule_target_title_leakage": target_title_leakage,
    }


def _build_messages(history_sids: list[str]) -> list[dict[str, str]]:
    history = ", ".join(history_sids)
    prompt = f"The user has sequentially interacted with items {history}. Can you recommend the next item for him? Let's think step by step before making recommendation. Directly output the item SID after thinking."
    return [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": prompt},
    ]


def _validate_checkpoint(checkpoint: str) -> Path:
    path = Path(checkpoint).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Checkpoint directory does not exist: {path}")
    if (path / "config.json").is_file():
        return path

    actor_dir = path if path.name == "actor" else path / "actor"
    if (actor_dir / "huggingface").is_dir():
        step_dir = actor_dir.parent
        suggested_output = step_dir / "actor_merged"
        raise ValueError(
            "The checkpoint is an unmerged VERL/FSDP actor. Merge it before "
            "inference with:\n"
            f"  python phase3_rl/merge_fsdp_checkpoint.py --checkpoint {step_dir} "
            f"--output-dir {suggested_output}"
        )
    raise ValueError(
        f"{path} is not a loadable Hugging Face checkpoint: config.json is missing"
    )


def _validate_dataset_schema(
    dataset_repo: str,
    category: str,
    split: str,
    start_index: int,
    num_samples: int,
) -> tuple[int, int]:
    from datasets import load_dataset

    dataset = load_dataset(dataset_repo, f"{category}_reasoning", split=split)
    required = {"history_item_sid", "item_sid", "reasoning_path"}
    missing = sorted(required - set(dataset.column_names))
    if missing:
        raise ValueError(
            f"{category}_reasoning/{split} is missing required columns: {missing}"
        )
    if start_index < 0 or start_index >= len(dataset):
        raise ValueError(
            f"--start-index must be in [0, {len(dataset) - 1}], got {start_index}"
        )
    available = len(dataset) - start_index
    selected = available if num_samples < 0 else min(num_samples, available)
    if selected < 1:
        raise ValueError("The selected inference subset is empty")
    return len(dataset), selected


def _extract_and_validate_reasoning(
    raw_reasoning_output: str,
    phase2_v4: Any,
    history_sids: list[str],
) -> tuple[str, bool, str | None]:
    text = raw_reasoning_output.strip()
    open_count = text.count("<think>")
    close_count = text.count("</think>")
    if open_count == 0 and close_count == 0:
        reasoning_path = text
    elif open_count == 1 and close_count == 1:
        if not text.startswith("<think>"):
            return text, False, "<think> must be the first non-whitespace text"
        close_index = text.index("</think>")
        open_end = len("<think>")
        if close_index < open_end:
            return text, False, "</think> appears before <think>"
        reasoning_path = text[open_end:close_index].strip()
    elif open_count == 0 and close_count == 1:
        reasoning_path = text[: text.index("</think>")].strip()
    else:
        return (
            text,
            False,
            "expected no think wrapper, one complete wrapper, or one legacy "
            f"closing tag; found <think>={open_count}, </think>={close_count}",
        )
    try:
        trace = phase2_v4.parse_and_validate_generation(
            reasoning_path,
            history_sids,
        )
    except phase2_v4.TraceValidationError as error:
        return reasoning_path, False, str(error)
    return phase2_v4.render_trace(trace), True, None


def _configure_worker_environment(gpu_id: str, output_dir: Path) -> None:
    os.environ["CUDA_VISIBLE_DEVICES"] = gpu_id
    cache_dir = output_dir / ".cache" / f"gpu_{gpu_id.replace('/', '_')}"
    triton_dir = cache_dir / "triton"
    inductor_dir = cache_dir / "inductor"
    vllm_dir = cache_dir / "vllm"
    for directory in (triton_dir, inductor_dir, vllm_dir):
        directory.mkdir(parents=True, exist_ok=True)
    os.environ["TRITON_CACHE_DIR"] = str(triton_dir)
    os.environ["TORCHINDUCTOR_CACHE_DIR"] = str(inductor_dir)
    os.environ["VLLM_CACHE_ROOT"] = str(vllm_dir)
    cpu_threads = os.environ.get("SIDR_EVAL_CPU_THREADS", "1")
    for variable in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ[variable] = cpu_threads


def _worker_main(
    config: WorkerConfig,
    rank: int,
    gpu_id: str,
    progress_queue: Any,
) -> None:
    try:
        _configure_worker_environment(gpu_id, Path(config.output_dir))
        os.environ["SIDR_HF_REPO"] = config.dataset_repo

        from datasets import load_dataset
        import torch
        from vllm import LLM, SamplingParams

        import gpt5_regenerate_phase2_process_data_V4 as phase2_v4
        import hf_data
        from verl.workers.rollout.sid_constrained_decoding import (
            build_sid_token_trie,
            prepare_reasoning_prefix,
            vllm_constrained_beam_search,
        )

        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise RuntimeError(
                "Each worker must see exactly one CUDA GPU through CUDA_VISIBLE_DEVICES"
            )
        device_name = torch.cuda.get_device_name(0)
        phase2_v4.HF_REPO = config.dataset_repo
        random.seed(config.seed + rank)
        shard_start = config.start_index + rank * config.num_rows // config.world_size
        shard_end = (
            config.start_index
            + (rank + 1) * config.num_rows // config.world_size
        )
        source = load_dataset(
            config.dataset_repo,
            f"{config.category}_reasoning",
            split=config.split,
        )
        catalog = phase2_v4.build_catalog(config.category)

        llm = LLM(
            model=config.checkpoint,
            max_model_len=config.max_prompt_length + config.max_new_tokens,
            max_num_batched_tokens=config.max_num_batched_tokens,
            max_num_seqs=config.max_num_seqs,
            max_logprobs=config.num_beams,
            logprobs_mode="processed_logprobs",
            dtype="bfloat16",
            gpu_memory_utilization=config.gpu_memory_utilization,
            tensor_parallel_size=1,
            seed=config.seed + rank,
            enforce_eager=config.enforce_eager,
            enable_chunked_prefill=True,
            enable_prefix_caching=True,
        )
        tokenizer = llm.get_tokenizer()
        if tokenizer.eos_token_id is None:
            raise ValueError("The checkpoint tokenizer must define an EOS token")

        end_think_marker = tokenizer.encode("</think>", add_special_tokens=False)
        reasoning_separator = tokenizer.encode(
            "</think>\n\n", add_special_tokens=False
        )
        if not end_think_marker:
            raise ValueError("The checkpoint tokenizer cannot encode </think>")
        if reasoning_separator[: len(end_think_marker)] != end_think_marker:
            raise ValueError(
                "The </think> separator does not extend the tokenizer marker"
            )
        reserved_tokens = config.sid_length + len(reasoning_separator) + 1
        max_reasoning_tokens = config.max_new_tokens - reserved_tokens
        if max_reasoning_tokens < 1:
            raise ValueError(
                "--max-new-tokens is too short for reasoning and SID decoding"
            )

        sid_token_trie = build_sid_token_trie(
            tokenizer,
            hf_data.load_sid_indices(config.category).values(),
            depth=config.sid_length,
        )
        def reasoning_sampling_params(sample_count: int) -> Any:
            return SamplingParams(
                n=sample_count,
                logprobs=0,
                max_tokens=max_reasoning_tokens,
                min_tokens=1,
                repetition_penalty=1.0,
                detokenize=False,
                top_p=config.top_p,
                top_k=config.top_k,
                min_p=config.min_p,
                temperature=config.temperature,
            )

        contexts = []
        for source_index in range(shard_start, shard_end):
            row = dict(source[source_index])
            history_sids, _, _ = phase2_v4.history_from_row(
                row, catalog
            )
            prompt_ids = tokenizer.apply_chat_template(
                _build_messages(history_sids),
                add_generation_prompt=True,
                tokenize=True,
                return_tensors=None,
            )
            if len(prompt_ids) > config.max_prompt_length:
                raise ValueError(
                    f"source_index={source_index} prompt has {len(prompt_ids)} "
                    f"tokens, exceeding {config.max_prompt_length}"
                )
            contexts.append(
                {
                    "source_index": source_index,
                    "row": row,
                    "history_sids": history_sids,
                    "prompt_ids": list(prompt_ids),
                }
            )

        output_path = Path(config.output_dir) / f"rank_{rank:02d}.jsonl"
        progress_queue.put(
            ("ready", rank, shard_start, shard_end, device_name)
        )
        with output_path.open("w", encoding="utf-8") as output_handle:
            for context_batch in _batched(contexts, config.batch_size):
                states = [
                    {
                        "context": context,
                        "next_sample_index": 0,
                        "records": [],
                        "reasoning_seen": {},
                    }
                    for context in context_batch
                ]

                while True:
                    active_states = [
                        state
                        for state in states
                        if state["next_sample_index"]
                        < config.samples_per_prompt
                    ]
                    if not active_states:
                        break

                    remaining = min(
                        config.samples_per_prompt
                        - state["next_sample_index"]
                        for state in active_states
                    )
                    round_sample_count = min(
                        config.samples_per_prompt,
                        remaining,
                    )
                    reasoning_outputs = llm.generate(
                        prompts=[
                            {
                                "prompt_token_ids": state["context"][
                                    "prompt_ids"
                                ]
                            }
                            for state in active_states
                        ],
                        sampling_params=reasoning_sampling_params(
                            round_sample_count
                        ),
                        use_tqdm=False,
                    )
                    if len(reasoning_outputs) != len(active_states):
                        raise RuntimeError(
                            "vLLM returned an unexpected reasoning batch size"
                        )

                    candidates = []
                    beam_prompt_ids = []
                    beam_candidate_indices = []
                    for state, request_output in zip(
                        active_states,
                        reasoning_outputs,
                    ):
                        if len(request_output.outputs) != round_sample_count:
                            raise RuntimeError(
                                "vLLM returned an unexpected number of samples"
                            )
                        for offset, completion in enumerate(
                            request_output.outputs
                        ):
                            sample_index = state["next_sample_index"] + offset
                            response_ids = list(completion.token_ids)
                            raw_reasoning_output = tokenizer.decode(
                                response_ids,
                                skip_special_tokens=False,
                            ).strip()
                            duplicate_of = state["reasoning_seen"].get(
                                raw_reasoning_output
                            )
                            if duplicate_of is None:
                                state["reasoning_seen"][raw_reasoning_output] = (
                                    sample_index
                                )
                            candidate = {
                                "state": state,
                                "sample_index": sample_index,
                                "raw_reasoning_output": raw_reasoning_output,
                                "reasoning_prefix_ids": None,
                                "sid_beams": [],
                                "prefix_error": None,
                            }
                            if duplicate_of is None:
                                try:
                                    (
                                        reasoning_prefix_ids,
                                        _reasoning_token_length,
                                    ) = prepare_reasoning_prefix(
                                        response_ids,
                                        end_think_marker=end_think_marker,
                                        reasoning_separator=reasoning_separator,
                                        eos_token_id=tokenizer.eos_token_id,
                                        max_length=(
                                            config.max_new_tokens
                                            - config.sid_length
                                            - 1
                                        ),
                                    )
                                    candidate["reasoning_prefix_ids"] = (
                                        reasoning_prefix_ids
                                    )
                                    beam_prompt_ids.append(
                                        state["context"]["prompt_ids"]
                                        + reasoning_prefix_ids
                                    )
                                    beam_candidate_indices.append(len(candidates))
                                except (RuntimeError, ValueError) as error:
                                    candidate["prefix_error"] = str(error)
                            candidates.append(candidate)
                        state["next_sample_index"] += round_sample_count

                    if beam_prompt_ids:
                        generated_beams = vllm_constrained_beam_search(
                            llm,
                            prompts_ids=beam_prompt_ids,
                            sid_token_trie=sid_token_trie,
                            depth=config.sid_length,
                            beam_width=config.num_beams,
                        )
                        if len(generated_beams) != len(beam_candidate_indices):
                            raise RuntimeError(
                                "Constrained decoding returned an unexpected "
                                "batch size"
                            )
                        for candidate_index, sid_beams in zip(
                            beam_candidate_indices,
                            generated_beams,
                        ):
                            candidates[candidate_index]["sid_beams"] = sid_beams

                    batch_validity = []
                    for candidate in candidates:
                        state = candidate["state"]
                        context = state["context"]
                        row = context["row"]
                        reasoning_path, format_valid, format_error = (
                            _extract_and_validate_reasoning(
                                candidate["raw_reasoning_output"],
                                phase2_v4,
                                context["history_sids"],
                            )
                        )
                        if candidate["prefix_error"] is not None:
                            format_valid = False
                            format_error = candidate["prefix_error"]

                        rule_checks = {
                            "rule_quality_valid": False,
                            "rule_quality_errors": ["format_invalid"],
                            "rule_duplicate_summary_claims": False,
                            "rule_duplicate_future_interests": False,
                            "rule_target_sid_leakage": False,
                            "rule_target_title_leakage": False,
                        }
                        if format_valid:
                            trace = phase2_v4.parse_and_validate_generation(
                                reasoning_path,
                                context["history_sids"],
                            )
                            rule_checks = _reasoning_rule_checks(
                                trace,
                                str(row.get("item_sid") or ""),
                                str(row.get("item_title") or ""),
                                context["history_sids"],
                                phase2_v4,
                            )

                        decoded_beams = [
                            tokenizer.decode(
                                beam,
                                skip_special_tokens=False,
                            )
                            for beam in candidate["sid_beams"]
                        ]
                        target_sid = str(row.get("item_sid") or "")
                        target_rank = (
                            decoded_beams.index(target_sid) + 1
                            if target_sid in decoded_beams
                            else None
                        )
                        record = {
                            "source_index": context["source_index"],
                            "sample_index": candidate["sample_index"],
                            "user_id": row.get("user_id"),
                            "history_item_sid": context["history_sids"],
                            "history_item_title": _maybe_list(
                                row.get("history_item_title")
                            ),
                            "item_sid": row.get("item_sid"),
                            "item_title": row.get("item_title"),
                            "generated_reasoning_path": reasoning_path,
                            "target_rank": target_rank,
                            "target_rank_bucket": _rank_bucket(
                                target_rank,
                                config.num_beams,
                            ),
                            "rule_valid_hit": (
                                format_valid
                                and rule_checks["rule_quality_valid"]
                                and target_rank is not None
                            ),
                            "rule_quality_valid": rule_checks[
                                "rule_quality_valid"
                            ],
                            "format_valid": format_valid,
                        }
                        state["records"].append(record)
                        record["best_target_rank_so_far"] = (
                            _best_target_rank(state["records"])
                        )
                        output_handle.write(
                            json.dumps(record, ensure_ascii=False) + "\n"
                        )
                        batch_validity.append(format_valid)
                    output_handle.flush()

                    progress_queue.put(
                        (
                            "progress",
                            rank,
                            {
                                "candidate_validity": batch_validity,
                                "rows_finished": len(active_states),
                            },
                        )
                    )

        progress_queue.put(("finished", rank, None))
    except BaseException:
        progress_queue.put(("finished", rank, traceback.format_exc()))


def _minimal_selected(record: dict[str, Any]) -> dict[str, Any]:
    reasoning_path = record["generated_reasoning_path"]
    return {
        "source_index": record["source_index"],
        "user_id": record.get("user_id"),
        "history_item_title": record.get("history_item_title"),
        "item_title": record.get("item_title"),
        "history_item_sid": record.get("history_item_sid"),
        "item_sid": record.get("item_sid"),
        "reasoning_path": reasoning_path,
        "target_rank": record["target_rank"],
    }


def _merge_minimal_outputs(config: WorkerConfig) -> dict[str, Any]:
    output_dir = Path(config.output_dir)
    records = []
    shard_paths = []
    for rank in range(config.world_size):
        shard_path = output_dir / f"rank_{rank:02d}.jsonl"
        if not shard_path.is_file():
            raise FileNotFoundError(f"Missing worker output: {shard_path}")
        shard_paths.append(shard_path)
        with shard_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(json.loads(line))
    records.sort(key=lambda row: (row["source_index"], row["sample_index"]))

    records_by_source: dict[int, list[dict[str, Any]]] = {}
    for record in records:
        records_by_source.setdefault(record["source_index"], []).append(record)
    expected_sources = set(
        range(config.start_index, config.start_index + config.num_rows)
    )
    if set(records_by_source) != expected_sources:
        raise RuntimeError("Candidate source coverage differs from selected rows")
    for source_index, source_records in records_by_source.items():
        sample_indices = [record["sample_index"] for record in source_records]
        if sample_indices != list(range(config.samples_per_prompt)):
            raise RuntimeError(
                f"source_index={source_index} has unexpected sample indices "
                f"{sample_indices}"
            )

    selected_path = output_dir / "selected.jsonl"
    selected_records = []
    rank_bucket_counts: dict[str, int] = {}
    rows_without_rule_valid_hit = 0
    rows_above_rank_threshold = 0
    with selected_path.open("w", encoding="utf-8") as selected_handle:
        for source_index in sorted(records_by_source):
            source_records = records_by_source[source_index]
            valid_hits = sorted(
                (
                    record
                    for record in source_records
                    if record["rule_valid_hit"]
                ),
                key=_candidate_sort_key,
            )
            if not valid_hits:
                rows_without_rule_valid_hit += 1
                continue
            best = valid_hits[0]
            if best["target_rank"] > config.max_target_rank:
                rows_above_rank_threshold += 1
                continue
            selected_records.append(best)
            selected_handle.write(
                json.dumps(_minimal_selected(best), ensure_ascii=False) + "\n"
            )
            bucket = best["target_rank_bucket"]
            rank_bucket_counts[bucket] = rank_bucket_counts.get(bucket, 0) + 1

    checkpoints = sorted(
        {1, 2, config.samples_per_prompt}
        & set(range(1, config.samples_per_prompt + 1))
    )
    oracle_metrics = {}
    for checkpoint in checkpoints:
        best_ranks = [
            _best_target_rank(source_records[:checkpoint])
            for source_records in records_by_source.values()
        ]
        oracle_metrics[str(checkpoint)] = {
            f"hr_at_{cutoff}": sum(
                rank is not None and rank <= cutoff for rank in best_ranks
            )
            / config.num_rows
            for cutoff in (1, 5, 10, 20, 50, config.num_beams)
            if cutoff <= config.num_beams
        }

    total = len(records)
    format_valid = sum(record["format_valid"] for record in records)
    rule_valid = sum(record["rule_quality_valid"] for record in records)
    raw_hit_rows = sum(
        any(
            record["format_valid"] and record["target_rank"] is not None
            for record in source_records
        )
        for source_records in records_by_source.values()
    )
    selected_count = len(selected_records)
    summary = {
        "checkpoint": config.checkpoint,
        "dataset_repo": config.dataset_repo,
        "dataset_config": f"{config.category}_reasoning",
        "split": config.split,
        "start_index": config.start_index,
        "num_rows": config.num_rows,
        "samples_per_prompt": config.samples_per_prompt,
        "beam_width": config.num_beams,
        "max_target_rank": config.max_target_rank,
        "num_candidates": total,
        "format_valid_candidates": format_valid,
        "rule_valid_candidates": rule_valid,
        "rows_with_beam_hit": raw_hit_rows,
        "selected_rows": selected_count,
        "dropped_rows": config.num_rows - selected_count,
        "rows_without_rule_valid_hit": rows_without_rule_valid_hit,
        "rows_above_rank_threshold": rows_above_rank_threshold,
        "selection_rate": selected_count / config.num_rows,
        "selected_rank_bucket_distribution": rank_bucket_counts,
        "oracle_metrics_by_sample_count": oracle_metrics,
        "outputs": {
            "selected": str(selected_path),
        },
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    for shard_path in shard_paths:
        shard_path.unlink()
    shutil.rmtree(output_dir / ".cache", ignore_errors=True)
    return summary


def _run_distributed(
    config: WorkerConfig,
    gpu_ids: list[str],
    progress_every: int,
) -> dict[str, Any]:
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for old_output in (
        "samples.jsonl",
        "selected.jsonl",
        "summary.json",
        "accepted.jsonl",
        "rule_valid_hits.jsonl",
        "best_per_row.jsonl",
        "row_summaries.jsonl",
        "rank_filtered_candidates.jsonl",
        "rank_filtered_best.jsonl",
        "analysis_top_candidates.jsonl",
    ):
        old_path = output_dir / old_output
        if old_path.exists():
            old_path.unlink()
    for rank in range(config.world_size):
        for shard_path in (
            output_dir / f"rank_{rank:02d}.jsonl",
            output_dir / f"row_summaries_rank_{rank:02d}.jsonl",
        ):
            if shard_path.exists():
                shard_path.unlink()

    context = mp.get_context("spawn")
    progress_queue = context.Queue()
    workers = []
    for rank, gpu_id in enumerate(gpu_ids):
        process = context.Process(
            target=_worker_main,
            args=(config, rank, gpu_id, progress_queue),
            name=f"phase3-inference-rank-{rank}",
        )
        process.start()
        workers.append(process)

    generated_candidates = 0
    completed_rows = 0
    valid = 0
    next_report = progress_every
    finished_ranks = set()
    errors = []
    while len(finished_ranks) < config.world_size:
        try:
            message = progress_queue.get(timeout=1.0)
        except queue.Empty:
            crashed = [
                rank
                for rank, process in enumerate(workers)
                if rank not in finished_ranks
                and process.exitcode is not None
                and process.exitcode != 0
            ]
            if crashed:
                errors.append(f"workers exited unexpectedly: {crashed}")
                break
            continue

        kind, rank, payload = message[0], message[1], message[2:]
        if kind == "ready":
            shard_start, shard_end, device_name = payload
            print(
                f"[worker {rank}] GPU {gpu_ids[rank]} ({device_name}) ready; "
                f"rows [{shard_start}, {shard_end})",
                flush=True,
            )
        elif kind == "progress":
            progress = payload[0]
            for is_valid in progress["candidate_validity"]:
                generated_candidates += 1
                valid += int(is_valid)
            completed_rows += progress["rows_finished"]
            if completed_rows >= next_report:
                print(
                    f"[sampling] rows={completed_rows}/{config.num_rows} | "
                    f"candidates={generated_candidates} | valid={valid} | "
                    f"format_accuracy={valid / generated_candidates:.4%}",
                    flush=True,
                )
                while next_report <= completed_rows:
                    next_report += progress_every
        elif kind == "finished":
            finished_ranks.add(rank)
            if payload[0] is not None:
                errors.append(f"worker {rank} failed:\n{payload[0]}")

    if errors:
        for process in workers:
            if process.is_alive():
                process.terminate()
        for process in workers:
            process.join()
        raise RuntimeError("\n".join(errors))

    for process in workers:
        process.join()
        if process.exitcode != 0:
            raise RuntimeError(
                f"worker process {process.name} exited with {process.exitcode}"
            )

    if completed_rows and completed_rows % progress_every:
        print(
            f"[sampling] rows={completed_rows}/{config.num_rows} | "
            f"candidates={generated_candidates} | valid={valid} | "
            f"format_accuracy={valid / generated_candidates:.4%}",
            flush=True,
        )
    return _merge_minimal_outputs(config)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Phase-3 reasoning rejection sampling on eight one-GPU vLLM workers."
        )
    )
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--dataset-repo", default=HF_REPO)
    parser.add_argument("--category", choices=CATEGORIES, default="Video_Games")
    parser.add_argument("--split", default="train")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument(
        "--num-samples",
        type=int,
        default=-1,
        help="Number of dataset rows to infer; use -1 for all remaining rows.",
    )
    parser.add_argument(
        "--samples-per-prompt",
        type=int,
        default=4,
        help="Fixed number of reasoning samples generated for each history.",
    )
    parser.add_argument("--output-dir", default="./rejection_sampling_output")
    parser.add_argument("--gpus", default="0,1,2,3,4,5,6,7")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--progress-every", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-prompt-length", type=int, default=1024)
    parser.add_argument("--max-new-tokens", type=int, default=1024)
    parser.add_argument("--num-beams", type=int, default=100)
    parser.add_argument(
        "--max-target-rank",
        type=int,
        default=100,
        help="Keep a row only when its best rule-valid target rank is at most this value.",
    )
    parser.add_argument("--sid-length", type=int, default=3)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=-1)
    parser.add_argument("--min-p", type=float, default=0.0)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.8)
    parser.add_argument("--max-num-batched-tokens", type=int, default=32768)
    parser.add_argument("--max-num-seqs", type=int, default=2048)
    parser.add_argument("--enforce-eager", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    gpu_ids = [gpu.strip() for gpu in args.gpus.split(",") if gpu.strip()]
    if len(gpu_ids) != 8 or len(set(gpu_ids)) != 8:
        raise ValueError("--gpus must contain exactly eight distinct GPU IDs")
    if args.batch_size < 1:
        raise ValueError("--batch-size must be at least 1")
    if args.samples_per_prompt < 1:
        raise ValueError("--samples-per-prompt must be at least 1")
    if args.progress_every < 1:
        raise ValueError("--progress-every must be at least 1")
    if args.num_beams < 2:
        raise ValueError("--num-beams must be at least 2")
    if not 1 <= args.max_target_rank <= args.num_beams:
        raise ValueError("--max-target-rank must be in [1, --num-beams]")
    if args.sid_length != 3:
        raise ValueError("SID recommendation requires --sid-length 3")
    if args.max_num_batched_tokens < args.max_prompt_length + args.max_new_tokens:
        raise ValueError(
            "--max-num-batched-tokens must cover one full prompt and response"
        )

    checkpoint = _validate_checkpoint(args.checkpoint)
    dataset_size, num_rows = _validate_dataset_schema(
        args.dataset_repo,
        args.category,
        args.split,
        args.start_index,
        args.num_samples,
    )
    config = WorkerConfig(
        checkpoint=str(checkpoint),
        dataset_repo=args.dataset_repo,
        category=args.category,
        split=args.split,
        start_index=args.start_index,
        num_rows=num_rows,
        world_size=8,
        output_dir=str(Path(args.output_dir).expanduser().resolve()),
        batch_size=args.batch_size,
        samples_per_prompt=args.samples_per_prompt,
        max_target_rank=args.max_target_rank,
        seed=args.seed,
        max_prompt_length=args.max_prompt_length,
        max_new_tokens=args.max_new_tokens,
        num_beams=args.num_beams,
        sid_length=args.sid_length,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        min_p=args.min_p,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_num_batched_tokens=args.max_num_batched_tokens,
        max_num_seqs=args.max_num_seqs,
        enforce_eager=args.enforce_eager,
    )
    print(
        f"[setup] dataset={args.category}_reasoning/{args.split} "
        f"rows={num_rows}/{dataset_size} start={args.start_index} workers=8 "
        f"samples={args.samples_per_prompt} beam={args.num_beams} "
        f"max_target_rank={args.max_target_rank}",
        flush=True,
    )
    summary = _run_distributed(config, gpu_ids, args.progress_every)
    print(
        f"[done] candidates={summary['num_candidates']} "
        f"selected={summary['selected_rows']} "
        f"selection_rate={summary['selection_rate']:.4%}",
        flush=True,
    )
    print(f"[done] outputs={config.output_dir}", flush=True)


if __name__ == "__main__":
    main()