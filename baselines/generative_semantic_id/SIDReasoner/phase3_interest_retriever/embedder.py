from __future__ import annotations

from typing import Any, Optional


DEFAULT_MODEL = "/yufan/open_source_models/Embedding_Model/Qwen3-Embedding-0.6B"
DEFAULT_DOMAIN = "Video_Games"
DOMAIN_QUERY_INSTRUCTIONS = {
    "Video_Games": "Retrieve relevant Video Games products.",
    "Office_Products": "Retrieve relevant Office products.",
    "Industrial_and_Scientific": "Retrieve relevant Industrial and Scientific products.",
}
SUPPORTED_DOMAINS = tuple(DOMAIN_QUERY_INSTRUCTIONS)
DEFAULT_QUERY_INSTRUCTION = DOMAIN_QUERY_INSTRUCTIONS[DEFAULT_DOMAIN]
DEFAULT_DOCUMENT_MAX_LENGTH = 1024
DEFAULT_QUERY_MAX_LENGTH = 512


def query_instruction_for_domain(domain: str) -> str:
    try:
        return DOMAIN_QUERY_INSTRUCTIONS[domain]
    except KeyError as error:
        raise ValueError(f"unsupported retrieval domain: {domain}") from error


class Qwen3Embedder:
    """Qwen3-Embedding wrapper with document/query asymmetric encoding."""

    def __init__(
        self,
        model_name_or_path: str = DEFAULT_MODEL,
        device: str = "cuda:0",
        dtype: str = "float16",
        max_length: int = DEFAULT_QUERY_MAX_LENGTH,
        use_flash_attention: bool = False,
    ) -> None:
        import torch
        from transformers import AutoModel, AutoTokenizer

        dtypes = {
            "float32": torch.float32,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }
        if dtype not in dtypes:
            raise ValueError(f"unsupported dtype: {dtype}")

        self._torch = torch
        self.device = device
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            padding_side="left",
        )
        model_kwargs: dict[str, Any] = {"torch_dtype": dtypes[dtype]}
        if use_flash_attention:
            model_kwargs["attn_implementation"] = "flash_attention_2"
        self.model = AutoModel.from_pretrained(model_name_or_path, **model_kwargs)
        self.model.to(device)
        self.model.eval()

    def _last_token_pool(self, last_hidden_states: Any, attention_mask: Any) -> Any:
        if attention_mask[:, -1].sum() == attention_mask.shape[0]:
            return last_hidden_states[:, -1]
        sequence_lengths = attention_mask.sum(dim=1) - 1
        batch_size = last_hidden_states.shape[0]
        return last_hidden_states[
            self._torch.arange(batch_size, device=last_hidden_states.device),
            sequence_lengths,
        ]

    def _batch_indices(
        self,
        texts: list[str],
        batch_size: int,
        max_batch_tokens: Optional[int],
    ) -> list[list[int]]:
        if max_batch_tokens is None:
            return [
                list(range(start, min(start + batch_size, len(texts))))
                for start in range(0, len(texts), batch_size)
            ]

        tokenized = self.tokenizer(
            texts,
            padding=False,
            truncation=True,
            max_length=self.max_length,
            return_length=True,
        )
        lengths = [int(length) for length in tokenized["length"]]
        sorted_indices = sorted(range(len(texts)), key=lengths.__getitem__)
        batches: list[list[int]] = []
        current: list[int] = []
        for index in sorted_indices:
            next_size = len(current) + 1
            padded_tokens = next_size * lengths[index]
            if current and (next_size > batch_size or padded_tokens > max_batch_tokens):
                batches.append(current)
                current = []
            current.append(index)
        if current:
            batches.append(current)
        return batches

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
        max_batch_tokens: Optional[int] = None,
    ) -> Any:
        if not texts:
            raise ValueError("texts must not be empty")
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        if max_batch_tokens is not None and max_batch_tokens < 1:
            raise ValueError("max_batch_tokens must be positive")
        outputs = []
        output_indices = []
        with self._torch.no_grad():
            for indices in self._batch_indices(texts, batch_size, max_batch_tokens):
                inputs = self.tokenizer(
                    [texts[index] for index in indices],
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt",
                ).to(self.device)
                model_output = self.model(**inputs)
                embeddings = self._last_token_pool(
                    model_output.last_hidden_state,
                    inputs["attention_mask"],
                )
                embeddings = self._torch.nn.functional.normalize(embeddings, p=2, dim=1)
                outputs.append(embeddings.float().cpu().numpy())
                output_indices.extend(indices)

        import numpy as np

        concatenated = np.concatenate(outputs, axis=0)
        restored = np.empty_like(concatenated)
        restored[np.asarray(output_indices)] = concatenated
        return restored

    def encode_documents(
        self,
        documents: list[str],
        batch_size: int = 32,
        max_batch_tokens: Optional[int] = None,
    ) -> Any:
        return self.encode(
            documents,
            batch_size=batch_size,
            max_batch_tokens=max_batch_tokens,
        )

    def encode_queries(
        self,
        queries: list[str],
        instruction: str = DEFAULT_QUERY_INSTRUCTION,
        batch_size: int = 32,
    ) -> Any:
        prompts = [f"Instruct: {instruction}\nQuery: {query}" for query in queries]
        return self.encode(prompts, batch_size=batch_size)
