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

from reddit_dr_harness.founder_memory import (
    compile_sections_to_markdown,
    ensure_section_files,
    load_or_init_pattern_ledger,
    load_or_init_report_state,
    load_priority_manifest,
    read_json,
    render_pattern_ledger_markdown,
    render_priority_batch_markdown,
    write_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Refresh deterministic founder-memory artifacts for the active avatar workspace."
    )
    parser.add_argument("--workspace", required=True, help="Avatar workspace directory.")
    parser.add_argument("--config", required=True, help="Avatar config JSON.")
    parser.add_argument("--outputs-root", default="outputs", help="Output root for founder artifacts.")
    parser.add_argument(
        "--sections-template",
        default=".agents/skills/avatar-deep-dive/assets/founder_grade_section_template.md",
        help="Founder-grade section template path.",
    )
    parser.add_argument("--batch-size", type=int, default=5, help="Unread priority threads to queue per batch.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    workspace = Path(args.workspace)
    config = read_json(args.config)
    avatar_id = config["avatar_id"]
    outputs_root = Path(args.outputs_root)
    outputs_root.mkdir(parents=True, exist_ok=True)

    thread_cards_dir = outputs_root / "thread_cards"
    report_sections_dir = outputs_root / "report_sections"
    thread_cards_dir.mkdir(parents=True, exist_ok=True)
    report_sections_dir.mkdir(parents=True, exist_ok=True)

    priority_manifest_path = workspace / "priority_thread_index.csv"
    priority_rows = load_priority_manifest(priority_manifest_path)

    founder_body_path = outputs_root / "founder_report_body.md"
    report_state_path = outputs_root / "report_state.json"
    report_state = load_or_init_report_state(
        path=report_state_path,
        avatar_id=avatar_id,
        priority_rows=priority_rows,
        batch_size=args.batch_size,
        workspace_root=str(workspace),
        priority_manifest_path=str(priority_manifest_path),
        compiled_body_path=str(founder_body_path),
    )
    write_json(report_state_path, report_state)

    ledger_path = outputs_root / "pattern_ledger.json"
    ledger = load_or_init_pattern_ledger(
        path=ledger_path,
        avatar_id=avatar_id,
        processed_total=report_state["processed_total"],
        remaining_priority_threads=report_state["remaining_priority_threads"],
        subreddits=sorted({row.get("subreddit") or "" for row in priority_rows}),
    )
    write_json(ledger_path, ledger)
    (outputs_root / "pattern_ledger.md").write_text(
        render_pattern_ledger_markdown(ledger),
        encoding="utf-8",
    )

    created_sections = ensure_section_files(
        sections_dir=report_sections_dir,
        template_path=args.sections_template,
    )

    founder_body = compile_sections_to_markdown(
        sections_dir=report_sections_dir,
        report_state=report_state,
        pattern_ledger=ledger,
    )
    founder_body_path.write_text(founder_body, encoding="utf-8")

    batch_json_path = outputs_root / "current_priority_batch.json"
    batch_md_path = outputs_root / "current_priority_batch.md"
    batch_json_path.write_text(
        json.dumps(report_state.get("next_priority_batch", []), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    batch_md_path.write_text(
        render_priority_batch_markdown(report_state.get("next_priority_batch", []), avatar_id=avatar_id),
        encoding="utf-8",
    )

    print(f"Founder memory ready: {outputs_root}")
    print(f"Priority threads total: {report_state['priority_threads_total']}")
    print(f"Processed total: {report_state['processed_total']}")
    print(f"Remaining priority threads: {report_state['remaining_priority_threads']}")
    print(f"Queued next batch: {len(report_state.get('next_priority_batch', []))}")
    if created_sections:
        print(f"Section stubs created: {len(created_sections)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
