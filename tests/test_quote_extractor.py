\
from __future__ import annotations

import json
from pathlib import Path

from reddit_dr_harness.ingest import load_comments, load_submissions, write_threads_artifacts
from reddit_dr_harness.quotes import extract_quote_candidates


def test_quote_extractor_finds_expected_categories(tmp_path: Path) -> None:
    submissions = load_submissions("tests/fixtures/submissions.jsonl")
    comments = load_comments("tests/fixtures/comments.jsonl")

    threads_jsonl = tmp_path / "threads.jsonl"
    write_threads_artifacts(
        submissions,
        comments,
        threads_jsonl_path=threads_jsonl,
        threads_md_dir=tmp_path / "md",
        manifest_path=tmp_path / "thread_index.csv",
    )

    out_path = tmp_path / "quote_candidates.jsonl"
    records = extract_quote_candidates(threads_jsonl, out_path=out_path)

    assert out_path.exists()
    categories = {record["category"] for record in records}
    assert "pain_points" in categories
    assert "failures" in categories
    assert "victories" in categories
    assert "trigger_moments" in categories
    assert "visual_cues" in categories
    assert "desires" in categories
    assert any("cicadas" in record["quote"].lower() for record in records if record["category"] == "visual_cues")
    assert any(record["quote_strength"] >= 1.0 for record in records)


def test_quote_extractor_accepts_multiple_thread_files(tmp_path: Path) -> None:
    submissions = load_submissions("tests/fixtures/submissions.jsonl")
    comments = load_comments("tests/fixtures/comments.jsonl")

    threads_jsonl = tmp_path / "threads.jsonl"
    write_threads_artifacts(
        submissions,
        comments,
        threads_jsonl_path=threads_jsonl,
        threads_md_dir=tmp_path / "md",
        manifest_path=tmp_path / "thread_index.csv",
    )

    out_path = tmp_path / "quote_candidates_multi.jsonl"
    records = extract_quote_candidates(
        [threads_jsonl, tmp_path / "orphan_threads.jsonl"],
        out_path=out_path,
    )

    assert out_path.exists()
    assert any(record["thread_id"] == "t3_ghost999" for record in records)
