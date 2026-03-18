\
from __future__ import annotations

import json
from pathlib import Path

from reddit_dr_harness.ingest import load_comments, load_submissions, write_threads_artifacts
from reddit_dr_harness.validate import validate_evidence_references


def test_validate_evidence_refs_checks_thread_ids_and_quotes(tmp_path: Path) -> None:
    submissions = load_submissions("tests/fixtures/submissions.jsonl")
    comments = load_comments("tests/fixtures/comments.jsonl")

    threads_jsonl = tmp_path / "threads.jsonl"
    manifest_path = tmp_path / "thread_index.csv"
    write_threads_artifacts(
        submissions,
        comments,
        threads_jsonl_path=threads_jsonl,
        threads_md_dir=tmp_path / "md",
        manifest_path=manifest_path,
    )

    valid_payload = {
        "avatar_explanation": {
            "summary": "Sleep-deprived tinnitus sufferers seeking routine relief.",
            "confidence": "medium",
            "evidence": [
                {
                    "thread_id": "t3_abc123",
                    "submission_id": "abc123",
                    "comment_id": None,
                    "subreddit": "tinnitus",
                    "quote": "I'm exhausted. It sounds like cicadas in a quiet room.",
                    "why_it_supports": "Shows both distress and vivid metaphor."
                }
            ],
        }
    }
    valid_json = tmp_path / "valid.json"
    valid_json.write_text(json.dumps(valid_payload), encoding="utf-8")

    report = validate_evidence_references(
        json_path=valid_json,
        thread_index_path=manifest_path,
        threads_path=threads_jsonl,
    )
    assert report["valid"] is True
    assert report["missing_thread_ids"] == []
    assert report["quote_mismatches"] == []

    invalid_payload = {
        "evidence": [
            {
                "thread_id": "t3_missing",
                "submission_id": "missing",
                "comment_id": None,
                "subreddit": "tinnitus",
                "quote": "does not exist",
                "why_it_supports": "Bad evidence"
            }
        ]
    }
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text(json.dumps(invalid_payload), encoding="utf-8")

    invalid_report = validate_evidence_references(
        json_path=invalid_json,
        thread_index_path=manifest_path,
        threads_path=threads_jsonl,
    )
    assert invalid_report["valid"] is False
    assert invalid_report["missing_thread_ids"]
