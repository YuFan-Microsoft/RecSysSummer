#!/usr/bin/env python3
"""Refresh Semantic Scholar citation counts for the local arXiv corpus.

The workflow is deliberately split into resumable phases:

1. ``fetch`` snapshots the 2020-2026 JSONL shards, then retrieves only
   ``citationCount`` and ``influentialCitationCount`` into SQLite.
2. ``apply`` atomically rewrites each unchanged source shard and creates a
   persistent marker for ``upload_metadata_hf.py --newer``.
3. ``mark-uploaded`` records that the corresponding Hugging Face upload
   completed.

No existing citation value is overwritten when Semantic Scholar returns no
paper or a request fails.
"""
from __future__ import annotations

import argparse
import calendar
import glob
import json
import os
import random
import shutil
import sqlite3
import stat
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.join(HERE, "arxiv_full_metadata")
DEFAULT_DB = os.path.join(DEFAULT_ROOT, ".citation_refresh.sqlite3")
DEFAULT_MARKER = os.path.join(DEFAULT_ROOT, ".citation_refresh_marker")
S2_BATCH_URL = "https://api.semanticscholar.org/graph/v1/paper/batch"
FIELDS = "citationCount,influentialCitationCount"
UA = "recsys-s2-citation-refresh/1.0"
MIN_YEAR = 2020
MAX_YEAR = 2026


