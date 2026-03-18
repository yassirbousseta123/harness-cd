from __future__ import annotations

from pathlib import Path

from reddit_dr_harness.corpus_metrics import summarize_current_corpus
from reddit_dr_harness.ingest import load_comments, load_submissions, write_sqlite, write_threads_artifacts


def test_summarize_current_corpus_reads_existing_artifacts(tmp_path: Path) -> None:
    submissions = load_submissions("tests/fixtures/submissions.jsonl")
    comments = load_comments("tests/fixtures/comments.jsonl")

    sqlite_path = tmp_path / "reddit.db"
    manifest_path = tmp_path / "thread_index.csv"
    write_sqlite(submissions, comments, sqlite_path)
    summary = write_threads_artifacts(
        submissions,
        comments,
        threads_jsonl_path=tmp_path / "threads.jsonl",
        threads_md_dir=tmp_path / "md",
        manifest_path=manifest_path,
    )

    assert summarize_current_corpus(sqlite_path=sqlite_path, manifest_path=manifest_path) == summary
