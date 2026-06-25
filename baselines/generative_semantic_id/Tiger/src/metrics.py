"""Recall@K, NDCG@K and MRR@K for generative retrieval.

In the generative setting the model produces a ranked list of candidate
semantic-ID tuples (via beam search). A candidate is "relevant" iff it exactly
equals the ground-truth item's semantic-ID tuple. Each query has a single
relevant item, so:
  - Recall@K = hit rate (1 if the match is in the top K)
  - NDCG@K   = 1 / log2(rank + 2)   when the hit is within the top K
  - MRR@K    = 1 / (rank + 1)        when the hit is within the top K
"""

import math

import torch


def rank_of_match(generated, target):
    """For each query, the 0-based rank of the first beam matching the target,
    or -1 if no beam matches.

    generated: LongTensor (batch, beam, H)   ranked best-first
    target:    LongTensor (batch, H)
    returns:   LongTensor (batch,)
    """
    match = (generated == target.unsqueeze(1)).all(dim=2)  # (batch, beam)
    has_match = match.any(dim=1)
    first = match.float().argmax(dim=1)  # 0 when no match; fixed up below
    return torch.where(has_match, first, torch.full_like(first, -1))


def compute_metrics(generated, target, ks=(5, 10)):
    """Return {'recall@k':.., 'ndcg@k':.., 'mrr@k':..} averaged over the batch."""
    ranks = rank_of_match(generated, target)
    out = {}
    n = ranks.shape[0]
    for k in ks:
        hit = (ranks >= 0) & (ranks < k)
        out[f"recall@{k}"] = hit.float().mean().item()
        ndcg = torch.zeros(n)
        mrr = torch.zeros(n)
        for i in hit.nonzero(as_tuple=True)[0].tolist():
            r = ranks[i].item()
            ndcg[i] = 1.0 / math.log2(r + 2)
            mrr[i] = 1.0 / (r + 1)
        out[f"ndcg@{k}"] = ndcg.mean().item()
        out[f"mrr@{k}"] = mrr.mean().item()
    return out
