#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reddit_dr_harness.founder_memory import compile_sections_to_markdown, read_json, write_json


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _count_lines(path: Path) -> int:
    count = 0
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            count += chunk.count(b"\n")
    return count


def _chrome_binary() -> str | None:
    candidates = [
        shutil.which("google-chrome"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _render_pdf_from_html(html_path: Path, pdf_path: Path) -> None:
    chrome = _chrome_binary()
    if chrome:
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--allow-file-access-from-files",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_path}",
                html_path.resolve().as_uri(),
            ],
            check=True,
        )
        return

    with pdf_path.open("wb") as fh:
        subprocess.run(
            ["cupsfilter", "-m", "application/pdf", str(html_path)],
            check=True,
            stdout=fh,
        )


def _top_state_lines(label: str, items: dict[str, int], limit: int = 12) -> list[str]:
    lines = [f"## {label}", ""]
    if not items:
        lines.append("- none")
        lines.append("")
        return lines
    for key, value in list(items.items())[:limit]:
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return lines


def _top_thread_lines(label: str, items: list[dict[str, Any]], limit: int = 15) -> list[str]:
    lines = [f"## {label}", ""]
    if not items:
        lines.append("- none")
        lines.append("")
        return lines
    for item in items[:limit]:
        lines.append(
            f"- `{item['thread_id']}` | score `{item.get('score')}` | "
            f"{item.get('title') or '[untitled]'}"
        )
    lines.append("")
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a long-form avatar research report and render it to PDF."
    )
    parser.add_argument("--workspace", required=True, help="Avatar workspace directory.")
    parser.add_argument("--config", required=True, help="Avatar/state config JSON.")
    parser.add_argument("--body-markdown", help="Optional markdown body to append as the deep research section.")
    parser.add_argument("--sections-dir", help="Optional report-sections directory to compile into the body.")
    parser.add_argument("--report-state", help="Optional report_state.json path for coverage metadata.")
    parser.add_argument("--pattern-ledger", help="Optional pattern_ledger.json path for pattern counts.")
    parser.add_argument("--compiled-body-out", help="Optional path to write the compiled body markdown.")
    parser.add_argument("--out-dir", help="Optional output directory. Defaults to outputs/reports/<avatar_id>/")
    parser.add_argument("--title", help="Optional report title override.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    workspace = Path(args.workspace)
    config_path = Path(args.config)
    config = read_json(config_path)
    avatar_id = config["avatar_id"]
    out_dir = Path(args.out_dir) if args.out_dir else ROOT / "outputs" / "reports" / avatar_id
    out_dir.mkdir(parents=True, exist_ok=True)

    workspace_summary = read_json(workspace / "workspace_summary.json")
    broad_report = read_json(workspace / "report.json")
    priority_report = read_json(workspace / "priority_report.json")
    broad_manifest_rows = _read_csv_rows(workspace / "thread_index.csv")
    priority_manifest_rows = _read_csv_rows(workspace / "priority_thread_index.csv")
    quote_candidate_count = _count_lines(Path(workspace_summary["quote_candidates_path"]))
    report_state = read_json(args.report_state) if args.report_state and Path(args.report_state).exists() else None
    pattern_ledger = read_json(args.pattern_ledger) if args.pattern_ledger and Path(args.pattern_ledger).exists() else None

    title = args.title or f"AVATAR DEEP DIVE RESEARCH REPORT - {config.get('label', avatar_id)}"
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    body_markdown = ""
    if args.body_markdown:
        body_markdown = Path(args.body_markdown).read_text(encoding="utf-8").strip()
    elif args.sections_dir:
        if report_state is None:
            raise RuntimeError("--sections-dir requires --report-state so coverage stays explicit.")
        body_markdown = compile_sections_to_markdown(
            sections_dir=args.sections_dir,
            report_state=report_state,
            pattern_ledger=pattern_ledger,
        ).strip()

    if args.compiled_body_out and body_markdown:
        Path(args.compiled_body_out).write_text(body_markdown + "\n", encoding="utf-8")

    lines = [
        f"# {title}",
        "",
        f"- generated_at: `{generated_at}`",
        f"- avatar_id: `{avatar_id}`",
        f"- config: `{config_path}`",
        f"- workspace: `{workspace}`",
        "",
        "## Scope",
        "",
        "This report is the scalable research wrapper around the active avatar workspace. "
        "It captures corpus scale, treated thread counts, state-cluster match counts, source coverage, "
        "and the long-form deep research body when attached.",
        "",
    ]

    if report_state is not None:
        lines.extend(
            [
                "## Coverage Gate",
                "",
                f"- report_quality_label: `{report_state.get('report_quality_label')}`",
                f"- processed_priority_threads: `{report_state.get('processed_total')}`",
                f"- remaining_priority_threads: `{report_state.get('remaining_priority_threads')}`",
                f"- priority_threads_total: `{report_state.get('priority_threads_total')}`",
                "",
            ]
        )

    if pattern_ledger is not None:
        lines.extend(
            [
                "## Pattern Memory",
                "",
                f"- merged_patterns: `{len(pattern_ledger.get('patterns', []))}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Beachhead Definition",
            "",
            f"- label: `{config.get('label')}`",
            f"- description: {config.get('description')}",
            f"- min_core_score: `{config.get('min_core_score')}`",
            f"- min_core_states: `{config.get('min_core_states')}`",
            f"- priority_min_core_score: `{config.get('priority_min_core_score')}`",
            "",
            "## Corpus Funnel",
            "",
            f"- normal threads in canonical corpus: `{workspace_summary['corpus_summary']['threads']}`",
            f"- orphan threads in canonical corpus: `{workspace_summary['corpus_summary']['orphan_threads']}`",
            f"- unique comments in canonical corpus: `{workspace_summary['corpus_summary']['comments']}`",
            f"- linked comments in normal threads: `{workspace_summary['corpus_summary']['thread_comments']}`",
            f"- orphan comments preserved: `{workspace_summary['corpus_summary']['orphan_comments']}`",
            f"- quote candidates: `{quote_candidate_count}`",
            f"- broad avatar matches: `{workspace_summary['matched_threads']}`",
            f"- priority avatar matches: `{workspace_summary['priority_threads']}`",
            f"- broad packs built: `{workspace_summary['packs_built']}`",
            f"- priority packs built: `{workspace_summary['priority_packs_built']}`",
            "",
            "## Manifest Counts",
            "",
            f"- broad manifest rows: `{len(broad_manifest_rows)}`",
            f"- priority manifest rows: `{len(priority_manifest_rows)}`",
            "",
            "## Source Coverage",
            "",
        ]
    )

    for subreddit, count in broad_report.get("matched_by_subreddit", {}).items():
        lines.append(f"- `{subreddit}`: `{count}` matched threads")
    lines.append("")

    lines.extend(_top_state_lines("Core State Counts", broad_report.get("core_state_counts", {})))
    lines.extend(_top_state_lines("Adjacent State Counts", broad_report.get("adjacent_state_counts", {})))
    lines.extend(_top_thread_lines("Top Broad Threads", broad_report.get("top_threads", [])))
    lines.extend(_top_thread_lines("Top Priority Threads", priority_report.get("top_priority_threads", [])))
    lines.extend(_top_thread_lines("Near-Miss Discovery Threads", broad_report.get("near_miss_threads", [])))

    lines.extend(
        [
            "## Reproducibility",
            "",
            f"- seed corpus: `{workspace_summary.get('seed_corpus_path')}`",
            f"- canonical threads: `{workspace_summary['canonical_threads_path']}`",
            f"- canonical orphan threads: `{workspace_summary['canonical_orphan_threads_path']}`",
            f"- quote candidates: `{workspace_summary['quote_candidates_path']}`",
            f"- broad slice manifest: `{workspace_summary['slice_manifest_path']}`",
            f"- priority slice manifest: `{workspace_summary['priority_manifest_path']}`",
        ]
    )
    if args.report_state:
        lines.append(f"- report state: `{args.report_state}`")
    if args.pattern_ledger:
        lines.append(f"- pattern ledger: `{args.pattern_ledger}`")
    if args.sections_dir:
        lines.append(f"- report sections: `{args.sections_dir}`")
    if args.compiled_body_out:
        lines.append(f"- compiled body: `{args.compiled_body_out}`")
    lines.extend(
        [
            "",
            "## Deep Research Body",
            "",
        ]
    )

    if body_markdown:
        lines.append(body_markdown)
        lines.append("")
    else:
        lines.append("_No body markdown attached yet. Build report sections or attach `--body-markdown` and rerun to embed it into this PDF._")
        lines.append("")

    markdown_path = out_dir / f"{avatar_id}_report.md"
    html_path = out_dir / f"{avatar_id}_report.html"
    pdf_path = out_dir / f"{avatar_id}_report.pdf"

    markdown_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    subprocess.run(
        [
            "pandoc",
            str(markdown_path),
            "--standalone",
            "--from",
            "gfm",
            "--to",
            "html5",
            "--output",
            str(html_path),
        ],
        check=True,
    )
    _render_pdf_from_html(html_path, pdf_path)

    if report_state is not None and args.report_state:
        report_state["pdf_last_built_at"] = generated_at
        if args.compiled_body_out:
            report_state["compiled_body_path"] = str(Path(args.compiled_body_out))
            report_state["sections_last_built_at"] = generated_at
        write_json(args.report_state, report_state)

    print(f"Markdown report: {markdown_path}")
    print(f"HTML report: {html_path}")
    print(f"PDF report: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
