"""Deterministic utilities for turning Reddit exports into research corpora."""

from .ingest import (
    CommentRecord,
    SubmissionRecord,
    build_thread_record,
    comment_to_dict,
    dedupe_comments,
    dedupe_submissions,
    extract_thread_text,
    iter_json_records,
    load_comments,
    load_submissions,
    render_thread_markdown,
    submission_to_dict,
)
from .avatar_state import build_avatar_slice, load_avatar_config, load_threads_from_paths, score_thread, write_avatar_slice
from .quotes import extract_quote_candidates, quote_categories
from .validate import validate_evidence_references

__all__ = [
    "CommentRecord",
    "SubmissionRecord",
    "build_thread_record",
    "comment_to_dict",
    "dedupe_comments",
    "dedupe_submissions",
    "extract_thread_text",
    "iter_json_records",
    "load_comments",
    "load_submissions",
    "render_thread_markdown",
    "submission_to_dict",
    "build_avatar_slice",
    "load_avatar_config",
    "load_threads_from_paths",
    "score_thread",
    "write_avatar_slice",
    "extract_quote_candidates",
    "quote_categories",
    "validate_evidence_references",
]

__version__ = "0.1.0"
