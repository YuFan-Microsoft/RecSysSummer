from __future__ import annotations

from typing import Any


def ensure_history_sids_in_extra_info(row: dict[str, Any]) -> dict[str, Any]:
    extra_info = row.get("extra_info")
    if extra_info is None:
        extra_info = {}
        row["extra_info"] = extra_info

    if extra_info.get("history_sids") is None and row.get("history_sids") is not None:
        extra_info["history_sids"] = row["history_sids"]

    return row