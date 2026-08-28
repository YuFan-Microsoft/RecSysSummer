#!/usr/bin/env python3
"""Refresh citation counts from the Semantic Scholar papers dataset.

The pipeline is resumable and intentionally keeps at most one downloaded gzip
shard on disk:

1. Snapshot local 2020-2026 metadata and index its Semantic Scholar corpus IDs.
2. Download one official ``papers`` dataset gzip shard.
3. Stream it, checkpoint matching citation counts in SQLite, then delete it.
4. After every dataset shard is complete, atomically rewrite local JSONL
   shards and upload them with ``upload_metadata_hf.py --newer``.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import re
import sqlite3
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

try:
    import orjson

    def json_loads(data):
        return orjson.loads(data)

except ImportError:

    def json_loads(data):
        return json.loads(data)


HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.join(HERE, "arxiv_full_metadata")
DEFAULT_DB = os.path.join(DEFAULT_ROOT, ".citation_dataset_refresh.sqlite3")
DEFAULT_WORK = os.path.join(DEFAULT_ROOT, ".citation_dataset_refresh")
DEFAULT_MARKER = os.path.join(DEFAULT_ROOT, ".citation_dataset_refresh_marker")
LATEST_RELEASE_URL = (
    "https://api.semanticscholar.org/datasets/v1/release/latest"
)
DATASET_URL = (
    "https://api.semanticscholar.org/datasets/v1/release/"
    "{release_id}/dataset/papers"
)
MIN_YEAR = 2020
MAX_YEAR = 2026
UA = "recsys-s2-dataset-citation-refresh/1.0"
CORPUS_ID_PATTERN = re.compile(
    rb'"(?:corpusid|corpusId)"\s*:\s*(\d+)'
)


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
            "S2 API key required (set S2_API_KEY or create "
            "arxiv_download_tool/.s2_api_key)."
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
        CREATE TABLE IF NOT EXISTS targets (
            arxiv_id TEXT PRIMARY KEY,
            corpus_id INTEGER NOT NULL,
            shard TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS targets_corpus_idx
            ON targets(corpus_id);
        CREATE INDEX IF NOT EXISTS targets_shard_idx
            ON targets(shard);

        CREATE TABLE IF NOT EXISTS counts (
            corpus_id INTEGER PRIMARY KEY,
            citation_count INTEGER,
            influential_citation_count INTEGER,
            release_id TEXT NOT NULL,
            matched_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS shards (
            path TEXT PRIMARY KEY,
            row_count INTEGER NOT NULL,
            target_count INTEGER NOT NULL,
            source_size INTEGER NOT NULL,
            source_mtime_ns INTEGER NOT NULL,
            applied INTEGER NOT NULL DEFAULT 0,
            updated_rows INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS files (
            file_key TEXT PRIMARY KEY,
            ordinal INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0,
            record_count INTEGER NOT NULL DEFAULT 0,
            matched_lines INTEGER NOT NULL DEFAULT 0,
            metric_lines INTEGER NOT NULL DEFAULT 0,
            malformed_target_lines INTEGER NOT NULL DEFAULT 0,
            download_bytes INTEGER NOT NULL DEFAULT 0,
            processed_at TEXT,
            last_error TEXT
        );

        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    file_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(files)")
    }
    migrations = {
        "attempts": (
            "ALTER TABLE files ADD COLUMN "
            "attempts INTEGER NOT NULL DEFAULT 0"
        ),
        "metric_lines": (
            "ALTER TABLE files ADD COLUMN "
            "metric_lines INTEGER NOT NULL DEFAULT 0"
        ),
        "malformed_target_lines": (
            "ALTER TABLE files ADD COLUMN "
            "malformed_target_lines INTEGER NOT NULL DEFAULT 0"
        ),
    }
    with conn:
        for column, statement in migrations.items():
            if column not in file_columns:
                conn.execute(statement)
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
    result = []
    for year in range(MIN_YEAR, MAX_YEAR + 1):
        result.extend(
            glob.glob(os.path.join(root, str(year), "*", "metadata.jsonl"))
        )
    return sorted(result)


def initialize_state(conn: sqlite3.Connection, root: str) -> None:
    if get_meta(conn, "initialized") == "1":
        return

    shards = discover_shards(root)
    if not shards:
        raise SystemExit(f"No {MIN_YEAR}-{MAX_YEAR} metadata shards found in {root}")

    log(f"indexing corpus IDs from {len(shards)} local metadata shards")
    with conn:
        conn.execute("DELETE FROM targets")
        conn.execute("DELETE FROM counts")
        conn.execute("DELETE FROM shards")
        conn.execute("DELETE FROM files")
        conn.execute("DELETE FROM meta")
        set_meta(conn, "initializing", utc_now())

    total_rows = 0
    target_rows = 0
    for index, path in enumerate(shards, 1):
        before = os.stat(path)
        relative = os.path.relpath(path, root)
        rows = 0
        targets = 0
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
                        corpus_id = int_or_none(record.get("corpusId"))
                        if corpus_id is None:
                            continue
                        pending.append((str(arxiv_id), corpus_id, relative))
                        targets += 1
                        if len(pending) >= 5000:
                            conn.executemany(
                                """
                                INSERT INTO targets(arxiv_id, corpus_id, shard)
                                VALUES (?, ?, ?)
                                """,
                                pending,
                            )
                            pending.clear()
                    if pending:
                        conn.executemany(
                            """
                            INSERT INTO targets(arxiv_id, corpus_id, shard)
                            VALUES (?, ?, ?)
                            """,
                            pending,
                        )

                after = os.stat(path)
                if (
                    after.st_size != before.st_size
                    or after.st_mtime_ns != before.st_mtime_ns
                ):
                    raise RuntimeError(
                        f"{relative} changed while dataset state was initialized"
                    )
                conn.execute(
                    """
                    INSERT INTO shards(
                        path, row_count, target_count,
                        source_size, source_mtime_ns
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        relative,
                        rows,
                        targets,
                        before.st_size,
                        before.st_mtime_ns,
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise RuntimeError(
                f"duplicate arxiv_id detected while scanning {relative}"
            ) from error

        total_rows += rows
        target_rows += targets
        log(
            f"indexed shard {index}/{len(shards)}: {relative} "
            f"rows={rows:,} targets={targets:,}"
        )

    distinct_corpus_ids = conn.execute(
        "SELECT COUNT(DISTINCT corpus_id) AS n FROM targets"
    ).fetchone()["n"]
    with conn:
        set_meta(conn, "initialized", 1)
        set_meta(conn, "initialized_at", utc_now())
        set_meta(conn, "source_rows", total_rows)
        set_meta(conn, "target_rows", target_rows)
        set_meta(conn, "distinct_corpus_ids", distinct_corpus_ids)
        set_meta(conn, "fetch_complete", 0)
        set_meta(conn, "apply_complete", 0)
        set_meta(conn, "upload_complete", 0)
        conn.execute("DELETE FROM meta WHERE key = 'initializing'")
    log(
        f"local target index ready: rows={total_rows:,} "
        f"targets={target_rows:,} distinct_corpus_ids={distinct_corpus_ids:,}"
    )


def retry_after_seconds(headers, default: float) -> float:
    value = headers.get("Retry-After") if headers else None
    if value:
        try:
            return max(default, float(value))
        except ValueError:
            pass
    return default


def request_json_with_backoff(
    url: str,
    api_key: str | None,
    initial_backoff: float,
    max_backoff: float,
):
    delay = initial_backoff
    while True:
        headers = {"User-Agent": UA}
        if api_key:
            headers["x-api-key"] = api_key
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            preview = error.read(500).decode("utf-8", errors="replace")
            if error.code == 429:
                wait = retry_after_seconds(error.headers, delay)
                log(
                    f"dataset API rate limited; waiting {wait:.0f}s "
                    f"before retry"
                )
                time.sleep(wait)
                delay = min(max_backoff, delay * 2)
                continue
            if error.code in (408, 425, 500, 502, 503, 504):
                log(
                    f"dataset API HTTP {error.code}; waiting {delay:.0f}s "
                    f"before retry"
                )
                time.sleep(delay)
                delay = min(max_backoff, delay * 2)
                continue
            raise RuntimeError(
                f"dataset API HTTP {error.code}: {preview}"
            ) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            log(
                f"dataset API network error ({type(error).__name__}); "
                f"waiting {delay:.0f}s before retry"
            )
            time.sleep(delay)
            delay = min(max_backoff, delay * 2)


def load_dataset_info(args, api_key: str | None):
    if args.dataset_info_file:
        with open(args.dataset_info_file, encoding="utf-8") as handle:
            info = json.load(handle)
        release_id = str(info.get("release_id") or "sample")
        return release_id, info

    release_id = get_meta(args.conn, "release_id")
    if not release_id:
        latest = request_json_with_backoff(
            LATEST_RELEASE_URL,
            None,
            args.api_backoff,
            args.api_max_backoff,
        )
        release_id = str(latest["release_id"])
    info = request_json_with_backoff(
        DATASET_URL.format(release_id=release_id),
        api_key,
        args.api_backoff,
        args.api_max_backoff,
    )
    return release_id, info


def file_key(url: str, ordinal: int) -> str:
    path = urllib.parse.urlparse(url).path
    name = os.path.basename(path)
    return name or f"papers-part-{ordinal:03d}.jsonl.gz"


def register_dataset_files(
    conn: sqlite3.Connection,
    release_id: str,
    urls: list[str],
) -> None:
    existing_release = get_meta(conn, "release_id")
    if existing_release and existing_release != release_id:
        raise SystemExit(
            f"State is pinned to release {existing_release}, but API returned "
            f"{release_id}; use --reset to start a new snapshot."
        )
    if not urls:
        raise RuntimeError("papers dataset returned no download files")

    keys = []
    for ordinal, url in enumerate(urls):
        key = file_key(url, ordinal)
        if key in keys:
            key = f"{ordinal:03d}-{key}"
        keys.append(key)

    existing_keys = {
        row["file_key"] for row in conn.execute("SELECT file_key FROM files")
    }
    if existing_keys and existing_keys != set(keys):
        raise RuntimeError(
            f"file list changed within pinned release {release_id}: "
            f"state={len(existing_keys)}, API={len(keys)}"
        )

    with conn:
        set_meta(conn, "release_id", release_id)
        set_meta(conn, "file_count", len(keys))
        for ordinal, key in enumerate(keys):
            conn.execute(
                """
                INSERT INTO files(file_key, ordinal)
                VALUES (?, ?)
                ON CONFLICT(file_key) DO UPDATE SET ordinal = excluded.ordinal
                """,
                (key, ordinal),
            )
    log(f"pinned papers dataset release {release_id}: {len(keys)} gzip shards")


def urls_by_key(urls: list[str]) -> dict[str, str]:
    result = {}
    seen = set()
    for ordinal, url in enumerate(urls):
        key = file_key(url, ordinal)
        if key in seen:
            key = f"{ordinal:03d}-{key}"
        seen.add(key)
        result[key] = url
    return result


def curl_config_url(url: str) -> str:
    return url.replace("\\", "\\\\").replace('"', '\\"')


def download_one(url: str, part_path: str, gzip_path: str) -> int:
    if os.path.exists(gzip_path):
        return os.path.getsize(gzip_path)

    command = [
        "curl",
        "--fail",
        "--location",
        "--silent",
        "--show-error",
        "--connect-timeout",
        "30",
        "--speed-limit",
        "10240",
        "--speed-time",
        "300",
        "--retry",
        "8",
        "--retry-all-errors",
        "--retry-delay",
        "30",
        "--continue-at",
        "-",
        "--output",
        part_path,
        "--config",
        "-",
    ]
    config = f'url = "{curl_config_url(url)}"\n'
    result = subprocess.run(
        command,
        input=config.encode("utf-8"),
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl download failed with exit code {result.returncode}")
    os.replace(part_path, gzip_path)
    return os.path.getsize(gzip_path)


def upsert_counts(
    conn: sqlite3.Connection,
    updates: list[tuple],
) -> None:
    if not updates:
        return
    with conn:
        conn.executemany(
            """
            INSERT INTO counts(
                corpus_id, citation_count, influential_citation_count,
                release_id, matched_at
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(corpus_id) DO UPDATE SET
                citation_count = excluded.citation_count,
                influential_citation_count =
                    excluded.influential_citation_count,
                release_id = excluded.release_id,
                matched_at = excluded.matched_at
            """,
            updates,
        )


def match_totals(conn: sqlite3.Connection) -> tuple[int, int]:
    unique_matches = conn.execute(
        "SELECT COUNT(*) AS n FROM counts"
    ).fetchone()["n"]
    matched_targets = conn.execute(
        """
        SELECT COUNT(*) AS n
        FROM targets AS t
        JOIN counts AS c ON c.corpus_id = t.corpus_id
        """
    ).fetchone()["n"]
    return unique_matches, matched_targets


def process_gzip(
    conn: sqlite3.Connection,
    gzip_path: str,
    target_ids: set[int],
    release_id: str,
    progress_every: int,
    max_malformed_target_lines: int,
) -> tuple[int, int, int, int]:
    records = 0
    matched_lines = 0
    metric_lines = 0
    malformed_target_lines = 0
    updates = []
    started = time.monotonic()
    matched_at = utc_now()

    with gzip.open(gzip_path, "rb") as handle:
        for line in handle:
            if not line.strip():
                continue
            records += 1
            if progress_every and records % progress_every == 0:
                elapsed = max(time.monotonic() - started, 0.001)
                log(
                    f"streamed {records:,} records, matched "
                    f"{matched_lines:,} ({records / elapsed:,.0f} rows/s)"
                )
            match = CORPUS_ID_PATTERN.search(line)
            if not match:
                continue
            corpus_id = int(match.group(1))
            if corpus_id not in target_ids:
                continue

            try:
                record = json_loads(line)
            except Exception as error:
                malformed_target_lines += 1
                log(
                    f"malformed target record for corpusId={corpus_id}: "
                    f"{type(error).__name__}"
                )
                if malformed_target_lines > max_malformed_target_lines:
                    raise RuntimeError(
                        f"more than {max_malformed_target_lines} malformed "
                        f"target records in one gzip"
                    ) from error
                continue

            matched_lines += 1
            citation_key = (
                "citationcount"
                if "citationcount" in record
                else "citationCount"
                if "citationCount" in record
                else None
            )
            influential_key = (
                "influentialcitationcount"
                if "influentialcitationcount" in record
                else "influentialCitationCount"
                if "influentialCitationCount" in record
                else None
            )
            citation_count = (
                int_or_none(record.get(citation_key)) if citation_key else None
            )
            influential_count = (
                int_or_none(record.get(influential_key))
                if influential_key
                else None
            )
            if (
                citation_key is None
                or influential_key is None
                or citation_count is None
                or influential_count is None
            ):
                continue

            metric_lines += 1
            updates.append(
                (
                    corpus_id,
                    citation_count,
                    influential_count,
                    release_id,
                    matched_at,
                )
            )
            if len(updates) >= 10000:
                upsert_counts(conn, updates)
                updates.clear()

    upsert_counts(conn, updates)
    if matched_lines and not metric_lines:
        raise RuntimeError(
            "matched papers dataset records contain neither complete "
            "citationcount nor influentialcitationcount metrics"
        )
    return (
        records,
        matched_lines,
        metric_lines,
        malformed_target_lines,
    )


def cleanup_current_file(
    conn: sqlite3.Connection,
    work_dir: str,
) -> None:
    key_path = os.path.join(work_dir, "current.key")
    if not os.path.exists(key_path):
        return
    with open(key_path, encoding="utf-8") as handle:
        key = handle.read().strip()
    row = conn.execute(
        "SELECT status FROM files WHERE file_key = ?", (key,)
    ).fetchone()
    if row and row["status"] == "done":
        for name in ("current.jsonl.gz", "current.jsonl.gz.part", "current.key"):
            path = os.path.join(work_dir, name)
            if os.path.exists(path):
                os.remove(path)


def prepare_current_file(work_dir: str, key: str) -> tuple[str, str]:
    os.makedirs(work_dir, exist_ok=True)
    key_path = os.path.join(work_dir, "current.key")
    current_key = ""
    if os.path.exists(key_path):
        with open(key_path, encoding="utf-8") as handle:
            current_key = handle.read().strip()
    if current_key and current_key != key:
        for name in ("current.jsonl.gz", "current.jsonl.gz.part", "current.key"):
            path = os.path.join(work_dir, name)
            if os.path.exists(path):
                os.remove(path)
    with open(key_path, "w", encoding="utf-8") as handle:
        handle.write(key + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return (
        os.path.join(work_dir, "current.jsonl.gz.part"),
        os.path.join(work_dir, "current.jsonl.gz"),
    )


def run_fetch(args) -> int:
    conn = connect(args.db)
    args.conn = conn
    try:
        initialize_state(conn, args.root)
        if get_meta(conn, "upload_complete") == "1":
            raise SystemExit(
                "This dataset citation campaign is already uploaded; "
                "use --reset for a new release."
            )
        if get_meta(conn, "fetch_complete") == "1":
            log("all dataset gzip shards are already processed")
            return 0

        api_key = None if args.dataset_info_file else read_api_key()
        release_id, info = load_dataset_info(args, api_key)
        urls = list(info.get("files") or [])
        register_dataset_files(conn, release_id, urls)
        current_urls = urls_by_key(urls)
        target_ids = {
            row["corpus_id"]
            for row in conn.execute("SELECT DISTINCT corpus_id FROM targets")
        }
        log(f"loaded {len(target_ids):,} target corpus IDs into memory")

        cleanup_current_file(conn, args.work_dir)
        completed_this_run = 0
        while True:
            file_row = conn.execute(
                """
                SELECT *
                FROM files
                WHERE status != 'done'
                ORDER BY ordinal
                LIMIT 1
                """
            ).fetchone()
            if not file_row:
                break
            if args.limit_files and completed_this_run >= args.limit_files:
                break

            url = current_urls.get(file_row["file_key"])
            if not url:
                raise RuntimeError(f"dataset metadata omitted {file_row['file_key']}")

            part_path, gzip_path = prepare_current_file(
                args.work_dir, file_row["file_key"]
            )
            with conn:
                conn.execute(
                    """
                    UPDATE files
                    SET status = 'downloading', last_error = NULL
                    WHERE file_key = ?
                    """,
                    (file_row["file_key"],),
                )
            log(
                f"downloading gzip {file_row['ordinal'] + 1}/"
                f"{get_meta(conn, 'file_count')}: {file_row['file_key']}"
            )
            try:
                download_bytes = download_one(url, part_path, gzip_path)
                log(
                    f"processing {file_row['file_key']} "
                    f"({download_bytes / (1024 ** 3):.2f} GiB compressed)"
                )
                with conn:
                    conn.execute(
                        "UPDATE files SET status = 'processing' WHERE file_key = ?",
                        (file_row["file_key"],),
                    )
                (
                    records,
                    matched_lines,
                    metric_lines,
                    malformed_target_lines,
                ) = process_gzip(
                    conn,
                    gzip_path,
                    target_ids,
                    release_id,
                    args.progress_every,
                    args.max_malformed_target_lines,
                )
                with conn:
                    conn.execute(
                        """
                        UPDATE files
                        SET status = 'done',
                        attempts = attempts + 1,
                        record_count = ?,
                        matched_lines = ?,
                        metric_lines = ?,
                        malformed_target_lines = ?,
                        download_bytes = ?,
                        processed_at = ?,
                        last_error = NULL
                        WHERE file_key = ?
                        """,
                        (
                            records,
                            matched_lines,
                            metric_lines,
                            malformed_target_lines,
                            download_bytes,
                            utc_now(),
                            file_row["file_key"],
                        ),
                    )
                os.remove(gzip_path)
                key_path = os.path.join(args.work_dir, "current.key")
                if os.path.exists(key_path):
                    os.remove(key_path)
                files_done = conn.execute(
                    "SELECT COUNT(*) AS n FROM files WHERE status = 'done'"
                ).fetchone()["n"]
                file_count = int(get_meta(conn, "file_count"))
                unique_matches, matched_targets = match_totals(conn)
                completion = files_done / file_count if file_count else 0
                log(
                    f"completed and deleted {file_row['file_key']}: "
                    f"records={records:,} matched_lines={matched_lines:,} "
                    f"complete_metrics={metric_lines:,}; "
                    f"cumulative_corpus_matches={unique_matches:,} "
                    f"cumulative_target_rows={matched_targets:,}; "
                    f"gzip_progress={files_done}/{file_count} "
                    f"({completion:.2%})"
                )
                completed_this_run += 1
            except Exception as error:
                for name in (
                    "current.jsonl.gz",
                    "current.jsonl.gz.part",
                    "current.key",
                ):
                    path = os.path.join(args.work_dir, name)
                    if os.path.exists(path):
                        os.remove(path)
                with conn:
                    conn.execute(
                        """
                        UPDATE files
                        SET status = 'error',
                            attempts = attempts + 1,
                            last_error = ?
                        WHERE file_key = ?
                        """,
                        (
                            f"{type(error).__name__}: {error}",
                            file_row["file_key"],
                        ),
                    )
                raise

        remaining = conn.execute(
            "SELECT COUNT(*) AS n FROM files WHERE status != 'done'"
        ).fetchone()["n"]
        if remaining == 0:
            with conn:
                set_meta(conn, "fetch_complete", 1)
                set_meta(conn, "fetch_completed_at", utc_now())
            unique_matches, matched_targets = match_totals(conn)
            log(
                f"dataset fetch complete: unique corpus matches="
                f"{unique_matches:,}, local target rows matched="
                f"{matched_targets:,}"
            )
        else:
            log(f"dataset fetch paused with {remaining} gzip shards remaining")
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
                f"Refusing to apply: source shard changed after dataset "
                f"snapshot: {row['path']}"
            )


def rewrite_shard(
    conn: sqlite3.Connection,
    root: str,
    shard_row: sqlite3.Row,
    release_id: str,
    refreshed_at: str,
) -> int:
    relative = shard_row["path"]
    path = os.path.join(root, relative)
    updates = {
        row["arxiv_id"]: (
            row["citation_count"],
            row["influential_citation_count"],
        )
        for row in conn.execute(
            """
            SELECT t.arxiv_id, c.citation_count,
                   c.influential_citation_count
            FROM targets AS t
            JOIN counts AS c ON c.corpus_id = t.corpus_id
            WHERE t.shard = ?
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
    temporary = path + ".citation-dataset-refresh.tmp"
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
                update = updates.get(record.get("arxiv_id"))
                if update is not None:
                    citation_count, influential_count = update
                    if citation_count is not None:
                        record["citationCount"] = citation_count
                    if influential_count is not None:
                        record["influentialCitationCount"] = influential_count
                    record["citation_refreshed_at"] = refreshed_at
                    record["citation_source_release"] = release_id
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
                f"{relative}: matched {matched:,}/{len(updates):,} updates"
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
        if get_meta(conn, "fetch_complete") != "1":
            raise SystemExit("Cannot apply before every dataset gzip is complete")
        if get_meta(conn, "apply_complete") == "1":
            if (
                get_meta(conn, "upload_complete") != "1"
                and not os.path.exists(args.marker)
            ):
                raise SystemExit(
                    "Apply is complete but the upload marker is missing"
                )
            log("dataset citation updates are already applied")
            return 0

        target_rows = int(get_meta(conn, "target_rows", 0))
        matched_targets = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM targets AS t
            JOIN counts AS c ON c.corpus_id = t.corpus_id
            """
        ).fetchone()["n"]
        coverage = matched_targets / target_rows if target_rows else 0.0
        if not args.force and coverage < args.min_coverage:
            raise SystemExit(
                f"Dataset coverage {coverage:.2%} is below "
                f"{args.min_coverage:.2%} "
                f"({matched_targets:,}/{target_rows:,})"
            )

        verify_unapplied_sources(conn, args.root)
        if not os.path.exists(args.marker):
            with open(args.marker, "x", encoding="utf-8") as marker:
                marker.write(utc_now() + "\n")
                marker.flush()
                os.fsync(marker.fileno())
            time.sleep(1.1)

        release_id = get_meta(conn, "release_id")
        refreshed_at = utc_now()
        shard_rows = conn.execute(
            "SELECT * FROM shards WHERE applied != 1 ORDER BY path"
        ).fetchall()
        total_updated = 0
        for index, shard_row in enumerate(shard_rows, 1):
            updated = rewrite_shard(
                conn,
                args.root,
                shard_row,
                release_id,
                refreshed_at,
            )
            total_updated += updated
            log(
                f"applied shard {index}/{len(shard_rows)}: "
                f"{shard_row['path']} updated={updated:,}"
            )

        applied_rows = conn.execute(
            "SELECT COALESCE(SUM(updated_rows), 0) AS n FROM shards"
        ).fetchone()["n"]
        if applied_rows != matched_targets:
            raise SystemExit(
                f"Applied-row validation failed: "
                f"{applied_rows:,} != {matched_targets:,}"
            )
        with conn:
            set_meta(conn, "apply_complete", 1)
            set_meta(conn, "applied_at", utc_now())
            set_meta(conn, "applied_rows", applied_rows)
            set_meta(conn, "coverage", f"{coverage:.12f}")
        log(
            f"dataset apply complete: updated={applied_rows:,} "
            f"coverage={coverage:.2%}"
        )
        return 0
    finally:
        conn.close()


def print_status(args) -> int:
    if not os.path.exists(args.db):
        print(f"state_db={args.db} (missing)")
        return 1
    conn = connect(args.db)
    try:
        print(f"state_db={args.db}")
        for key in (
            "release_id",
            "source_rows",
            "target_rows",
            "distinct_corpus_ids",
            "file_count",
            "fetch_complete",
            "fetch_completed_at",
            "apply_complete",
            "applied_rows",
            "coverage",
            "upload_complete",
            "uploaded_at",
            "hf_commit",
        ):
            value = get_meta(conn, key)
            if value is not None:
                print(f"{key}={value}")
        file_counts = {
            row["status"]: row["n"]
            for row in conn.execute(
                "SELECT status, COUNT(*) AS n FROM files GROUP BY status"
            )
        }
        for status_name in ("pending", "downloading", "processing", "error", "done"):
            print(f"files_{status_name}={file_counts.get(status_name, 0)}")
        unique_matches = conn.execute(
            "SELECT COUNT(*) AS n FROM counts"
        ).fetchone()["n"]
        matched_targets = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM targets AS t
            JOIN counts AS c ON c.corpus_id = t.corpus_id
            """
        ).fetchone()["n"]
        print(f"unique_corpus_matches={unique_matches}")
        print(f"matched_target_rows={matched_targets}")
        current_gzip = os.path.join(args.work_dir, "current.jsonl.gz")
        current_part = current_gzip + ".part"
        if os.path.exists(current_gzip):
            print(f"current_gzip_bytes={os.path.getsize(current_gzip)}")
        elif os.path.exists(current_part):
            print(f"current_partial_bytes={os.path.getsize(current_part)}")
        else:
            print("current_download_bytes=0")
        return 0
    finally:
        conn.close()


def mark_uploaded(args) -> int:
    conn = connect(args.db)
    try:
        if get_meta(conn, "apply_complete") != "1":
            raise SystemExit("Cannot mark upload complete before apply")
        with conn:
            set_meta(conn, "upload_complete", 1)
            set_meta(conn, "uploaded_at", utc_now())
            if args.hf_commit:
                set_meta(conn, "hf_commit", args.hf_commit)
        log("dataset citation upload marked complete")
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
        )
        return 0 if active else 1
    finally:
        conn.close()


def clear_work_dir(root: str, work_dir: str) -> None:
    root_real = os.path.realpath(root)
    work_real = os.path.realpath(work_dir)
    if (
        work_real == root_real
        or os.path.commonpath((root_real, work_real)) != root_real
    ):
        raise SystemExit(
            f"Refusing to clear unsafe work directory: {work_dir}"
        )
    if not os.path.exists(work_dir):
        return
    allowed = {
        "current.key",
        "current.jsonl.gz",
        "current.jsonl.gz.part",
    }
    entries = set(os.listdir(work_dir))
    unexpected = entries - allowed
    if unexpected:
        raise SystemExit(
            f"Refusing to clear work directory with unexpected entries: "
            f"{sorted(unexpected)}"
        )
    for name in entries:
        path = os.path.join(work_dir, name)
        if not os.path.isfile(path):
            raise SystemExit(f"Refusing to remove non-file work entry: {path}")
        os.remove(path)
    os.rmdir(work_dir)


def reset_state(
    db_path: str,
    work_dir: str,
    marker: str,
    root: str,
) -> None:
    clear_work_dir(root, work_dir)
    for path in (db_path, db_path + "-wal", db_path + "-shm", marker):
        if os.path.exists(path):
            os.remove(path)
    log("removed prior dataset citation refresh state")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--work-dir", default=DEFAULT_WORK)
    parser.add_argument("--marker", default=DEFAULT_MARKER)
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser("fetch")
    fetch.add_argument("--reset", action="store_true")
    fetch.add_argument("--dataset-info-file")
    fetch.add_argument("--limit-files", type=int, default=0)
    fetch.add_argument("--progress-every", type=int, default=1000000)
    fetch.add_argument("--max-malformed-target-lines", type=int, default=10)
    fetch.add_argument("--api-backoff", type=float, default=3600.0)
    fetch.add_argument("--api-max-backoff", type=float, default=21600.0)

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--min-coverage", type=float, default=0.98)
    apply_parser.add_argument("--force", action="store_true")

    subparsers.add_parser("status")
    uploaded = subparsers.add_parser("mark-uploaded")
    uploaded.add_argument("--hf-commit")
    subparsers.add_parser("is-uploaded")
    subparsers.add_parser("is-active")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.root = os.path.abspath(os.path.expanduser(args.root))
    args.db = os.path.abspath(os.path.expanduser(args.db))
    args.work_dir = os.path.abspath(os.path.expanduser(args.work_dir))
    args.marker = os.path.abspath(os.path.expanduser(args.marker))

    if args.command == "fetch":
        if args.reset:
            reset_state(args.db, args.work_dir, args.marker, args.root)
        return run_fetch(args)
    if args.command == "apply":
        return run_apply(args)
    if args.command == "status":
        return print_status(args)
    if args.command == "mark-uploaded":
        return mark_uploaded(args)
    if args.command == "is-uploaded":
        return is_uploaded(args)
    if args.command == "is-active":
        return is_active(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    sys.exit(main())
