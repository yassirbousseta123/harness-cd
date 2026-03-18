\
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

from reddit_dr_harness.validate import validate_evidence_references


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate thread-level evidence references inside JSON or JSONL research outputs."
    )
    parser.add_argument("--json", required=True, help="JSON or JSONL output to inspect.")
    parser.add_argument("--thread-index", required=True, help="CSV thread manifest from ingest.")
    parser.add_argument("--threads", help="Optional threads JSONL used to validate quotes against source text.")
    parser.add_argument("--report", help="Optional path to write a JSON validation report.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any issues are found.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = validate_evidence_references(
        json_path=args.json,
        thread_index_path=args.thread_index,
        threads_path=args.threads,
    )
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    print(payload)
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(payload + "\n", encoding="utf-8")
    if args.strict and not report.get("valid", False):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