def log(message: str) -> None:
    print(time.strftime("%Y-%m-%d %H:%M:%S"), message, flush=True)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def int_or_none(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def read_api_key() -> str:
    key = os.environ.get("S2_API_KEY", "").strip()
    if key:
        return key
    path = os.path.join(HERE, ".s2_api_key")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            key = handle.read().strip()
    if not key:
        raise SystemExit(
            "S2 API key required for the full citation refresh "
            "(set S2_API_KEY or create arxiv_download_tool/.s2_api_key)."
        )
    return key


def connect(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS papers (
            arxiv_id TEXT PRIMARY KEY,
            corpus_id INTEGER,
            shard TEXT NOT NULL,
            year INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            citation_count INTEGER,
            influential_citation_count INTEGER,
            published INTEGER NOT NULL DEFAULT 0,
            attempts INTEGER NOT NULL DEFAULT 0,
            fetched_at TEXT,
            last_error TEXT
        );
        CREATE INDEX IF NOT EXISTS papers_status_idx
            ON papers(status, year DESC, arxiv_id DESC);
        CREATE INDEX IF NOT EXISTS papers_shard_idx
            ON papers(shard, status);

        CREATE TABLE IF NOT EXISTS shards (
            path TEXT PRIMARY KEY,
            row_count INTEGER NOT NULL,
            eligible_count INTEGER NOT NULL,
            source_size INTEGER NOT NULL,
            source_mtime_ns INTEGER NOT NULL,
            applied INTEGER NOT NULL DEFAULT 0,
            updated_rows INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    paper_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(papers)")
    }
    if "published" not in paper_columns:
        with conn:
            conn.execute(
                "ALTER TABLE papers "
                "ADD COLUMN published INTEGER NOT NULL DEFAULT 0"
            )
    return conn


def get_meta(conn: sqlite3.Connection, key: str, default=None):
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_meta(conn: sqlite3.Connection, key: str, value) -> None:
    conn.execute(
        """
        INSERT INTO meta(key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, str(value)),
    )


def discover_shards(root: str) -> list[str]:
    paths = []
    for year in range(MIN_YEAR, MAX_YEAR + 1):
        paths.extend(
            glob.glob(os.path.join(root, str(year), "*", "metadata.jsonl"))
        )
    return sorted(paths)


def initialize_state(conn: sqlite3.Connection, root: str) -> None:
    if get_meta(conn, "initialized") == "1":
        return

    shards = discover_shards(root)
    if not shards:
        raise SystemExit(f"No {MIN_YEAR}-{MAX_YEAR} metadata shards found in {root}")

    log(f"initializing SQLite state from {len(shards)} metadata shards")
    with conn:
        conn.execute("DELETE FROM papers")
        conn.execute("DELETE FROM shards")
        conn.execute("DELETE FROM meta")
        set_meta(conn, "initializing", utc_now())

    total_rows = 0
    eligible_rows = 0
    skipped_not_found = 0
    for index, path in enumerate(shards, 1):
        before = os.stat(path)
        relative = os.path.relpath(path, root)
        year = int(relative.split(os.sep, 1)[0])
        rows = 0
        eligible = 0
        skipped = 0
        pending = []

        try:
            with conn:
                with open(path, encoding="utf-8") as handle:
                    for line_number, line in enumerate(handle, 1):
                        if not line.strip():
                            continue
                        rows += 1
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError as error:
                            raise RuntimeError(
                                f"{relative}:{line_number}: invalid JSON: {error}"
                            ) from error
                        arxiv_id = record.get("arxiv_id")
                        if not arxiv_id:
                            raise RuntimeError(
                                f"{relative}:{line_number}: missing arxiv_id"
                            )
                        if record.get("found") is False:
                            skipped += 1
                            continue
                        pending.append(
                            (
                                str(arxiv_id),
                                int_or_none(record.get("corpusId")),
                                relative,
                                year,
                            )
                        )
                        eligible += 1
                        if len(pending) >= 5000:
                            conn.executemany(
                                """
                                INSERT INTO papers(
                                    arxiv_id, corpus_id, shard, year
                                ) VALUES (?, ?, ?, ?)
                                """,
                                pending,
                            )
                            pending.clear()
                    if pending:
                        conn.executemany(
                            """
                            INSERT INTO papers(
                                arxiv_id, corpus_id, shard, year
                            ) VALUES (?, ?, ?, ?)
                            """,
                            pending,
                        )

                after = os.stat(path)
                if (
                    after.st_size != before.st_size
                    or after.st_mtime_ns != before.st_mtime_ns
                ):
                    raise RuntimeError(
                        f"{relative} changed while citation state was initialized"
                    )
                conn.execute(
                    """
                    INSERT INTO shards(
                        path, row_count, eligible_count,
                        source_size, source_mtime_ns
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        relative,
                        rows,
                        eligible,
                        before.st_size,
                        before.st_mtime_ns,
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise RuntimeError(
                f"duplicate arxiv_id detected while scanning {relative}"
            ) from error

        total_rows += rows
        eligible_rows += eligible
        skipped_not_found += skipped
        log(
            f"indexed shard {index}/{len(shards)}: {relative} "
            f"rows={rows:,} eligible={eligible:,}"
        )

    with conn:
        set_meta(conn, "initialized", 1)
        set_meta(conn, "initialized_at", utc_now())
        set_meta(conn, "source_rows", total_rows)
        set_meta(conn, "eligible_rows", eligible_rows)
        set_meta(conn, "skipped_found_false", skipped_not_found)
        set_meta(conn, "request_count", 0)
        set_meta(conn, "rate_limit_count", 0)
        set_meta(conn, "apply_complete", 0)
        set_meta(conn, "upload_complete", 0)
        conn.execute("DELETE FROM meta WHERE key = 'initializing'")
    log(
        f"state ready: rows={total_rows:,} eligible={eligible_rows:,} "
        f"found:false skipped={skipped_not_found:,}"
    )


class RateLimiter:
    def __init__(self, minimum_interval: float, jitter: float = 0.5):
        self.minimum_interval = minimum_interval
        self.jitter = jitter
        self.last_start = None

    def wait(self) -> None:
        if self.last_start is not None:
            remaining = self.minimum_interval - (
                time.monotonic() - self.last_start
            )
            if remaining > 0:
                time.sleep(remaining)
        if self.jitter > 0:
            time.sleep(random.uniform(0, self.jitter))
        self.last_start = time.monotonic()


def request_batch(
    rows,
    api_key: str,
    limiter: RateLimiter,
    retries: int,
    timeout: float,
):
    identifiers = []
    for row in rows:
        if row["corpus_id"] is not None:
            identifiers.append(f"CorpusId:{row['corpus_id']}")
        else:
            identifiers.append(f"ARXIV:{row['arxiv_id']}")

    url = S2_BATCH_URL + "?" + urllib.parse.urlencode({"fields": FIELDS})
    body = json.dumps({"ids": identifiers}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": UA,
        "x-api-key": api_key,
    }
    rate_limits = 0
    last_error = ""

    for attempt in range(1, retries + 1):
        limiter.wait()
        try:
            request = urllib.request.Request(
                url, data=body, headers=headers, method="POST"
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read())
            if not isinstance(payload, list) or len(payload) != len(rows):
                actual = len(payload) if isinstance(payload, list) else type(payload).__name__
                last_error = (
                    f"malformed response: expected {len(rows)} entries, got {actual}"
                )
                if attempt < retries:
                    log(f"{last_error}; retrying after 30s")
                    time.sleep(30)
                    continue
                return None, last_error, rate_limits, "transient"
            return payload, "", rate_limits, None
        except urllib.error.HTTPError as error:
            body_preview = error.read(500).decode("utf-8", errors="replace")
            last_error = f"HTTP {error.code}: {body_preview}"
            if error.code == 429:
                rate_limits += 1
                return None, last_error, rate_limits, "rate_limited"
            if error.code in (408, 425, 503) or 500 <= error.code < 600:
                if attempt >= retries:
                    return None, last_error, rate_limits, "transient"
                wait = min(300, 30 * (2 ** (attempt - 1)))
                log(f"HTTP {error.code}; retrying after {wait}s")
                time.sleep(wait)
                continue
            if error.code == 400:
                return None, last_error, rate_limits, "split"
            return None, last_error, rate_limits, "abort"
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = f"{type(error).__name__}: {error}"
            if attempt < retries:
                wait = min(300, 30 * (2 ** (attempt - 1)))
                log(f"network error; retrying after {wait}s: {error}")
                time.sleep(wait)
                continue
            return None, last_error, rate_limits, "transient"
        except (json.JSONDecodeError, ValueError) as error:
            last_error = f"invalid JSON response: {error}"
            if attempt < retries:
                log(f"{last_error}; retrying after 30s")
                time.sleep(30)
                continue
            return None, last_error, rate_limits, "transient"

    return (
        None,
        last_error or "request retries exhausted",
        rate_limits,
        "transient",
    )


def resolve_batch(
    rows,
    api_key,
    limiter,
    retries,
    timeout,
    split_request_budget,
):
    remaining_requests = split_request_budget

    def walk(subset):
        nonlocal remaining_requests
        if remaining_requests <= 0:
            return (
                [
                    (
                        subset,
                        None,
                        "HTTP 400 split-request budget exhausted",
                        "transient",
                    )
                ],
                0,
                0,
            )

        remaining_requests -= 1
        payload, error_message, rate_limits, failure_kind = request_batch(
            subset, api_key, limiter, retries, timeout
        )
        request_count = 1
        if payload is None and failure_kind == "split" and len(subset) > 1:
            middle = len(subset) // 2
            left, left_requests, left_429 = walk(subset[:middle])
            right, right_requests, right_429 = walk(subset[middle:])
            return (
                left + right,
                request_count + left_requests + right_requests,
                rate_limits + left_429 + right_429,
            )
        return (
            [(subset, payload, error_message, failure_kind)],
            request_count,
            rate_limits,
        )

    return walk(rows)


def status_counts(conn: sqlite3.Connection) -> dict[str, int]:
    counts = {
        row["status"]: row["count"]
        for row in conn.execute(
            "SELECT status, COUNT(*) AS count FROM papers GROUP BY status"
        )
    }
    for status_name in ("pending", "done", "not_found", "skipped", "error"):
        counts.setdefault(status_name, 0)
    return counts


def run_fetch(args) -> int:
    conn = connect(args.db)
    try:
        api_key = read_api_key()
        initialize_state(conn, args.root)
        if get_meta(conn, "upload_complete") == "1":
            raise SystemExit(
                "This citation refresh campaign is already uploaded. "
                "Use --reset only when intentionally starting a new campaign."
            )

        with conn:
            error_count = conn.execute(
                "SELECT COUNT(*) AS n FROM papers WHERE status = 'error'"
            ).fetchone()["n"]
            if error_count:
                log(
                    f"reviving {error_count:,} prior transient-error rows "
                    f"for this supervisor pass"
                )
            conn.execute(
                """
                UPDATE papers
                SET status = 'pending', attempts = 0, last_error = NULL
                WHERE status = 'error'
                """
            )

        if args.initial_delay > 0:
            log(
                f"initial API cooldown: waiting {args.initial_delay:.0f}s "
                f"before the first request"
            )
            time.sleep(args.initial_delay)

        limiter = RateLimiter(args.min_interval, args.jitter)
        completed_batches = 0
        started = time.monotonic()

        while True:
            rows = conn.execute(
                """
                SELECT arxiv_id, corpus_id
                FROM papers
                WHERE status = 'pending'
                ORDER BY year DESC, arxiv_id DESC
                LIMIT ?
                """,
                (args.batch_size,),
            ).fetchall()
            if not rows:
                retryable = conn.execute(
                    """
                    SELECT COUNT(*) AS n
                    FROM papers
                    WHERE status = 'error' AND attempts < ?
                    """,
                    (args.max_attempts,),
                ).fetchone()["n"]
                if retryable and not args.limit_batches:
                    log(
                        f"{retryable:,} transient errors remain; waiting "
                        f"{args.error_retry_delay:.0f}s before another pass"
                    )
                    time.sleep(args.error_retry_delay)
                    with conn:
                        conn.execute(
                            """
                            UPDATE papers
                            SET status = 'pending', last_error = NULL
                            WHERE status = 'error' AND attempts < ?
                            """,
                            (args.max_attempts,),
                        )
                    continue
                break
            if args.limit_batches and completed_batches >= args.limit_batches:
                break

            outcomes, request_count, rate_limits = resolve_batch(
                rows,
                api_key,
                limiter,
                args.request_retries,
                args.timeout,
                args.split_request_budget,
            )
            fetched_at = utc_now()
            abort_outcome = next(
                (
                    (failure_kind, error_message)
                    for _, payload, error_message, failure_kind in outcomes
                    if payload is None
                    and failure_kind in ("abort", "rate_limited")
                ),
                None,
            )
            abort_kind = abort_outcome[0] if abort_outcome else None
            abort_error = abort_outcome[1] if abort_outcome else None
            with conn:
                total_requests = int(get_meta(conn, "request_count", 0))
                set_meta(conn, "request_count", total_requests + request_count)
                if rate_limits:
                    total_429 = int(get_meta(conn, "rate_limit_count", 0))
                    set_meta(conn, "rate_limit_count", total_429 + rate_limits)

                if abort_error:
                    set_meta(conn, "last_abort_error", abort_error)
                    set_meta(conn, "last_abort_at", fetched_at)

                for outcome_rows, payload, error_message, failure_kind in outcomes:
                    if failure_kind in ("abort", "rate_limited"):
                        continue
                    if payload is None:
                        if failure_kind == "split" and len(outcome_rows) == 1:
                            conn.execute(
                                """
                                UPDATE papers
                                SET status = 'skipped',
                                    attempts = attempts + 1,
                                    last_error = ?
                                WHERE arxiv_id = ?
                                """,
                                (error_message, outcome_rows[0]["arxiv_id"]),
                            )
                        else:
                            conn.executemany(
                                """
                                UPDATE papers
                                SET status = 'error',
                                    attempts = attempts + ?,
                                    last_error = ?
                                WHERE arxiv_id = ?
                                """,
                                [
                                    (
                                        1,
                                        error_message,
                                        row["arxiv_id"],
                                    )
                                    for row in outcome_rows
                                ],
                            )
                    else:
                        updates = []
                        for row, record in zip(outcome_rows, payload):
                            if record is None:
                                updates.append(
                                    (
                                        "not_found",
                                        None,
                                        None,
                                        fetched_at,
                                        None,
                                        row["arxiv_id"],
                                    )
                                )
                            else:
                                updates.append(
                                    (
                                        "done",
                                        int_or_none(record.get("citationCount")),
                                        int_or_none(
                                            record.get(
                                                "influentialCitationCount"
                                            )
                                        ),
                                        fetched_at,
                                        None,
                                        row["arxiv_id"],
                                    )
                                )
                        conn.executemany(
                            """
                            UPDATE papers
                            SET status = ?,
                                citation_count = ?,
                                influential_citation_count = ?,
                                fetched_at = ?,
                                last_error = ?,
                                attempts = attempts + 1
                            WHERE arxiv_id = ?
                            """,
                            updates,
                        )

            if abort_error:
                if abort_kind == "rate_limited":
                    log(
                        "Semantic Scholar rate limited this request; "
                        "checkpoint preserved without changing rows"
                    )
                    return 75
                raise SystemExit(
                    f"Semantic Scholar request aborted without changing rows: "
                    f"{abort_error}"
                )

            completed_batches += request_count
            counts = status_counts(conn)
            elapsed = max(time.monotonic() - started, 0.001)
            processed = (
                counts["done"] + counts["not_found"] + counts["skipped"]
            )
            rate = processed / elapsed
            eta_seconds = counts["pending"] / rate if rate > 0 else 0
            log(
                f"batch {completed_batches}: size={len(rows)} "
                f"done={counts['done']:,} not_found={counts['not_found']:,} "
                f"skipped={counts['skipped']:,} "
                f"pending={counts['pending']:,} errors={counts['error']:,} "
                f"429={get_meta(conn, 'rate_limit_count', 0)} "
                f"eta={eta_seconds / 3600:.1f}h"
            )

        counts = status_counts(conn)
        log(
            "fetch status: "
            + " ".join(f"{key}={value:,}" for key, value in counts.items())
        )
        if counts["error"]:
            log("fetch stopped with errors; rerun later to retry without losing progress")
            return 2
        return 0
    finally:
        conn.close()


def verify_unapplied_sources(conn: sqlite3.Connection, root: str) -> None:
    for row in conn.execute(
        "SELECT * FROM shards WHERE applied != 1 ORDER BY path"
    ):
        path = os.path.join(root, row["path"])
        if not os.path.exists(path):
            raise SystemExit(f"Missing source shard: {row['path']}")
        if row["applied"] == 2:
            continue
        current = os.stat(path)
        if (
            current.st_size != row["source_size"]
            or current.st_mtime_ns != row["source_mtime_ns"]
        ):
            raise SystemExit(
                f"Refusing to apply: source shard changed after the fetch "
                f"snapshot: {row['path']}"
            )


def rewrite_shard(
    conn: sqlite3.Connection,
    root: str,
    shard_row: sqlite3.Row,
) -> int:
    relative = shard_row["path"]
    path = os.path.join(root, relative)
    updates = {
        row["arxiv_id"]: (
            row["citation_count"],
            row["influential_citation_count"],
            row["fetched_at"],
        )
        for row in conn.execute(
            """
            SELECT arxiv_id, citation_count,
                   influential_citation_count, fetched_at
            FROM papers
            WHERE shard = ? AND status = 'done'
            """,
            (relative,),
        )
    }
    if not updates:
        with conn:
            conn.execute(
                "UPDATE shards SET applied = 1, updated_rows = 0 WHERE path = ?",
                (relative,),
            )
        return 0

    with conn:
        conn.execute(
            "UPDATE shards SET applied = 2 WHERE path = ?",
            (relative,),
        )

    source_stat = os.stat(path)
    temporary = path + ".citation-refresh.tmp"
    if os.path.exists(temporary):
        os.remove(temporary)

    rows = 0
    matched = 0
    try:
        with open(path, encoding="utf-8") as source, open(
            temporary, "w", encoding="utf-8"
        ) as target:
            for line_number, line in enumerate(source, 1):
                if not line.strip():
                    continue
                rows += 1
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise RuntimeError(
                        f"{relative}:{line_number}: invalid JSON: {error}"
                    ) from error
                arxiv_id = record.get("arxiv_id")
                update = updates.get(arxiv_id)
                if update is not None:
                    citation_count, influential_count, fetched_at = update
                    if citation_count is not None:
                        record["citationCount"] = citation_count
                    if influential_count is not None:
                        record["influentialCitationCount"] = influential_count
                    record["citation_refreshed_at"] = fetched_at
                    matched += 1
                target.write(json.dumps(record, ensure_ascii=False) + "\n")
            target.flush()
            os.fsync(target.fileno())

        if rows != shard_row["row_count"]:
            raise RuntimeError(
                f"{relative}: row count changed during rewrite "
                f"({rows:,} != {shard_row['row_count']:,})"
            )
        if matched != len(updates):
            raise RuntimeError(
                f"{relative}: matched {matched:,}/{len(updates):,} citation updates"
            )

        os.chmod(temporary, stat.S_IMODE(source_stat.st_mode))
        os.replace(temporary, path)
        with conn:
            conn.execute(
                """
                UPDATE shards
                SET applied = 1, updated_rows = ?
                WHERE path = ?
                """,
                (matched, relative),
            )
        return matched
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def run_apply(args) -> int:
    conn = connect(args.db)
    try:
        if get_meta(conn, "initialized") != "1":
            raise SystemExit("Citation refresh state is not initialized")

        counts = status_counts(conn)
        if counts["pending"] or counts["error"]:
            raise SystemExit(
                "Refusing to rewrite metadata before fetch completion: "
                f"pending={counts['pending']:,}, errors={counts['error']:,}"
            )

        if get_meta(conn, "apply_complete") == "1":
            if not os.path.exists(args.marker) and get_meta(
                conn, "upload_complete"
            ) != "1":
                raise SystemExit(
                    "Apply is complete but the upload marker is missing; "
                    "cannot safely identify changed shards."
                )
            log("citation updates are already applied")
            return 0

        eligible_rows = int(get_meta(conn, "eligible_rows", 0))
        coverage = counts["done"] / eligible_rows if eligible_rows else 0.0
        if not args.force and coverage < args.min_coverage:
            raise SystemExit(
                f"Refusing to apply: successful citation coverage "
                f"{coverage:.2%} is below {args.min_coverage:.2%} "
                f"(done={counts['done']:,}, eligible={eligible_rows:,}, "
                f"not_found={counts['not_found']:,}, skipped={counts['skipped']:,})"
            )

        verify_unapplied_sources(conn, args.root)
        if not os.path.exists(args.marker):
            with open(args.marker, "x", encoding="utf-8") as marker:
                marker.write(utc_now() + "\n")
                marker.flush()
                os.fsync(marker.fileno())
            time.sleep(1.1)

        shard_rows = conn.execute(
            "SELECT * FROM shards WHERE applied != 1 ORDER BY path"
        ).fetchall()
        total_updated = 0
        for index, shard_row in enumerate(shard_rows, 1):
            updated = rewrite_shard(conn, args.root, shard_row)
            total_updated += updated
            log(
                f"applied shard {index}/{len(shard_rows)}: "
                f"{shard_row['path']} updated={updated:,}"
            )

        applied_rows = conn.execute(
            "SELECT COALESCE(SUM(updated_rows), 0) AS n FROM shards"
        ).fetchone()["n"]
        expected_rows = counts["done"]
        if applied_rows != expected_rows:
            raise SystemExit(
                f"Applied-row validation failed: {applied_rows:,} != {expected_rows:,}"
            )
        with conn:
            set_meta(conn, "apply_complete", 1)
            set_meta(conn, "applied_at", utc_now())
            set_meta(conn, "applied_rows", applied_rows)
        log(f"apply complete: citation timestamps written for {applied_rows:,} papers")
        return 0
    finally:
        conn.close()


def write_partial_shard(
    conn: sqlite3.Connection,
    root: str,
    temporary_root: str,
    shard_row: sqlite3.Row,
) -> tuple[str, int]:
    relative = shard_row["path"]
    source_path = os.path.join(root, relative)
    target_path = os.path.join(temporary_root, relative)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    updates = {
        row["arxiv_id"]: (
            row["citation_count"],
            row["influential_citation_count"],
            row["fetched_at"],
        )
        for row in conn.execute(
            """
            SELECT arxiv_id, citation_count,
                   influential_citation_count, fetched_at
            FROM papers
            WHERE shard = ? AND status = 'done'
            """,
            (relative,),
        )
    }
    rows = 0
    matched = 0
    source_before = os.stat(source_path)
    with open(source_path, encoding="utf-8") as source, open(
        target_path, "w", encoding="utf-8"
    ) as target:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            rows += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise RuntimeError(
                    f"{relative}:{line_number}: invalid JSON: {error}"
                ) from error
            update = updates.get(record.get("arxiv_id"))
            if update is not None:
                citation_count, influential_count, fetched_at = update
                if citation_count is not None:
                    record["citationCount"] = citation_count
                if influential_count is not None:
                    record["influentialCitationCount"] = influential_count
                record["citation_refreshed_at"] = fetched_at
                matched += 1
            target.write(json.dumps(record, ensure_ascii=False) + "\n")
        target.flush()
        os.fsync(target.fileno())

    source_after = os.stat(source_path)
    if (
        source_after.st_size != source_before.st_size
        or source_after.st_mtime_ns != source_before.st_mtime_ns
    ):
        raise RuntimeError(
            f"{relative}: source changed while partial publish was prepared"
        )
    if matched != len(updates):
        raise RuntimeError(
            f"{relative}: partial publish matched "
            f"{matched:,}/{len(updates):,} updates"
        )
    if (
        rows != shard_row["row_count"]
        or source_after.st_size != shard_row["source_size"]
        or source_after.st_mtime_ns != shard_row["source_mtime_ns"]
    ):
        with conn:
            conn.execute(
                """
                UPDATE shards
                SET row_count = ?,
                    source_size = ?,
                    source_mtime_ns = ?
                WHERE path = ?
                """,
                (
                    rows,
                    source_after.st_size,
                    source_after.st_mtime_ns,
                    relative,
                ),
            )
        log(
            f"rebased source snapshot for {relative}: "
            f"{shard_row['row_count']:,} -> {rows:,} rows"
        )
    return target_path, matched


def publish_partial(args) -> int:
    if not os.path.exists(args.db):
        log("no citation state yet; nothing to publish")
        return 0
    conn = connect(args.db)
    temporary_root = os.path.join(args.root, ".citation_partial_publish")
    try:
        if get_meta(conn, "initialized") != "1":
            log("citation state is not initialized; nothing to publish")
            return 0
        unpublished = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM papers
            WHERE status = 'done' AND published = 0
            """
        ).fetchone()["n"]
        if not unpublished:
            log("no unpublished citation checkpoint to send to Hugging Face")
            return 0
        if not args.force and unpublished < args.min_unpublished:
            last_partial = get_meta(conn, "last_partial_at")
            age_hours = float("inf")
            if last_partial:
                parsed = time.strptime(last_partial, "%Y-%m-%dT%H:%M:%SZ")
                age_hours = (
                    time.time() - calendar.timegm(parsed)
                ) / 3600
            if age_hours < args.max_age_hours:
                log(
                    f"deferring partial publish: {unpublished:,} unpublished "
                    f"< {args.min_unpublished:,} and last publish was "
                    f"{age_hours:.1f}h ago"
                )
                return 0

        shard_rows = conn.execute(
            """
            SELECT s.*
            FROM shards AS s
            WHERE EXISTS (
                SELECT 1
                FROM papers AS p
                WHERE p.shard = s.path
                  AND p.status = 'done'
                  AND p.published = 0
            )
            ORDER BY s.path
            """
        ).fetchall()
        if os.path.exists(temporary_root):
            shutil.rmtree(temporary_root)

        operations = []
        affected_shards = []
        try:
            from huggingface_hub import CommitOperationAdd, HfApi
            from upload_metadata_hf import REPO_ID, resolve_token

            for index, shard_row in enumerate(shard_rows, 1):
                target_path, cumulative_updates = write_partial_shard(
                    conn, args.root, temporary_root, shard_row
                )
                year, subject = shard_row["path"].split(os.sep)[:2]
                path_in_repo = f"{subject}/{year}/metadata.jsonl"
                operations.append(
                    CommitOperationAdd(
                        path_in_repo=path_in_repo,
                        path_or_fileobj=target_path,
                    )
                )
                affected_shards.append(shard_row["path"])
                log(
                    f"prepared partial shard {index}/{len(shard_rows)}: "
                    f"{shard_row['path']} cumulative_updates={cumulative_updates:,}"
                )

            if args.dry_run:
                log(
                    f"partial publish dry-run: {unpublished:,} new papers "
                    f"across {len(operations)} shards"
                )
                return 0

            token = resolve_token()
            done_count = status_counts(conn)["done"]
            eligible_rows = int(get_meta(conn, "eligible_rows", 0))
            info = HfApi(token=token).create_commit(
                repo_id=REPO_ID,
                repo_type="dataset",
                operations=operations,
                commit_message=(
                    f"Partial citation refresh: +{unpublished:,} papers "
                    f"({done_count:,}/{eligible_rows:,})"
                ),
            )
            commit_url = str(getattr(info, "commit_url", info))
            placeholders = ",".join("?" for _ in affected_shards)
            with conn:
                conn.execute(
                    f"""
                    UPDATE papers
                    SET published = 1
                    WHERE status = 'done'
                      AND shard IN ({placeholders})
                    """,
                    affected_shards,
                )
                partial_count = int(get_meta(conn, "partial_upload_count", 0))
                set_meta(conn, "partial_upload_count", partial_count + 1)
                set_meta(conn, "last_partial_commit", commit_url)
                set_meta(conn, "last_partial_at", utc_now())
            log(f"partial Hugging Face commit complete: {commit_url}")
            return 0
        finally:
            if os.path.exists(temporary_root):
                shutil.rmtree(temporary_root)
    finally:
        conn.close()


def print_status(args) -> int:
    if not os.path.exists(args.db):
        print(f"state_db={args.db} (missing)")
        return 1
    conn = connect(args.db)
    try:
        counts = status_counts(conn)
        print(f"state_db={args.db}")
        for key in (
            "initialized_at",
            "source_rows",
            "eligible_rows",
            "skipped_found_false",
            "request_count",
            "rate_limit_count",
            "apply_complete",
            "applied_at",
            "applied_rows",
            "upload_complete",
            "uploaded_at",
            "partial_upload_count",
            "last_partial_commit",
            "last_partial_at",
        ):
            value = get_meta(conn, key)
            if value is not None:
                print(f"{key}={value}")
        for key in ("pending", "done", "not_found", "skipped", "error"):
            print(f"{key}={counts[key]}")
        unpublished = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM papers
            WHERE status = 'done' AND published = 0
            """
        ).fetchone()["n"]
        print(f"unpublished_done={unpublished}")
        return 0
    finally:
        conn.close()


def mark_uploaded(args) -> int:
    conn = connect(args.db)
    try:
        if get_meta(conn, "apply_complete") != "1":
            raise SystemExit("Cannot mark upload complete before apply completion")
        with conn:
            conn.execute(
                "UPDATE papers SET published = 1 WHERE status = 'done'"
            )
            set_meta(conn, "upload_complete", 1)
            set_meta(conn, "uploaded_at", utc_now())
        log("upload marked complete")
        return 0
    finally:
        conn.close()


def is_uploaded(args) -> int:
    if not os.path.exists(args.db):
        return 1
    conn = connect(args.db)
    try:
        return 0 if get_meta(conn, "upload_complete") == "1" else 1
    finally:
        conn.close()


def is_active(args) -> int:
    if not os.path.exists(args.db):
        return 1
    conn = connect(args.db)
    try:
        active = (
            get_meta(conn, "initialized") == "1"
            and get_meta(conn, "upload_complete") != "1"
            and get_meta(conn, "abandoned") != "1"
        )
        return 0 if active else 1
    finally:
        conn.close()


def abandon(args) -> int:
    if not os.path.exists(args.db):
        return 0
    conn = connect(args.db)
    try:
        with conn:
            set_meta(conn, "abandoned", 1)
            set_meta(conn, "abandoned_at", utc_now())
        log("Graph citation campaign marked abandoned")
        return 0
    finally:
        conn.close()


def reset_state(db_path: str, marker: str) -> None:
    for path in (db_path, db_path + "-wal", db_path + "-shm", marker):
        if os.path.exists(path):
            os.remove(path)
    log("removed prior citation refresh state")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--marker", default=DEFAULT_MARKER)
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser("fetch")
    fetch.add_argument("--batch-size", type=int, default=500)
    fetch.add_argument(
        "--min-interval",
        type=float,
        default=5.0,
        help="minimum seconds between request starts (default: 5.0)",
    )
    fetch.add_argument("--jitter", type=float, default=0.5)
    fetch.add_argument("--initial-delay", type=float, default=0.0)
    fetch.add_argument("--timeout", type=float, default=90.0)
    fetch.add_argument("--request-retries", type=int, default=6)
    fetch.add_argument("--max-attempts", type=int, default=3)
    fetch.add_argument("--error-retry-delay", type=float, default=300.0)
    fetch.add_argument("--split-request-budget", type=int, default=32)
    fetch.add_argument("--limit-batches", type=int, default=0)
    fetch.add_argument("--reset", action="store_true")

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--min-coverage", type=float, default=0.99)
    apply_parser.add_argument("--force", action="store_true")
    subparsers.add_parser("status")
    partial_parser = subparsers.add_parser("publish-partial")
    partial_parser.add_argument("--dry-run", action="store_true")
    partial_parser.add_argument("--force", action="store_true")
    partial_parser.add_argument("--min-unpublished", type=int, default=50000)
    partial_parser.add_argument("--max-age-hours", type=float, default=12.0)
    subparsers.add_parser("mark-uploaded")
    subparsers.add_parser("is-uploaded")
    subparsers.add_parser("is-active")
    subparsers.add_parser("abandon")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.root = os.path.abspath(os.path.expanduser(args.root))
    args.db = os.path.abspath(os.path.expanduser(args.db))
    args.marker = os.path.abspath(os.path.expanduser(args.marker))

    if args.command == "fetch":
        if not 1 <= args.batch_size <= 500:
            raise SystemExit("--batch-size must be between 1 and 500")
        if args.min_interval < 1.0:
            raise SystemExit("--min-interval must be at least 1 second")
        if args.reset:
            reset_state(args.db, args.marker)
        return run_fetch(args)
    if args.command == "apply":
        return run_apply(args)
    if args.command == "status":
        return print_status(args)
    if args.command == "publish-partial":
        return publish_partial(args)
    if args.command == "mark-uploaded":
        return mark_uploaded(args)
    if args.command == "is-uploaded":
        return is_uploaded(args)
    if args.command == "is-active":
        return is_active(args)
    if args.command == "abandon":
        return abandon(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    sys.exit(main())
