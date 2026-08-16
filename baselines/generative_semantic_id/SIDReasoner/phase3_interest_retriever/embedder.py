from __future__ import annotations

from typing import Any


DEFAULT_MODEL = "/yufan/open_source_models/Embedding_Model/Qwen3-Embedding-0.6B"
DEFAULT_QUERY_INSTRUCTION = (
    "Given a future shopping interest, retrieve products that satisfy the interest."
)


class Qwen3Embedder:
    """Qwen3-Embedding wrapper with document/query asymmetric encoding."""

    def __init__(
        self,
        model_name_or_path: str = DEFAULT_MODEL,
        device: str = "cuda:0",
        dtype: str = "bfloat16",
        max_length: int = 512,
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

    def encode(self, texts: list[str], batch_size: int = 32) -> Any:
        if not texts:
            raise ValueError("texts must not be empty")
        outputs = []
        with self._torch.no_grad():
            for start in range(0, len(texts), batch_size):
                inputs = self.tokenizer(
                    texts[start : start + batch_size],
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

        import numpy as np

        return np.concatenate(outputs, axis=0)

    def encode_documents(self, documents: list[str], batch_size: int = 32) -> Any:
        return self.encode(documents, batch_size=batch_size)

    def encode_queries(
        self,
        queries: list[str],
        instruction: str = DEFAULT_QUERY_INSTRUCTION,
        batch_size: int = 32,
    ) -> Any:
        prompts = [f"Instruct: {instruction}\nQuery:{query}" for query in queries]
        return self.encode(prompts, batch_size=batch_size)