#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_research_packs import build_packs
from update_research_corpus import (
    compute_pair_infos,
    discover_input_pairs,
    load_registry,
    save_registry,
    split_pair_infos,
)
from reddit_dr_harness.avatar_state import build_avatar_slice, load_avatar_config, load_threads_from_paths, write_avatar_slice
from reddit_dr_harness.corpus_metrics import summarize_current_corpus
from reddit_dr_harness.founder_memory import file_sha256, remove_path
from reddit_dr_harness.ingest import dedupe_comments, dedupe_submissions, load_comments, load_submissions, write_sqlite, write_threads_artifacts
from reddit_dr_harness.quotes import extract_quote_candidates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Update the full corpus and rebuild an avatar/state-cluster workspace in one run."
    )
    parser.add_argument("--config", required=True, help="Avatar/state config JSON.")
    parser.add_argument("--input-root", default="data/raw", help="Root directory containing raw Reddit exports.")
    parser.add_argument("--registry", default="data/intermediate/ingest_registry.json", help="Registry file path.")
    parser.add_argument("--sqlite", default="data/intermediate/reddit.db", help="SQLite output path.")
    parser.add_argument("--threads-jsonl", default="data/threads/threads.jsonl", help="Canonical threads JSONL path.")
    parser.add_argument("--threads-md-dir", default="data/threads/md", help="Canonical thread markdown directory.")
    parser.add_argument("--manifest", default="data/threads/thread_index.csv", help="Canonical thread manifest path.")
    parser.add_argument("--quotes-out", default="data/evidence/quote_candidates.jsonl", help="Canonical quote candidate JSONL.")
    parser.add_argument("--seed-csv", help="Optional manual source-log CSV to copy into the avatar workspace.")
    parser.add_argument("--workspace-root", default="data/avatar_states", help="Root directory for avatar-specific slices.")
    parser.add_argument("--allow-changed", action="store_true", help="Rebuild if existing raw pairs changed.")
    parser.add_argument("--force", action="store_true", help="Rebuild even if registry says nothing changed.")
    parser.add_argument("--clean-workspace", action="store_true", help="Delete generated avatar workspace artifacts before rebuilding the slice.")
    parser.add_argument("--packs-max-threads", type=int, default=20, help="Maximum threads per avatar pack.")
    parser.add_argument("--packs-max-chars", type=int, default=120000, help="Maximum characters per avatar pack.")
    parser.add_argument("--packs-max-comments-per-thread", type=int, default=80, help="Maximum comments per thread in avatar packs.")
    parser.add_argument("--priority-packs-max-threads", type=int, default=5, help="Maximum threads per priority pack.")
    parser.add_argument("--priority-packs-max-chars", type=int, default=45000, help="Maximum characters per priority pack.")
    parser.add_argument("--priority-packs-max-comments-per-thread", type=int, default=160, help="Maximum comments per thread in priority packs.")
    return parser


def clean_avatar_workspace(workspace_root: Path) -> None:
    for dirname in ("packs", "priority_packs"):
        remove_path(workspace_root / dirname)
    for filename in (
        "threads.jsonl",
        "thread_index.csv",
        "report.json",
        "priority_threads.jsonl",
        "priority_thread_index.csv",
        "priority_report.json",
        "pack_manifest.csv",
        "priority_pack_manifest.csv",
        "workspace_summary.json",
        "seed_corpus.csv",
    ):
        remove_path(workspace_root / filename)


def ensure_canonical_corpus(args: argparse.Namespace) -> dict[str, int]:
    pairs, missing = discover_input_pairs(args.input_root)
    if missing:
        print("Unpaired raw files detected:")
        for path in missing:
            print(f"- {path}")
    if not pairs:
        raise RuntimeError(f"No submissions/comments pairs found under {args.input_root}.")

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
        raise RuntimeError("Raw input pair contents changed. Re-run with --allow-changed.")

    if not args.force and artifacts_exist and not new_pairs and not changed_pairs:
        print("Canonical corpus already current.")
        return {
            **summarize_current_corpus(
                sqlite_path=args.sqlite,
                manifest_path=args.manifest,
            ),
            "corpus_refreshed": False,
            "new_pairs": 0,
            "changed_pairs": 0,
            "unchanged_pairs": len(unchanged_pairs),
        }

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
        f"Canonical corpus refreshed: {summary['threads']} threads, {summary['orphan_threads']} orphan threads, "
        f"{summary['comments']} unique comments."
    )
    return {
        **summary,
        "corpus_refreshed": True,
        "new_pairs": len(new_pairs),
        "changed_pairs": len(changed_pairs),
        "unchanged_pairs": len(unchanged_pairs),
    }


