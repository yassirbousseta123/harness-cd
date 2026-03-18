from __future__ import annotations

import json
from pathlib import Path

from reddit_dr_harness.avatar_state import build_avatar_slice
from reddit_dr_harness.ingest import (
    CommentRecord,
    SubmissionRecord,
    dedupe_comments,
    dedupe_submissions,
    load_comments,
    load_submissions,
    write_threads_artifacts,
)


def test_build_avatar_slice_scores_normal_and_orphan_threads(tmp_path: Path) -> None:
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

    threads = []
    for path in [threads_jsonl, tmp_path / "orphan_threads.jsonl"]:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                threads.append(json.loads(line))

    config = {
        "avatar_id": "test_cluster",
        "label": "Test Cluster",
        "min_core_score": 2.0,
        "min_core_states": 2,
        "core_states": [
            {"id": "stress_loop", "weight": 1.0, "patterns": [r"\bstress\b"]},
            {"id": "sleep_spike", "weight": 1.0, "patterns": [r"\bbedtime\b", r"\bslept\b"]},
            {"id": "daytime_function", "weight": 1.0, "patterns": [r"\bwork\b"]},
            {"id": "missing_post_context", "weight": 1.0, "patterns": [r"\bpost is gone\b"]},
            {"id": "context_matters", "weight": 1.0, "patterns": [r"\bstill matters\b"]},
        ],
        "adjacent_states": [
            {"id": "kids", "weight": 1.0, "patterns": [r"\bkids\b"]},
        ],
    }

    matched_threads, report = build_avatar_slice(threads, config)

    assert {thread["thread_id"] for thread in matched_threads} == {"t3_abc123", "t3_def456", "t3_ghost999"}
    orphan = next(thread for thread in matched_threads if thread["thread_id"] == "t3_ghost999")
    assert orphan["slice_metadata"]["source_kind"] == "orphan"
    assert report["matched_threads"] == 3
    assert "stress_loop" in report["core_state_counts"]
    assert "kids" in report["adjacent_state_counts"]


def test_dedupe_helpers_keep_richer_records() -> None:
    submissions = [
        SubmissionRecord(
            id="abc123",
            subreddit="tinnitus",
            title="Short",
            selftext="",
            author=None,
            created_utc=1.0,
            score=None,
            num_comments=None,
            permalink=None,
            url=None,
            over_18=None,
            raw={"id": "abc123"},
        ),
        SubmissionRecord(
            id="abc123",
            subreddit="tinnitus",
            title="Longer title",
            selftext="More complete body",
            author="author",
            created_utc=1.0,
            score=5,
            num_comments=2,
            permalink="/r/tinnitus/comments/abc123",
            url="https://reddit.example/abc123",
            over_18=False,
            raw={"id": "abc123", "extra": True},
        ),
    ]
    comments = [
        CommentRecord(
            id="c1",
            subreddit="tinnitus",
            link_id="abc123",
            parent_id="t3_abc123",
            parent_kind="t3",
            parent_comment_id=None,
            parent_submission_id="abc123",
            body="short",
            author=None,
            created_utc=1.0,
            score=None,
            permalink=None,
            raw={"id": "c1"},
        ),
        CommentRecord(
            id="c1",
            subreddit="tinnitus",
            link_id="abc123",
            parent_id="t3_abc123",
            parent_kind="t3",
            parent_comment_id=None,
            parent_submission_id="abc123",
            body="much richer comment body",
            author="writer",
            created_utc=1.0,
            score=3,
            permalink="/r/tinnitus/comments/abc123/_/c1/",
            raw={"id": "c1", "extra": True},
        ),
    ]

    deduped_submissions = dedupe_submissions(submissions)
    deduped_comments = dedupe_comments(comments)

    assert len(deduped_submissions) == 1
    assert deduped_submissions[0].selftext == "More complete body"
    assert len(deduped_comments) == 1
    assert deduped_comments[0].body == "much richer comment body"
