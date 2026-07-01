"""Two-stage arXiv search with domain / year filters and relevance/citation sort.

Pipeline for one query:

    1. Pick the shard for the chosen ``domain`` (single-select).
    2. Keep only papers whose ``year`` is in the chosen ``years`` (multi-select;
       empty = all years).
    3. Recall: embed the query with Qwen3-Embedding-8B and take the ``recall_k``
       papers with the highest cosine similarity (within the year filter).
    4. Rerank: score each recalled paper against the query with
       Qwen3-Reranker-8B and keep the top ``rerank_k`` most relevant.
    5. Sort the final ``rerank_k`` papers either by relevance (rerank score) or
       by citation count, depending on ``sort_by``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

from common import ArxivPaper, load_config
from embedder import Qwen3Embedder
from reranker import Qwen3Reranker

# Accepted values for the ``sort_by`` argument.
SORT_RELEVANCE = "relevance"
SORT_CITATION = "citation"


@dataclass
class SearchResult:
    rank: int
    arxiv_id: str
    title: str
    abstract: str
    authors: str
    domain: str
    year: int
    publication_date: str
    citation_count: int
    influential_citation_count: int
    arxiv_url: str
    recall_score: float
    rerank_score: float

    def to_dict(self) -> dict:
        return asdict(self)


class _DomainShard:
    """One domain's in-memory index: embeddings + parallel metadata + year array."""

    def __init__(self, embeddings: np.ndarray, metadata: list[dict]) -> None:
        self.embeddings = embeddings                     # (N, dim) float32, normalised
        self.metadata = metadata                         # list of paper dicts, len N
        self.years = np.array(                           # (N,) int, for fast filtering
            [int(m.get("year") or 0) for m in metadata], dtype=np.int32
        )


class SearchEngine:
    """Loads the prebuilt shards and both models, then serves filtered queries."""

    def __init__(self, config_path: str | None = None) -> None:
        self.cfg = load_config(config_path)
        self.index_dir = Path(self.cfg["index_dir"]).expanduser()
        self._shards: dict[str, _DomainShard] = {}  # domain -> shard (lazy cache)

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

    # ------------------------------------------------------------------ shards
    def _load_shard(self, domain: str) -> _DomainShard:
        """Load (and cache) one domain's embeddings + metadata from disk."""
        if domain in self._shards:
            return self._shards[domain]

        shard_dir = self.index_dir / domain
        emb_path = shard_dir / "embeddings.npy"
        meta_path = shard_dir / "metadata.json"
        if not emb_path.exists() or not meta_path.exists():
            raise FileNotFoundError(
                f"No index for domain {domain!r} in {shard_dir}. "
                f"Run `python build_index.py --domain {domain}` first."
            )

        embeddings = np.load(emb_path).astype(np.float32)
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        print(f"[search] loaded shard {domain}: {embeddings.shape[0]} papers")
        shard = _DomainShard(embeddings, metadata)
        self._shards[domain] = shard
        return shard

    # ------------------------------------------------------------------ search
    def search(
        self,
        query: str,
        domain: str,
        years: list[int] | None = None,
        sort_by: str = SORT_RELEVANCE,
        rerank_k: int | None = None,
        recall_k: int | None = None,
    ) -> list[SearchResult]:
        query = (query or "").strip()
        if not query:
            return []
        if domain not in self.cfg["domains"]:
            raise ValueError(f"Unknown domain {domain!r}. Choose one of {self.cfg['domains']}")

        rerank_k = int(rerank_k or self.cfg["rerank_k"])
        recall_k = int(recall_k or self.cfg["recall_k"])
        recall_k = max(recall_k, rerank_k)

        shard = self._load_shard(domain)

        # --- Year filter: which rows are eligible? ---
        wanted_years = {int(y) for y in years} if years else None
        if wanted_years:
            mask = np.isin(shard.years, list(wanted_years))
            eligible = np.nonzero(mask)[0]
            if eligible.size == 0:
                return []
        else:
            eligible = None  # all rows eligible

        # --- Stage 1: embedding recall (restricted to eligible rows) ---
        q_emb = self.embedder.encode_queries(
            [query], task=self.cfg["query_instruction"]
        ).numpy()[0]

        if eligible is None:
            sims = shard.embeddings @ q_emb
            pool = min(recall_k, sims.shape[0])
            top_local = np.argpartition(-sims, pool - 1)[:pool]
            top_local = top_local[np.argsort(-sims[top_local])]
            cand_idx = top_local
            cand_scores = sims[top_local]
        else:
            sims = shard.embeddings[eligible] @ q_emb
            pool = min(recall_k, sims.shape[0])
            top_local = np.argpartition(-sims, pool - 1)[:pool]
            top_local = top_local[np.argsort(-sims[top_local])]
            cand_idx = eligible[top_local]
            cand_scores = sims[top_local]

        candidates = [shard.metadata[i] for i in cand_idx]
        recall_scores = [float(s) for s in cand_scores]

        # --- Stage 2: rerank the recalled pool ---
        docs = [self._doc_for_rerank(c) for c in candidates]
        rerank_scores = self.reranker.score(
            query, docs, instruction=self.cfg["reranker_instruction"]
        )

        # Keep the top rerank_k most relevant papers (this is the result set).
        top_order = np.argsort(-np.asarray(rerank_scores))[:rerank_k]

        # --- Final ordering: by relevance, or by citation count ---
        if sort_by == SORT_CITATION:
            top_order = sorted(
                top_order,
                key=lambda j: int(candidates[j].get("citation_count") or 0),
                reverse=True,
            )
        # else: keep the relevance order from the reranker.

        results: list[SearchResult] = []
        for rank, j in enumerate(top_order, start=1):
            c = candidates[j]
            paper = ArxivPaper(**c) if not isinstance(c, ArxivPaper) else c
            results.append(
                SearchResult(
                    rank=rank,
                    arxiv_id=c["arxiv_id"],
                    title=c["title"],
                    abstract=c.get("abstract", ""),
                    authors=c.get("authors", ""),
                    domain=c.get("domain", domain),
                    year=int(c.get("year") or 0),
                    publication_date=c.get("publication_date", ""),
                    citation_count=int(c.get("citation_count") or 0),
                    influential_citation_count=int(c.get("influential_citation_count") or 0),
                    arxiv_url=paper.arxiv_url,
                    recall_score=recall_scores[j],
                    rerank_score=float(rerank_scores[j]),
                )
            )
        return results

    def _doc_for_rerank(self, meta: dict) -> str:
        """Text given to the reranker: title + abstract (same as the index text)."""
        title = (meta.get("title") or "").strip()
        abstract = (meta.get("abstract") or "").strip()
        return f"{title}\n\n{abstract}".strip() if abstract else title


if __name__ == "__main__":
    import sys

    engine = SearchEngine()
    q = " ".join(sys.argv[1:]) or "diffusion models for image generation"
    for r in engine.search(q, domain="Computer_Science", years=[2024, 2025]):
        print(
            f"#{r.rank:2d} [{r.year}] cites={r.citation_count:5d} "
            f"rerank={r.rerank_score:.3f}  {r.title}"
        )
