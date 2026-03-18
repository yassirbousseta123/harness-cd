\
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reddit_dr_harness.ingest import load_threads_jsonl, render_thread_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bundle reconstructed thread markdown into larger Codex-friendly research packs."
    )
    parser.add_argument("--threads", required=True, help="Input threads JSONL.")
    parser.add_argument("--out-dir", required=True, help="Directory for markdown packs.")
    parser.add_argument("--manifest", required=True, help="CSV manifest path for generated packs.")
    parser.add_argument("--max-threads", type=int, default=25, help="Maximum threads per pack.")
    parser.add_argument("--max-chars", type=int, default=120000, help="Maximum characters per pack.")
    parser.add_argument(
        "--max-comments-per-thread",
        type=int,
        default=80,
        help="Maximum reconstructed comments to include from any one thread in a pack.",
    )
    return parser


def build_packs(
    threads: list[dict[str, object]],
    *,
    out_dir: str | Path,
    manifest_path: str | Path,
    max_threads: int = 25,
    max_chars: int = 120000,
    max_comments_per_thread: int = 80,
) -> list[dict[str, object]]:
    out_dir_path = Path(out_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)
    for stale_pack in sorted(out_dir_path.glob("pack_*.md")):
        stale_pack.unlink()

    manifest_file = Path(manifest_path)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)

    packs: list[dict[str, object]] = []
    current_threads: list[dict[str, object]] = []
    current_text_parts: list[str] = []
    current_chars = 0

    def flush_pack() -> None:
        nonlocal current_threads, current_text_parts, current_chars
        if not current_threads:
            return
        pack_index = len(packs) + 1
        pack_name = f"pack_{pack_index:03d}.md"
        pack_path = out_dir_path / pack_name
        header = [
            f"# Research Pack {pack_index:03d}",
            "",
            f"- threads: {len(current_threads)}",
            f"- chars: {current_chars}",
            "",
        ]
        pack_text = "\n".join(header + current_text_parts).strip() + "\n"
        pack_path.write_text(pack_text, encoding="utf-8")
        packs.append(
            {
                "pack_id": f"pack_{pack_index:03d}",
                "pack_path": str(pack_path),
                "thread_count": len(current_threads),
                "char_count": len(pack_text),
                "thread_ids": ",".join(str(thread["thread_id"]) for thread in current_threads),
            }
        )
        current_threads = []
        current_text_parts = []
        current_chars = 0

    for thread in threads:
        rendered = render_thread_markdown(thread, max_comments=max_comments_per_thread)
        candidate_chars = current_chars + len(rendered)
        if current_threads and (len(current_threads) >= max_threads or candidate_chars > max_chars):
            flush_pack()
        current_threads.append(thread)
        current_text_parts.append(rendered)
        current_text_parts.append("\n---\n")
        current_chars += len(rendered)

    flush_pack()

    with manifest_file.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["pack_id", "pack_path", "thread_count", "char_count", "thread_ids"],
        )
        writer.writeheader()
        writer.writerows(packs)

    return packs


def main() -> int:
    args = build_parser().parse_args()
    threads = load_threads_jsonl(args.threads)
    packs = build_packs(
        threads,
        out_dir=args.out_dir,
        manifest_path=args.manifest,
        max_threads=args.max_threads,
        max_chars=args.max_chars,
        max_comments_per_thread=args.max_comments_per_thread,
    )

    print(f"Built {len(packs)} pack(s) at {args.out_dir}")
    print(f"Manifest: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
