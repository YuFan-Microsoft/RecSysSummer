"""Two-stage semantic search: embedding recall + cross-encoder rerank.

Stage 1 (recall): embed the query with Qwen3-Embedding-8B and take the
``recall_k`` papers with the highest cosine similarity.

Stage 2 (rerank): score each recalled paper against the query with
Qwen3-Reranker-8B and keep the top ``rerank_k``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from common import load_config
from embedder import Qwen3Embedder
from reranker import Qwen3Reranker


@dataclass
class SearchResult:
    rank: int
    paper_id: str
    title: str
    company: str
    arxiv_url: str
    content: str
    recall_score: float
    rerank_score: float


class SearchEngine:
    """Loads the prebuilt index and both models, then serves queries."""

    def __init__(self, config_path: str | None = None) -> None:
        self.cfg = load_config(config_path)
        index_dir = Path(self.cfg["index_dir"]).expanduser()

        emb_path = index_dir / "embeddings.npy"
        meta_path = index_dir / "metadata.json"
        if not emb_path.exists() or not meta_path.exists():
            raise FileNotFoundError(
                f"Index not found in {index_dir}. Run `python build_index.py` first."
            )

        self.embeddings = np.load(emb_path).astype(np.float32)  # (N, dim), normalised
        with open(meta_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        print(f"[search] loaded index: {self.embeddings.shape[0]} papers")

        print(f"[search] loading embedding model: {self.cfg['embedding_model_path']}")
        self.embedder = Qwen3Embedder(
            model_path=self.cfg["embedding_model_path"],
            device=self.cfg["embedding_device"],
            dtype=self.cfg["dtype"],
            max_length=self.cfg["embedding_max_length"],
            use_flash_attention=self.cfg["use_flash_attention"],
        )

        print(f"[search] loading reranker model: {self.cfg['reranker_model_path']}")
        self.reranker = Qwen3Reranker(
            model_path=self.cfg["reranker_model_path"],
            device=self.cfg["reranker_device"],
            dtype=self.cfg["dtype"],
            max_length=self.cfg["reranker_max_length"],
            use_flash_attention=self.cfg["use_flash_attention"],
        )
        print("[search] ready.")

    def search(
        self,
        query: str,
        rerank_k: int | None = None,
        recall_k: int | None = None,
    ) -> list[SearchResult]:
        query = (query or "").strip()
        if not query:
            return []

        rerank_k = rerank_k or self.cfg["rerank_k"]
        # Recall pool is twice the requested top-K, capped at recall_cap (100).
        if recall_k is None:
            recall_k = min(2 * rerank_k, int(self.cfg.get("recall_cap", 100)))
        recall_k = min(recall_k, self.embeddings.shape[0])
        rerank_k = min(rerank_k, recall_k)

        # --- Stage 1: embedding recall ---
        q_emb = self.embedder.encode_queries(
            [query], task=self.cfg["query_instruction"]
        ).numpy()[0]
        sims = self.embeddings @ q_emb  # cosine (both L2-normalised)
        top_idx = np.argpartition(-sims, recall_k - 1)[:recall_k]
        top_idx = top_idx[np.argsort(-sims[top_idx])]

        candidates = [self.metadata[i] for i in top_idx]
        recall_scores = [float(sims[i]) for i in top_idx]

        # --- Stage 2: rerank ---
        docs = [self._doc_for_rerank(c) for c in candidates]
        rerank_scores = self.reranker.score(
            query, docs, instruction=self.cfg["reranker_instruction"]
        )

        order = np.argsort(-np.asarray(rerank_scores))[:rerank_k]
        results: list[SearchResult] = []
        for rank, j in enumerate(order, start=1):
            c = candidates[j]
            results.append(
                SearchResult(
                    rank=rank,
                    paper_id=c["paper_id"],
                    title=c["title"],
                    company=c["company"],
                    arxiv_url=c["arxiv_url"],
                    content=c["content"],
                    recall_score=recall_scores[j],
                    rerank_score=float(rerank_scores[j]),
                )
            )
        return results

    @staticmethod
    def _doc_for_rerank(meta: dict) -> str:
        """Compact text given to the reranker (title + body)."""
        return f"{meta['title']}\n\n{meta['content']}".strip()


if __name__ == "__main__":
    import sys

    engine = SearchEngine()
    q = " ".join(sys.argv[1:]) or "sequential recommendation with large language models"
    for r in engine.search(q):
        print(f"#{r.rank:2d} [{r.company}] rerank={r.rerank_score:.3f} "
              f"recall={r.recall_score:.3f}  {r.title}")
