import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

_cpu_threads = _os.environ.get("SIDR_EVAL_CPU_THREADS", "1")
for _thread_var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    _os.environ[_thread_var] = _cpu_threads

import json
import os
import random

import fire
import numpy as np
from tqdm import tqdm
from vllm import LLM

import hf_data
from data_Qwen3 import SidNextItemEvalDataset
from verl.workers.rollout.sid_constrained_decoding import (
    build_sid_token_trie,
    vllm_constrained_beam_search,
)


CATEGORY_NAMES = {
    "Industrial_and_Scientific": "industrial and scientific items",
    "Office_Products": "office products",
    "Toys_and_Games": "toys and games",
    "Sports": "sports and outdoors",
    "Books": "books",
    "Video_Games": "video games",
}


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)


def batched(values, batch_size):
    for start in range(0, len(values), batch_size):
        yield values[start : start + batch_size]


def main(
    base_model: str = "./output_dir/7Task-End2End_Qwen3_Games/final_checkpoint",
    train_file: str = "./data/Amazon_Games/train/Video_Games_5_2016-10-2018-11.csv",
    info_file: str = "./data/Amazon_Games/info/Video_Games_5_2016-10-2018-11.txt",
    category: str = "Video_Games",
    test_data_path: str = "./data/Amazon_Games/test/Video_Games_5_2016-10-2018-11_for_test.csv",
    result_json_data: str = "./temp/test_results_Qwen3.json",
    batch_size: int = 96,
    K: int = 0,
    seed: int = 42,
    length_penalty: float = 0.0,
    num_beams: int = 10,
    padding_side: str = "left",
    max_prompt_length: int = 1024,
    sid_length: int = 3,
    gpu_memory_utilization: float = 0.8,
    max_num_batched_tokens: int = 32768,
    max_num_seqs: int = 4096,
    enforce_eager: bool = False,
):
    """Evaluate no-thinking recommendations from three SID-token scores only."""
    del train_file, info_file, K, padding_side
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    if num_beams < 2:
        raise ValueError("num_beams must be at least 2")
    if sid_length != 3:
        raise ValueError("SID recommendation metrics require exactly three semantic tokens")
    if length_penalty != 0.0:
        raise ValueError("fixed-depth SID beam search requires length_penalty=0.0")
    if max_num_batched_tokens < max_prompt_length + sid_length:
        raise ValueError("max_num_batched_tokens must cover at least one full sequence")

    set_seed(seed)
    llm = LLM(
        model=base_model,
        max_model_len=max_prompt_length + sid_length,
        max_num_batched_tokens=max_num_batched_tokens,
        max_num_seqs=max_num_seqs,
        logprobs_mode="processed_logprobs",
        dtype="bfloat16",
        gpu_memory_utilization=gpu_memory_utilization,
        tensor_parallel_size=1,
        seed=seed,
        enforce_eager=enforce_eager,
        enable_chunked_prefill=True,
        enable_prefix_caching=True,
    )
    tokenizer = llm.get_tokenizer()
    sid_token_trie = build_sid_token_trie(
        tokenizer,
        hf_data.load_sid_indices(category).values(),
        depth=sid_length,
    )

    val_dataset = SidNextItemEvalDataset(
        train_file=test_data_path,
        tokenizer=tokenizer,
        max_len=max_prompt_length,
        category=CATEGORY_NAMES.get(category, "items"),
        test=True,
        seed=seed,
    )
    encodings = [val_dataset[index] for index in range(len(val_dataset))]
    test_data = val_dataset.get_all()
    if len(encodings) != len(test_data):
        raise RuntimeError("Evaluation prompts and result rows have different lengths")

    overlong_prompts = [
        len(encoding["input_ids"])
        for encoding in encodings
        if len(encoding["input_ids"]) > max_prompt_length
    ]
    if overlong_prompts:
        raise ValueError(
            f"Found {len(overlong_prompts)} prompts longer than the training limit "
            f"of {max_prompt_length} tokens (maximum: {max(overlong_prompts)})"
        )

    predictions = []
    encoding_batches = list(batched(encodings, batch_size))
    for encoding_batch in tqdm(encoding_batches, desc="Generating constrained SID beams"):
        prompt_ids = [list(encoding["input_ids"]) for encoding in encoding_batch]
        sid_beams = vllm_constrained_beam_search(
            llm,
            prompts_ids=prompt_ids,
            sid_token_trie=sid_token_trie,
            depth=sid_length,
            beam_width=num_beams,
        )
        short_beams = [len(sample_beams) for sample_beams in sid_beams if len(sample_beams) != num_beams]
        if short_beams:
            raise RuntimeError(
                "Constrained SID beam search did not return the requested beam width "
                f"of {num_beams} (minimum returned: {min(short_beams)}). Ensure the "
                "vLLM engine uses logprobs_mode='processed_logprobs'."
            )
        predictions.extend(
            [
                tokenizer.decode(sid_ids, skip_special_tokens=False)
                for sid_ids in sample_beams
            ]
            for sample_beams in sid_beams
        )

    if len(predictions) != len(test_data):
        raise RuntimeError("Evaluation generated an inconsistent number of result rows")
    for sample, prediction in zip(test_data, predictions):
        sample["predict"] = prediction
        sample.pop("dedup", None)

    result_dir = os.path.dirname(result_json_data)
    if result_dir:
        os.makedirs(result_dir, exist_ok=True)
    with open(result_json_data, "w", encoding="utf-8") as handle:
        json.dump(test_data, handle, indent=4)


if __name__ == "__main__":
    fire.Fire(main)