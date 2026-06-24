"""Qwen3-Reranker wrapper (cross-encoder yes/no relevance scoring).

Implements the official Transformers usage from the model card: the model is a
causal LM that answers "yes"/"no" to whether a document satisfies the query; the
relevance score is ``softmax(yes, no)`` for the "yes" token at the last position.
"""

from __future__ import annotations

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

_DTYPES = {
    "float32": torch.float32,
    "float16": torch.float16,
    "bfloat16": torch.bfloat16,
}

_PREFIX = (
    "<|im_start|>system\nJudge whether the Document meets the requirements based "
    'on the Query and the Instruct provided. Note that the answer can only be "yes" '
    'or "no".<|im_end|>\n<|im_start|>user\n'
)
_SUFFIX = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


class Qwen3Reranker:
    """Cross-encoder reranker built on Qwen3-Reranker."""

    def __init__(
        self,
        model_path: str,
        device: str = "cuda:0",
        dtype: str = "bfloat16",
        max_length: int = 512,
        use_flash_attention: bool = False,
    ) -> None:
        self.device = device
        self.max_length = max_length
        torch_dtype = _DTYPES.get(dtype, torch.bfloat16)

        self.tokenizer = AutoTokenizer.from_pretrained(model_path, padding_side="left")
        model_kwargs: dict = {"torch_dtype": torch_dtype}
        if use_flash_attention:
            model_kwargs["attn_implementation"] = "flash_attention_2"
        self.model = AutoModelForCausalLM.from_pretrained(model_path, **model_kwargs)
        self.model.to(device)
        self.model.eval()

        self.token_true_id = self.tokenizer.convert_tokens_to_ids("yes")
        self.token_false_id = self.tokenizer.convert_tokens_to_ids("no")
        self.prefix_tokens = self.tokenizer.encode(_PREFIX, add_special_tokens=False)
        self.suffix_tokens = self.tokenizer.encode(_SUFFIX, add_special_tokens=False)

    @staticmethod
    def _format_instruction(instruction: str, query: str, doc: str) -> str:
        return f"<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}"

    def _process_inputs(self, pairs: list[str]):
        budget = self.max_length - len(self.prefix_tokens) - len(self.suffix_tokens)
        inputs = self.tokenizer(
            pairs,
            padding=False,
            truncation="longest_first",
            return_attention_mask=False,
            max_length=budget,
        )
        for i, ele in enumerate(inputs["input_ids"]):
            inputs["input_ids"][i] = self.prefix_tokens + ele + self.suffix_tokens
        inputs = self.tokenizer.pad(
            inputs, padding=True, return_tensors="pt", max_length=self.max_length
        )
        return {k: v.to(self.device) for k, v in inputs.items()}

    @torch.no_grad()
    def _compute_logits(self, inputs) -> list[float]:
        batch_scores = self.model(**inputs).logits[:, -1, :]
        true_vector = batch_scores[:, self.token_true_id]
        false_vector = batch_scores[:, self.token_false_id]
        batch_scores = torch.stack([false_vector, true_vector], dim=1)
        batch_scores = torch.nn.functional.log_softmax(batch_scores, dim=1)
        return batch_scores[:, 1].exp().float().tolist()

    @torch.no_grad()
    def score(
        self,
        query: str,
        documents: list[str],
        instruction: str,
        batch_size: int = 16,
    ) -> list[float]:
        """Return a relevance score in ``[0, 1]`` for each document."""
        scores: list[float] = []
        for start in range(0, len(documents), batch_size):
            batch_docs = documents[start : start + batch_size]
            pairs = [
                self._format_instruction(instruction, query, doc) for doc in batch_docs
            ]
            inputs = self._process_inputs(pairs)
            scores.extend(self._compute_logits(inputs))
        return scores