def main() -> int:
    args = build_parser().parse_args()
    config = load_avatar_config(args.config)
    avatar_id = config["avatar_id"]
    workspace_root = Path(args.workspace_root) / avatar_id
    workspace_root.mkdir(parents=True, exist_ok=True)
    if args.clean_workspace:
        clean_avatar_workspace(workspace_root)

    corpus_summary = ensure_canonical_corpus(args)

    threads_paths = [args.threads_jsonl, str(Path(args.threads_jsonl).with_name("orphan_threads.jsonl"))]
    if args.force or corpus_summary.get("corpus_refreshed") or not Path(args.quotes_out).exists():
        quote_candidates = extract_quote_candidates(threads_paths, out_path=args.quotes_out)
        print(f"Quote candidates refreshed: {len(quote_candidates)} -> {args.quotes_out}")
    else:
        quote_candidates = None
        print(f"Quote candidates already current: {args.quotes_out}")

    threads = load_threads_from_paths(threads_paths)
    matched_threads, report = build_avatar_slice(threads, config)
    if not matched_threads:
        raise RuntimeError(f"No threads matched avatar config {avatar_id}.")
    priority_threads = [thread for thread in matched_threads if thread["slice_metadata"]["priority_qualifies"]]

    slice_threads_path = workspace_root / "threads.jsonl"
    slice_manifest_path = workspace_root / "thread_index.csv"
    slice_report_path = workspace_root / "report.json"
    write_avatar_slice(
        matched_threads,
        out_threads_path=slice_threads_path,
        out_manifest_path=slice_manifest_path,
    )
    slice_report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    priority_threads_path = workspace_root / "priority_threads.jsonl"
    priority_manifest_path = workspace_root / "priority_thread_index.csv"
    priority_report_path = workspace_root / "priority_report.json"
    write_avatar_slice(
        priority_threads,
        out_threads_path=priority_threads_path,
        out_manifest_path=priority_manifest_path,
    )
    priority_report = {
        "avatar_id": avatar_id,
        "priority_threads": len(priority_threads),
        "top_priority_threads": [
            {
                "thread_id": thread["thread_id"],
                "title": thread["slice_metadata"]["title"],
                "score": thread["slice_metadata"]["score"],
                "matched_core_states": [item["id"] for item in thread["slice_metadata"]["matched_core_states"]],
            }
            for thread in priority_threads[:50]
        ],
    }
    priority_report_path.write_text(json.dumps(priority_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    packs_dir = workspace_root / "packs"
    pack_manifest_path = workspace_root / "pack_manifest.csv"
    packs = build_packs(
        matched_threads,
        out_dir=packs_dir,
        manifest_path=pack_manifest_path,
        max_threads=args.packs_max_threads,
        max_chars=args.packs_max_chars,
        max_comments_per_thread=args.packs_max_comments_per_thread,
    )

    priority_packs_dir = workspace_root / "priority_packs"
    priority_pack_manifest_path = workspace_root / "priority_pack_manifest.csv"
    priority_packs = build_packs(
        priority_threads,
        out_dir=priority_packs_dir,
        manifest_path=priority_pack_manifest_path,
        max_threads=args.priority_packs_max_threads,
        max_chars=args.priority_packs_max_chars,
        max_comments_per_thread=args.priority_packs_max_comments_per_thread,
    )

    seed_copy_path = None
    if args.seed_csv:
        seed_copy_path = workspace_root / "seed_corpus.csv"
        shutil.copy2(args.seed_csv, seed_copy_path)

    summary = {
        "avatar_id": avatar_id,
        "label": config.get("label"),
        "workspace_root": str(workspace_root),
        "workspace_signature": file_sha256(priority_manifest_path),
        "canonical_threads_path": args.threads_jsonl,
        "canonical_orphan_threads_path": str(Path(args.threads_jsonl).with_name("orphan_threads.jsonl")),
        "quote_candidates_path": args.quotes_out,
        "slice_threads_path": str(slice_threads_path),
        "slice_manifest_path": str(slice_manifest_path),
        "slice_report_path": str(slice_report_path),
        "pack_manifest_path": str(pack_manifest_path),
        "priority_threads_path": str(priority_threads_path),
        "priority_manifest_path": str(priority_manifest_path),
        "priority_report_path": str(priority_report_path),
        "priority_pack_manifest_path": str(priority_pack_manifest_path),
        "packs_built": len(packs),
        "priority_packs_built": len(priority_packs),
        "matched_threads": len(matched_threads),
        "priority_threads": len(priority_threads),
        "seed_corpus_path": str(seed_copy_path) if seed_copy_path else None,
        "matched_by_subreddit": report.get("matched_by_subreddit", {}),
        "corpus_summary": corpus_summary,
    }
    (workspace_root / "workspace_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Avatar workspace ready: {workspace_root}")
    print(f"Matched threads: {len(matched_threads)}")
    print(f"Packs built: {len(packs)}")
    print(f"Priority threads: {len(priority_threads)}")
    print(f"Priority packs built: {len(priority_packs)}")
    if seed_copy_path:
        print(f"Seed corpus copied: {seed_copy_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
