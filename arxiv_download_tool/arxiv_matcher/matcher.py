"""Title -> arXiv id matcher: embedding recall + rerank + edit-distance/author adjudication.

Pipeline for a request ``(title, author)``:

1. Recall   : embed the (normalized) title with Qwen3-Embedding and take the
              ``recall_k`` arXiv titles with the highest cosine similarity.
2. Rerank   : score each candidate against the query title with Qwen3-Reranker
              and keep the single best.
3. Adjudicate: accept the top-1 only when the normalized-title edit-distance
               similarity >= ``title_sim_threshold`` AND the first-author
               surname agrees. On acceptance, return the arXiv id and url.

Usage (CLI):
    python matcher.py "Optimal Baseline Corrections for Off-Policy Contextual Bandits" "Shashank Gupta"
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from common import (
    load_config,
    normalize_title,
    surnames_match,
    title_similarity,
)
from embedder import Qwen3Embedder
from reranker import Qwen3Reranker


@dataclass
class MatchResult:
    matched: bool
    arxiv_id: str | None = None
    arxiv_url: str | None = None
    matched_title: str | None = None     # normalized title of the chosen arXiv paper
    matched_surname: str | None = None
    recall_score: float = 0.0
    rerank_score: float = 0.0
    title_sim: float = 0.0
    author_ok: bool = False
    candidates: list | None = None       # ranked [(title, surname, arxiv_id, recall, rerank)]


class ArxivTitleMatcher:
    """Loads the prebuilt title index and both models, then matches titles."""

    def __init__(self, config_path: str | None = None) -> None:
        self.cfg = load_config(config_path)
        index_dir = Path(self.cfg["index_dir"]).expanduser()

        emb_path = index_dir / "embeddings.npy"
        meta_path = index_dir / "metadata.jsonl"
        if not emb_path.exists() or not meta_path.exists():
            raise FileNotFoundError(
                f"Index not found in {index_dir}. Run `python build_index.py` first."
            )

        self.embeddings = np.load(emb_path).astype(np.float32)  # (N, dim), normalised
        self.metadata: list[dict] = []
        with open(meta_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.metadata.append(json.loads(line))
        print(f"[match] loaded index: {self.embeddings.shape[0]} titles")

        print(f"[match] loading embedding model: {self.cfg['embedding_model_path']}")
        self.embedder = Qwen3Embedder(
            model_path=self.cfg["embedding_model_path"],
            device=self.cfg["embedding_device"],
            dtype=self.cfg["dtype"],
            max_length=self.cfg["embedding_max_length"],
            use_flash_attention=self.cfg["use_flash_attention"],
        )

        print(f"[match] loading reranker model: {self.cfg['reranker_model_path']}")
        self.reranker = Qwen3Reranker(
            model_path=self.cfg["reranker_model_path"],
            device=self.cfg["reranker_device"],
            dtype=self.cfg["dtype"],
            max_length=self.cfg["reranker_max_length"],
            use_flash_attention=self.cfg["use_flash_attention"],
        )
        print("[match] ready.")

    def _recall(self, norm_title: str, recall_k: int) -> tuple[list[dict], list[float]]:
        """Top-``recall_k`` arXiv titles by cosine similarity to the query title."""
        q_emb = self.embedder.encode_queries(
            [norm_title], task=self.cfg["query_instruction"]
        ).numpy()[0]
        sims = self.embeddings @ q_emb
        k = min(recall_k, self.embeddings.shape[0])
        top_idx = np.argpartition(-sims, k - 1)[:k]
        top_idx = top_idx[np.argsort(-sims[top_idx])]
        return [self.metadata[i] for i in top_idx], [float(sims[i]) for i in top_idx]

    def match(
        self,
        title: str,
        author: str = "",
        recall_k: int | None = None,
    ) -> MatchResult:
        """Match a paper title (+ first author) to an arXiv id, or report no match."""
        norm_q = normalize_title(title)
        if not norm_q:
            return MatchResult(matched=False)

        recall_k = recall_k or int(self.cfg["recall_k"])

        # --- Stage 1: embedding recall ---
        candidates, recall_scores = self._recall(norm_q, recall_k)

        # --- Stage 2: rerank to top-1 ---
        docs = [c["title"] for c in candidates]
        rerank_scores = self.reranker.score(
            norm_q, docs, instruction=self.cfg["reranker_instruction"]
        )
        best = int(np.argmax(rerank_scores))
        cand = candidates[best]

        # --- Stage 3: adjudicate with edit distance + first author ---
        tsim = title_similarity(norm_q, cand["title"])
        author_ok = surnames_match(author, cand.get("surname", ""))
        accept = tsim >= float(self.cfg["title_sim_threshold"])
        if self.cfg.get("require_author_match", True):
            accept = accept and author_ok

        order = sorted(range(len(candidates)), key=lambda i: -rerank_scores[i])
        ranked = [
            {
                "title": candidates[i]["title"],
                "surname": candidates[i].get("surname", ""),
                "arxiv_id": candidates[i]["arxiv_id"],
                "recall": recall_scores[i],
                "rerank": float(rerank_scores[i]),
            }
            for i in order
        ]

        return MatchResult(
            matched=accept,
            arxiv_id=cand["arxiv_id"] if accept else None,
            arxiv_url=f"https://arxiv.org/abs/{cand['arxiv_id']}" if accept else None,
            matched_title=cand["title"],
            matched_surname=cand.get("surname", ""),
            recall_score=recall_scores[best],
            rerank_score=float(rerank_scores[best]),
            title_sim=tsim,
            author_ok=author_ok,
            candidates=ranked,
        )


if __name__ == "__main__":
    import sys

    title = sys.argv[1] if len(sys.argv) > 1 else \
        "Optimal Baseline Corrections for Off-Policy Contextual Bandits"
    author = sys.argv[2] if len(sys.argv) > 2 else ""

    matcher = ArxivTitleMatcher()
    r = matcher.match(title, author)
    if r.matched:
        print(f"MATCH  {r.arxiv_url}")
    else:
        print("NO MATCH")
    print(f"  rerank={r.rerank_score:.3f} recall={r.recall_score:.3f} "
          f"title_sim={r.title_sim:.3f} author_ok={r.author_ok}")
    print(f"  candidate_title: {r.matched_title}")
