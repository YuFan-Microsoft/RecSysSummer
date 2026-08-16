from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from collections import defaultdict

import numpy as np


class InterestIndex:
    def __init__(self, index_dir: str | Path) -> None:
        self.index_dir = Path(index_dir)
        with (self.index_dir / "manifest.json").open("r", encoding="utf-8") as file:
            self.manifest = json.load(file)
        with (self.index_dir / "metadata.json").open("r", encoding="utf-8") as file:
            self.metadata: list[dict[str, Any]] = json.load(file)
        self.embeddings = np.load(self.index_dir / "embeddings.npy", mmap_mode="r")

        if self.embeddings.ndim != 2:
            raise ValueError("embeddings.npy must be a two-dimensional matrix")
        if len(self.metadata) != self.embeddings.shape[0]:
            raise ValueError("metadata and embedding row counts do not match")
        if self.manifest.get("item_count") != len(self.metadata):
            raise ValueError("manifest item_count does not match the index")
        if self.manifest.get("embedding_dim") != self.embeddings.shape[1]:
            raise ValueError("manifest embedding_dim does not match the index")
        if not self.metadata:
            raise ValueError("index must contain at least one item")

        self.sid_to_rows: dict[str, list[int]] = defaultdict(list)
        for row, item in enumerate(self.metadata):
            self.sid_to_rows[item["sid"]].append(row)

    @property
    def model_name_or_path(self) -> str:
        return str(self.manifest["model_name_or_path"])

    @property
    def query_instruction(self) -> str:
        return str(self.manifest["query_instruction"])

    def search(self, query_embeddings: np.ndarray, top_k: int) -> list[list[dict[str, Any]]]:
        queries = np.asarray(query_embeddings, dtype=np.float32)
        if queries.ndim != 2 or queries.shape[1] != self.embeddings.shape[1]:
            raise ValueError(
                f"expected query embeddings with shape (N, {self.embeddings.shape[1]})"
            )
        if top_k < 1:
            raise ValueError("top_k must be positive")

        result_count = min(top_k, len(self.metadata))
        scores = queries @ self.embeddings.T
        unordered = np.argpartition(scores, -result_count, axis=1)[:, -result_count:]
        unordered_scores = np.take_along_axis(scores, unordered, axis=1)
        order = np.argsort(-unordered_scores, axis=1)
        ranked_rows = np.take_along_axis(unordered, order, axis=1)

        results = []
        for query_index, rows in enumerate(ranked_rows):
            items = []
            for rank, row in enumerate(rows.tolist(), start=1):
                item = self.metadata[row]
                items.append(
                    {
                        "item_id": item.get("item_id"),
                        "sid": item["sid"],
                        "title": item["title"],
                        "score": float(scores[query_index, row]),
                        "rank": rank,
                    }
                )
            results.append(items)
        return results