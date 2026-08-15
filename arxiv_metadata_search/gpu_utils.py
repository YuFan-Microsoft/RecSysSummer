"""Runtime GPU selection: find the GPUs that are currently idle (free).

Instead of hard-coding GPU ids, we ask ``nvidia-smi`` how much memory each GPU
is using and treat a GPU as *free* when its used memory is at or below a small
threshold (i.e. nothing substantial is loaded on it). This is used by:

  * ``build_index.py`` -> fan the embedding model out over ALL idle GPUs.
  * ``search.py``      -> pin the embedder and reranker on 2 idle GPUs (1 each).

If ``nvidia-smi`` is unavailable, the helpers raise ``RuntimeError`` so the
caller can fall back to an explicit id list or a clear error message.
"""

from __future__ import annotations

import subprocess


def query_gpu_status() -> list[dict]:
    """Return per-GPU ``{index, mem_used_mb, mem_total_mb, util_pct}`` via nvidia-smi.

    Raises ``RuntimeError`` if ``nvidia-smi`` is missing or returns nothing.
    """
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # nvidia-smi absent / failed
        raise RuntimeError(f"nvidia-smi unavailable: {exc}") from exc

    gpus: list[dict] = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        idx, used, total, util = parts[:4]
        gpus.append(
            {
                "index": int(idx),
                "mem_used_mb": int(float(used)),
                "mem_total_mb": int(float(total)),
                "util_pct": int(float(util)),
            }
        )
    if not gpus:
        raise RuntimeError("nvidia-smi returned no GPUs")
    return gpus


def free_gpus(
    reserved: list[int] | None = None,
    mem_used_max_pct: float = 1.0,
    util_max_pct: float = 10.0,
) -> list[int]:
    """Sorted ids of GPUs that look idle, excluding any ``reserved`` ids.

    A GPU is considered *free* only when BOTH hold:
      * used memory is below ``mem_used_max_pct`` percent of its total memory, and
      * GPU utilisation is below ``util_max_pct`` percent.

    Raises ``RuntimeError`` if detection fails.
    """
    reserved_set = set(reserved or [])
    gpus = query_gpu_status()
    out: list[int] = []
    for g in gpus:
        if g["index"] in reserved_set:
            continue
        total = g["mem_total_mb"] or 1
        mem_pct = 100.0 * g["mem_used_mb"] / total
        if mem_pct < mem_used_max_pct and g["util_pct"] < util_max_pct:
            out.append(g["index"])
    return sorted(out)


def describe_gpus(reserved: list[int] | None = None) -> str:
    """One-line human summary of every GPU's memory use (for logging)."""
    reserved_set = set(reserved or [])
    try:
        gpus = query_gpu_status()
    except RuntimeError as exc:
        return f"(gpu status unavailable: {exc})"
    bits = []
    for g in gpus:
        tag = " reserved" if g["index"] in reserved_set else ""
        bits.append(
            f"GPU{g['index']}: {g['mem_used_mb']}/{g['mem_total_mb']}MB "
            f"{g['util_pct']}%{tag}"
        )
    return " | ".join(bits)
