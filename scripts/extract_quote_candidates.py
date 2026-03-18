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

from reddit_dr_harness.quotes import extract_quote_candidates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heuristically extract quote candidates from reconstructed thread corpora."
    )
    parser.add_argument("--threads", action="append", required=True, help="Input threads JSONL. Repeatable.")
    parser.add_argument("--out", required=True, help="Output JSONL for quote candidates.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    items = extract_quote_candidates(args.threads, out_path=args.out)
    print(f"Wrote {len(items)} quote candidate records to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
