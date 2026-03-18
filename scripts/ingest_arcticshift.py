\
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reddit_dr_harness.ingest import (
    load_comments,
    load_submissions,
    write_sqlite,
    write_threads_artifacts,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest Arctic Shift-style Reddit exports, persist them to SQLite, and reconstruct per-thread artifacts."
    )
    parser.add_argument("--submissions", required=True, help="Path to submissions JSONL/JSON/ZST export.")
    parser.add_argument("--comments", required=True, help="Path to comments JSONL/JSON/ZST export.")
    parser.add_argument("--sqlite", required=True, help="SQLite output path.")
    parser.add_argument("--threads-jsonl", required=True, help="Thread JSONL output path.")
    parser.add_argument("--threads-md-dir", required=True, help="Directory for per-thread markdown files.")
    parser.add_argument("--manifest", required=True, help="CSV manifest output path.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    submissions = load_submissions(args.submissions)
    comments = load_comments(args.comments)

    if not submissions:
        print("No submissions could be parsed from the input file.", file=sys.stderr)
        return 1

    write_sqlite(submissions, comments, args.sqlite)
    summary = write_threads_artifacts(
        submissions,
        comments,
        threads_jsonl_path=args.threads_jsonl,
        threads_md_dir=args.threads_md_dir,
        manifest_path=args.manifest,
    )

    print(
        f"Ingest complete: {summary['submissions']} submissions, "
        f"{summary['comments']} comments parsed, "
        f"{summary['thread_comments']} linked into {summary['threads']} threads, "
        f"{summary['orphan_comments']} comments preserved in {summary['orphan_threads']} orphan threads."
    )
    print(f"SQLite: {args.sqlite}")
    print(f"Threads JSONL: {args.threads_jsonl}")
    print(f"Manifest: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
