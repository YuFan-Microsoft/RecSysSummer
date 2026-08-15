"""Qwen3-Embedding-8B wrapper.

Implements the official Transformers usage from the model card: last-token
pooling, L2 normalisation, and an ``Instruct: ... \\nQuery: ...`` prompt for
queries (documents are embedded without an instruction).
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoModel, AutoTokenizer

_DTYPES = {
    "float32": torch.float32,
    "float16": torch.float16,
    "bfloat16": torch.bfloat16,
}


def _last_token_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    """Pool the hidden state of the last non-padding token (handles left padding)."""
    left_padding = attention_mask[:, -1].sum() == attention_mask.shape[0]
    if left_padding:
        return last_hidden_states[:, -1]
    sequence_lengths = attention_mask.sum(dim=1) - 1
    batch_size = last_hidden_states.shape[0]
    return last_hidden_states[
        torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths
    ]


class Qwen3Embedder:
    """Embedding model for both indexing (documents) and querying."""

    def __init__(
        self,
        model_path: str,
        device: str = "cuda:0",
        dtype: str = "bfloat16",
        max_length: int = 8192,
        use_flash_attention: bool = False,
    ) -> None:
        self.device = device
        self.max_length = max_length
        torch_dtype = _DTYPES.get(dtype, torch.bfloat16)

        self.tokenizer = AutoTokenizer.from_pretrained(model_path, padding_side="left")
        model_kwargs: dict = {"torch_dtype": torch_dtype}
        if use_flash_attention:
            model_kwargs["attn_implementation"] = "flash_attention_2"
        self.model = AutoModel.from_pretrained(model_path, **model_kwargs)
        self.model.to(device)
        self.model.eval()

    @staticmethod
    def detailed_instruct(task_description: str, query: str) -> str:
        return f"Instruct: {task_description}\nQuery:{query}"

    @torch.no_grad()
    def encode(
        self,
        texts: list[str],
        batch_size: int = 8,
        show_progress: bool = False,
    ) -> Tensor:
        """Return L2-normalised embeddings of shape ``(len(texts), dim)`` on CPU."""
        all_embeddings: list[Tensor] = []
        iterator = range(0, len(texts), batch_size)
        if show_progress:
            try:
                from tqdm import tqdm

                iterator = tqdm(iterator, desc="Embedding", unit="batch")
            except ImportError:
                pass

        for start in iterator:
            batch = texts[start : start + batch_size]
            inputs = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            ).to(self.device)
            outputs = self.model(**inputs)
            emb = _last_token_pool(outputs.last_hidden_state, inputs["attention_mask"])
            emb = F.normalize(emb, p=2, dim=1)
            all_embeddings.append(emb.float().cpu())

        return torch.cat(all_embeddings, dim=0)

    def encode_queries(self, queries: list[str], task: str, batch_size: int = 8) -> Tensor:
        """Embed queries with the task instruction prepended."""
        prompts = [self.detailed_instruct(task, q) for q in queries]
        return self.encode(prompts, batch_size=batch_size)
