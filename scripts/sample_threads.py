\
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reddit_dr_harness.ingest import extract_thread_text, load_threads_jsonl


def _parse_iso_date(value: str | None) -> float | None:
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Filter reconstructed thread JSONL files into smaller slices before packing or synthesis."
    )
    parser.add_argument("--threads", required=True, help="Input threads JSONL.")
    parser.add_argument("--out-jsonl", help="Optional output JSONL path for matching threads.")
    parser.add_argument("--out-csv", help="Optional output CSV manifest path for matching threads.")
    parser.add_argument("--subreddit", action="append", default=[], help="Allowed subreddit; repeatable.")
    parser.add_argument("--keyword", action="append", default=[], help="Keyword or regex to match; repeatable.")
    parser.add_argument("--after", help="Inclusive ISO date filter on submission created_utc.")
    parser.add_argument("--before", help="Exclusive ISO date filter on submission created_utc.")
    parser.add_argument("--min-comments", type=int, default=0, help="Minimum reconstructed comment count.")
    parser.add_argument("--min-score", type=int, default=-10**9, help="Minimum submission score.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum number of matches to keep after sorting.")
    parser.add_argument(
        "--sort-by",
        choices=["created_utc", "score", "comment_count"],
        default="comment_count",
        help="Sort key for results before applying --limit.",
    )
    parser.add_argument(
        "--descending",
        action="store_true",
        help="Sort descending instead of ascending (recommended for score/comment_count).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    threads = load_threads_jsonl(args.threads)
    after_ts = _parse_iso_date(args.after)
    before_ts = _parse_iso_date(args.before)
    keywords = [re.compile(pattern, re.IGNORECASE) for pattern in args.keyword]
    allowed_subreddits = {item.lower() for item in args.subreddit}

    matches: list[dict] = []
    for thread in threads:
        submission = thread.get("submission", {})
        created = submission.get("created_utc")
        if allowed_subreddits and str(thread.get("subreddit", "")).lower() not in allowed_subreddits:
            continue
        if after_ts is not None and (created is None or created < after_ts):
            continue
        if before_ts is not None and (created is None or created >= before_ts):
            continue
        if thread.get("stats", {}).get("comment_count", 0) < args.min_comments:
            continue
        if (submission.get("score") or 0) < args.min_score:
            continue
        if keywords:
            haystack = extract_thread_text(thread)
            if not any(pattern.search(haystack) for pattern in keywords):
                continue
        matches.append(thread)

    key_funcs = {
        "created_utc": lambda item: item.get("submission", {}).get("created_utc") or 0,
        "score": lambda item: item.get("submission", {}).get("score") or 0,
        "comment_count": lambda item: item.get("stats", {}).get("comment_count") or 0,
    }
    matches.sort(key=key_funcs[args.sort_by], reverse=args.descending)

    if args.limit and args.limit > 0:
        matches = matches[: args.limit]

    if args.out_jsonl:
        out_jsonl = Path(args.out_jsonl)
        out_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with out_jsonl.open("w", encoding="utf-8") as fh:
            for thread in matches:
                fh.write(json.dumps(thread, ensure_ascii=False) + "\n")

    if args.out_csv:
        out_csv = Path(args.out_csv)
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        with out_csv.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=[
                    "thread_id",
                    "submission_id",
                    "subreddit",
                    "created_utc",
                    "score",
                    "comment_count",
                    "title",
                ],
            )
            writer.writeheader()
            for thread in matches:
                submission = thread.get("submission", {})
                writer.writerow(
                    {
                        "thread_id": thread.get("thread_id"),
                        "submission_id": thread.get("submission_id"),
                        "subreddit": thread.get("subreddit"),
                        "created_utc": submission.get("created_utc"),
                        "score": submission.get("score"),
                        "comment_count": thread.get("stats", {}).get("comment_count"),
                        "title": submission.get("title"),
                    }
                )

    print(f"Matched {len(matches)} thread(s).")
    if args.out_jsonl:
        print(f"JSONL: {args.out_jsonl}")
    if args.out_csv:
        print(f"CSV: {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
