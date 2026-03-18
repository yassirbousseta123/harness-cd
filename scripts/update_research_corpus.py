#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reddit_dr_harness.ingest import (
    dedupe_comments,
    dedupe_submissions,
    load_comments,
    load_submissions,
    write_sqlite,
    write_threads_artifacts,
)

PAIR_SUFFIXES = {
    "_posts.jsonl": "submissions",
    "_posts.ndjson": "submissions",
    "_posts.json": "submissions",
    "_posts.zst": "submissions",
    "_submissions.jsonl": "submissions",
    "_submissions.ndjson": "submissions",
    "_submissions.json": "submissions",
    "_submissions.zst": "submissions",
    "_comments.jsonl": "comments",
    "_comments.ndjson": "comments",
    "_comments.json": "comments",
    "_comments.zst": "comments",
}


def _suffix_info(path: Path) -> tuple[str, str] | None:
    for suffix, role in PAIR_SUFFIXES.items():
        if path.name.lower().endswith(suffix):
            base = path.name[: -len(suffix)]
            key = str(path.parent / base)
            return key, role
    return None


def discover_input_pairs(input_root: str | Path) -> tuple[list[tuple[Path, Path]], list[Path]]:
    groups: dict[str, dict[str, Path]] = {}
    for path in sorted(Path(input_root).rglob("*")):
        if not path.is_file():
            continue
        info = _suffix_info(path)
        if info is None:
            continue
        key, role = info
        groups.setdefault(key, {})[role] = path

    pairs: list[tuple[Path, Path]] = []
    missing: list[Path] = []
    for key in sorted(groups):
        group = groups[key]
        submissions = group.get("submissions")
        comments = group.get("comments")
        if submissions and comments:
            pairs.append((submissions, comments))
        else:
            missing.extend(item for item in group.values())
    return pairs, missing


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def count_lines(path: Path) -> int:
    count = 0
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            count += chunk.count(b"\n")
    return count


def compute_pair_infos(pairs: list[tuple[Path, Path]]) -> list[dict[str, Any]]:
    infos: list[dict[str, Any]] = []
    for submissions_path, comments_path in pairs:
        infos.append(
            {
                "submissions_path": str(submissions_path.resolve()),
                "comments_path": str(comments_path.resolve()),
                "submissions_sha256": compute_sha256(submissions_path),
                "comments_sha256": compute_sha256(comments_path),
                "submissions_bytes": submissions_path.stat().st_size,
                "comments_bytes": comments_path.stat().st_size,
                "submissions_lines": count_lines(submissions_path),
                "comments_lines": count_lines(comments_path),
            }
        )
    return infos


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "pairs": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_registry(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _registry_key(item: dict[str, Any]) -> tuple[str, str]:
    return (item["submissions_path"], item["comments_path"])


def _registry_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left["submissions_sha256"] == right.get("submissions_sha256")
        and left["comments_sha256"] == right.get("comments_sha256")
        and left["submissions_bytes"] == right.get("submissions_bytes")
        and left["comments_bytes"] == right.get("comments_bytes")
        and left["submissions_lines"] == right.get("submissions_lines")
        and left["comments_lines"] == right.get("comments_lines")
    )


def split_pair_infos(
    pair_infos: list[dict[str, Any]],
    registry: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    registry_map = {_registry_key(item): item for item in registry.get("pairs", [])}
    new_pairs: list[dict[str, Any]] = []
    unchanged_pairs: list[dict[str, Any]] = []
    changed_pairs: list[dict[str, Any]] = []
    for info in pair_infos:
        key = _registry_key(info)
        if key not in registry_map:
            new_pairs.append(info)
        elif _registry_match(info, registry_map[key]):
            unchanged_pairs.append(info)
        else:
            changed_pairs.append(info)
    return new_pairs, unchanged_pairs, changed_pairs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Incrementally update the canonical Reddit research corpus from raw submissions/comments pairs."
    )
    parser.add_argument("--input-root", default="data/raw", help="Root directory containing raw Reddit exports.")
    parser.add_argument("--registry", default="data/intermediate/ingest_registry.json", help="Registry file path.")
    parser.add_argument("--sqlite", default="data/intermediate/reddit.db", help="SQLite output path.")
    parser.add_argument("--threads-jsonl", default="data/threads/threads.jsonl", help="Canonical threads JSONL path.")
    parser.add_argument("--threads-md-dir", default="data/threads/md", help="Canonical thread markdown directory.")
    parser.add_argument("--manifest", default="data/threads/thread_index.csv", help="Canonical thread manifest path.")
    parser.add_argument("--allow-changed", action="store_true", help="Rebuild even if existing raw pairs changed.")
    parser.add_argument("--force", action="store_true", help="Rebuild even if registry says nothing changed.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    pairs, missing = discover_input_pairs(args.input_root)
    if missing:
        print("Unpaired raw files detected:", file=sys.stderr)
        for path in missing:
            print(f"- {path}", file=sys.stderr)
    if not pairs:
        print(f"No submissions/comments pairs found under {args.input_root}.", file=sys.stderr)
        return 1

    pair_infos = compute_pair_infos(pairs)
    registry_path = Path(args.registry)
    registry = load_registry(registry_path)
    new_pairs, unchanged_pairs, changed_pairs = split_pair_infos(pair_infos, registry)

    artifact_paths = [
        Path(args.sqlite),
        Path(args.threads_jsonl),
        Path(args.manifest),
        Path(args.threads_jsonl).with_name("orphan_threads.jsonl"),
        Path(args.manifest).with_name("orphan_thread_index.csv"),
    ]
    artifacts_exist = all(path.exists() for path in artifact_paths)

    if changed_pairs and not args.allow_changed:
        print("Raw input pair contents changed. Re-run with --allow-changed to rebuild.", file=sys.stderr)
        for item in changed_pairs:
            print(f"- {item['submissions_path']} | {item['comments_path']}", file=sys.stderr)
        return 1

    if not args.force and artifacts_exist and not new_pairs and not changed_pairs:
        print("No new raw pairs detected. Canonical corpus unchanged.")
        print(f"Pairs tracked: {len(unchanged_pairs)}")
        return 0

    submissions = []
    comments = []
    for item in sorted(pair_infos, key=lambda payload: payload["submissions_path"]):
        submissions.extend(load_submissions(item["submissions_path"]))
        comments.extend(load_comments(item["comments_path"]))

    deduped_submissions = dedupe_submissions(submissions)
    deduped_comments = dedupe_comments(comments)

    write_sqlite(deduped_submissions, deduped_comments, args.sqlite)
    summary = write_threads_artifacts(
        deduped_submissions,
        deduped_comments,
        threads_jsonl_path=args.threads_jsonl,
        threads_md_dir=args.threads_md_dir,
        manifest_path=args.manifest,
    )

    save_registry(
        registry_path,
        {
            "version": 1,
            "pairs": sorted(pair_infos, key=lambda item: (item["submissions_path"], item["comments_path"])),
        },
    )

    print(
        f"Corpus updated from {len(pair_infos)} raw pair(s): "
        f"{len(deduped_submissions)} unique submissions, "
        f"{len(deduped_comments)} unique comments."
    )
    print(
        f"Threads: {summary['threads']} normal, "
        f"{summary['orphan_threads']} orphan | "
        f"comments linked: {summary['thread_comments']} | "
        f"orphan comments: {summary['orphan_comments']}"
    )
    print(f"New pairs: {len(new_pairs)} | changed pairs: {len(changed_pairs)} | unchanged pairs: {len(unchanged_pairs)}")
    print(f"Registry: {registry_path}")
    print(f"Threads JSONL: {args.threads_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
