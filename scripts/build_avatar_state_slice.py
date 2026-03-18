#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reddit_dr_harness.avatar_state import build_avatar_slice, load_avatar_config, load_threads_from_paths, write_avatar_slice


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an avatar/state-cluster slice from canonical thread corpora."
    )
    parser.add_argument("--config", required=True, help="Avatar/state config JSON.")
    parser.add_argument("--threads", action="append", required=True, help="Input threads JSONL. Repeatable.")
    parser.add_argument("--out-threads", required=True, help="Output filtered threads JSONL.")
    parser.add_argument("--out-manifest", required=True, help="Output filtered manifest CSV.")
    parser.add_argument("--out-report", required=True, help="Output JSON report for state matches and near misses.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_avatar_config(args.config)
    threads = load_threads_from_paths(args.threads)
    matched_threads, report = build_avatar_slice(threads, config)
    write_avatar_slice(
        matched_threads,
        out_threads_path=args.out_threads,
        out_manifest_path=args.out_manifest,
    )
    report_path = Path(args.out_report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Avatar slice: {config['avatar_id']}")
    print(f"Threads scored: {report['total_threads_scored']}")
    print(f"Matched threads: {report['matched_threads']}")
    print(f"Manifest: {args.out_manifest}")
    print(f"Report: {args.out_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
