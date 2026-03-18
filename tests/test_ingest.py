\
from __future__ import annotations

import csv
import json
from pathlib import Path

from reddit_dr_harness.ingest import (
    load_comments,
    load_submissions,
    write_sqlite,
    write_threads_artifacts,
)


def test_ingest_reconstructs_threads_and_marks_orphans(tmp_path: Path) -> None:
    submissions = load_submissions("tests/fixtures/submissions.jsonl")
    comments = load_comments("tests/fixtures/comments.jsonl")

    sqlite_path = tmp_path / "reddit.db"
    threads_jsonl = tmp_path / "threads.jsonl"
    orphan_threads_jsonl = tmp_path / "orphan_threads.jsonl"
    threads_md_dir = tmp_path / "md"
    orphan_threads_md_dir = tmp_path / "orphans_md"
    manifest_path = tmp_path / "thread_index.csv"
    orphan_manifest_path = tmp_path / "orphan_thread_index.csv"

    write_sqlite(submissions, comments, sqlite_path)
    summary = write_threads_artifacts(
        submissions,
        comments,
        threads_jsonl_path=threads_jsonl,
        threads_md_dir=threads_md_dir,
        manifest_path=manifest_path,
    )

    assert summary["threads"] == 2
    assert summary["thread_comments"] == 5
    assert summary["orphan_threads"] == 1
    assert summary["orphan_comments"] == 1
    assert sqlite_path.exists()
    assert threads_jsonl.exists()
    assert orphan_threads_jsonl.exists()
    assert manifest_path.exists()
    assert orphan_manifest_path.exists()
    assert orphan_threads_md_dir.exists()

    threads = [json.loads(line) for line in threads_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert {thread["thread_id"] for thread in threads} == {"t3_abc123", "t3_def456"}

    abc = next(thread for thread in threads if thread["thread_id"] == "t3_abc123")
    assert abc["stats"]["comment_count"] == 3
    assert abc["stats"]["orphaned_root_count"] == 1

    c1 = next(comment for comment in abc["comments"] if comment["id"] == "c1")
    c2 = next(comment for comment in abc["comments"] if comment["id"] == "c2")
    c3 = next(comment for comment in abc["comments"] if comment["id"] == "c3")

    assert c1["depth"] == 0
    assert c2["depth"] == 1
    assert c3["depth"] == 0
    assert c3["orphaned_parent_comment_id"] == "missing_parent"

    manifest_rows = list(csv.DictReader(manifest_path.open("r", encoding="utf-8")))
    assert len(manifest_rows) == 2
    assert manifest_rows[0]["markdown_path"].endswith(".md")

    orphan_threads = [json.loads(line) for line in orphan_threads_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(orphan_threads) == 1
    orphan = orphan_threads[0]
    assert orphan["thread_id"] == "t3_ghost999"
    assert orphan["missing_submission"] is True
    assert orphan["comments"][0]["id"] == "z1"

    orphan_manifest_rows = list(csv.DictReader(orphan_manifest_path.open("r", encoding="utf-8")))
    assert len(orphan_manifest_rows) == 1
    assert orphan_manifest_rows[0]["thread_id"] == "t3_ghost999"
