from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


def count_manifest_rows(path: str | Path) -> int:
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def sum_manifest_column(path: str | Path, fieldname: str) -> int:
    total = 0
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            value = row.get(fieldname) or "0"
            total += int(float(value))
    return total


def sqlite_table_count(sqlite_path: str | Path, table_name: str) -> int:
    conn = sqlite3.connect(Path(sqlite_path))
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
    finally:
        conn.close()


def summarize_current_corpus(
    *,
    sqlite_path: str | Path,
    manifest_path: str | Path,
) -> dict[str, int]:
    manifest = Path(manifest_path)
    orphan_manifest = manifest.with_name("orphan_thread_index.csv")
    return {
        "threads": count_manifest_rows(manifest),
        "comments": sqlite_table_count(sqlite_path, "comments"),
        "thread_comments": sum_manifest_column(manifest, "comment_count_reconstructed"),
        "orphan_threads": count_manifest_rows(orphan_manifest),
        "orphan_comments": sum_manifest_column(orphan_manifest, "comment_count_reconstructed"),
        "submissions": sqlite_table_count(sqlite_path, "submissions"),
    }
