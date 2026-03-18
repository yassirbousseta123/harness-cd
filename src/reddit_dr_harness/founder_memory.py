from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_SECTION_ORDER = [
    "avatar_explanation",
    "pain_points",
    "day_to_day_struggles",
    "failed_fixes",
    "victories_and_hope_signals",
    "mechanism_beliefs",
    "desires",
    "objections",
    "awareness_and_sophistication",
    "direct_response_implications",
    "supplement_positioning_lane",
    "gaps_and_contradictions",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_priority_manifest(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _quality_label(processed_total: int, remaining: int) -> str:
    if processed_total <= 0:
        return "mapping-only"
    if remaining <= 0:
        return "founder-grade deep dive"
    return "partial deep dive"


def _normalize_processed_ids(existing_ids: list[str], valid_ids: set[str]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for thread_id in existing_ids:
        if thread_id in valid_ids and thread_id not in seen:
            seen.add(thread_id)
            items.append(thread_id)
    return items


def _next_priority_batch(
    priority_rows: list[dict[str, str]],
    processed_ids: set[str],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in priority_rows:
        thread_id = row.get("thread_id") or ""
        if not thread_id or thread_id in processed_ids:
            continue
        score_raw = row.get("score")
        score = float(score_raw) if score_raw not in (None, "") else None
        items.append(
            {
                "thread_id": thread_id,
                "title": row.get("title") or "[untitled]",
                "subreddit": row.get("subreddit") or None,
                "markdown_path": row.get("markdown_path") or None,
                "score": score,
            }
        )
        if len(items) >= limit:
            break
    return items


def build_report_state(
    *,
    avatar_id: str,
    priority_rows: list[dict[str, str]],
    existing_state: dict[str, Any] | None = None,
    batch_size: int = 5,
    workspace_root: str | None = None,
    priority_manifest_path: str | None = None,
    compiled_body_path: str | None = None,
) -> dict[str, Any]:
    existing = existing_state or {}
    priority_ids = [row.get("thread_id") or "" for row in priority_rows if row.get("thread_id")]
    priority_id_set = {thread_id for thread_id in priority_ids if thread_id}
    processed_ids = _normalize_processed_ids(existing.get("processed_priority_thread_ids", []), priority_id_set)
    processed_total = len(processed_ids)
    remaining = max(len(priority_ids) - processed_total, 0)
    next_batch = _next_priority_batch(priority_rows, set(processed_ids), limit=batch_size)
    return {
        "avatar_id": avatar_id,
        "report_quality_label": _quality_label(processed_total, remaining),
        "processed_total": processed_total,
        "remaining_priority_threads": remaining,
        "processed_this_run": int(existing.get("processed_this_run", 0)),
        "priority_threads_total": len(priority_ids),
        "processed_priority_thread_ids": processed_ids,
        "next_priority_batch": next_batch,
        "updated_files": list(existing.get("updated_files", [])),
        "notable_new_patterns": list(existing.get("notable_new_patterns", [])),
        "notes": list(existing.get("notes", [])),
        "last_batch_processed_at": existing.get("last_batch_processed_at"),
        "last_refreshed_at": utc_now_iso(),
        "dossier_version": int(existing.get("dossier_version", 0)),
        "pattern_ledger_version": int(existing.get("pattern_ledger_version", 0)),
        "sections_last_built_at": existing.get("sections_last_built_at"),
        "pdf_last_built_at": existing.get("pdf_last_built_at"),
        "workspace_root": workspace_root,
        "priority_manifest_path": priority_manifest_path,
        "compiled_body_path": compiled_body_path,
    }


def load_or_init_report_state(
    *,
    path: str | Path,
    avatar_id: str,
    priority_rows: list[dict[str, str]],
    batch_size: int = 5,
    workspace_root: str | None = None,
    priority_manifest_path: str | None = None,
    compiled_body_path: str | None = None,
) -> dict[str, Any]:
    state_path = Path(path)
    existing = read_json(state_path) if state_path.exists() else {}
    return build_report_state(
        avatar_id=avatar_id,
        priority_rows=priority_rows,
        existing_state=existing,
        batch_size=batch_size,
        workspace_root=workspace_root,
        priority_manifest_path=priority_manifest_path,
        compiled_body_path=compiled_body_path,
    )


def load_or_init_pattern_ledger(
    *,
    path: str | Path,
    avatar_id: str,
    processed_total: int,
    remaining_priority_threads: int,
    subreddits: list[str],
) -> dict[str, Any]:
    ledger_path = Path(path)
    existing = read_json(ledger_path) if ledger_path.exists() else {}
    return {
        "avatar_id": avatar_id,
        "updated_at": utc_now_iso(),
        "version": int(existing.get("version", 0)),
        "coverage": {
            "processed_priority_threads": processed_total,
            "remaining_priority_threads": remaining_priority_threads,
            "subreddits": sorted({item for item in subreddits if item}),
        },
        "patterns": list(existing.get("patterns", [])),
    }


def render_pattern_ledger_markdown(ledger: dict[str, Any]) -> str:
    coverage = ledger.get("coverage", {})
    lines = [
        f"# Pattern Ledger - {ledger.get('avatar_id', 'unknown')}",
        "",
        f"- updated_at: `{ledger.get('updated_at')}`",
        f"- processed_priority_threads: `{coverage.get('processed_priority_threads', 0)}`",
        f"- remaining_priority_threads: `{coverage.get('remaining_priority_threads', 0)}`",
        "",
    ]
    subreddits = coverage.get("subreddits") or []
    if subreddits:
        lines.append("## Subreddits")
        lines.append("")
        for subreddit in subreddits:
            lines.append(f"- `{subreddit}`")
        lines.append("")

    patterns = ledger.get("patterns") or []
    if not patterns:
        lines.extend(
            [
                "## Patterns",
                "",
                "_No merged patterns yet. Process priority threads into thread cards first._",
                "",
            ]
        )
        return "\n".join(lines).strip() + "\n"

    lines.append("## Patterns")
    lines.append("")
    for pattern in patterns:
        lines.append(f"### {pattern.get('label', '[unlabeled]')}")
        lines.append(f"- class: `{pattern.get('class', 'unknown')}`")
        lines.append(f"- support_count: `{pattern.get('support_count', 0)}`")
        lines.append(f"- confidence: `{pattern.get('confidence', 'unknown')}`")
        lines.append(f"- description: {pattern.get('description', '')}")
        dr_significance = pattern.get("dr_significance")
        if dr_significance:
            lines.append(f"- DR significance: {dr_significance}")
        quotes = pattern.get("strongest_quotes") or []
        if quotes:
            lines.append("- strongest quotes:")
            for quote in quotes[:5]:
                lines.append(f"  - {quote}")
        contradictions = pattern.get("contradiction_notes") or []
        if contradictions:
            lines.append("- contradictions:")
            for item in contradictions[:5]:
                lines.append(f"  - {item}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _humanize_section_slug(slug: str) -> str:
    return slug.replace("_", " ").strip().title()


def ensure_section_files(
    *,
    sections_dir: str | Path,
    template_path: str | Path,
    section_order: list[str] | None = None,
) -> list[str]:
    order = section_order or DEFAULT_SECTION_ORDER
    target_dir = Path(sections_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    template = Path(template_path).read_text(encoding="utf-8")
    created: list[str] = []
    for slug in order:
        path = target_dir / f"{slug}.md"
        if path.exists():
            continue
        title = _humanize_section_slug(slug)
        body = template.replace("## Section name", f"## {title}")
        path.write_text(body.strip() + "\n", encoding="utf-8")
        created.append(str(path))
    return created


def compile_sections_to_markdown(
    *,
    sections_dir: str | Path,
    report_state: dict[str, Any],
    pattern_ledger: dict[str, Any] | None = None,
    section_order: list[str] | None = None,
) -> str:
    order = section_order or DEFAULT_SECTION_ORDER
    root = Path(sections_dir)
    lines = [
        "# Founder-Grade Report Body",
        "",
        f"- report_quality_label: `{report_state.get('report_quality_label', 'unknown')}`",
        f"- processed_priority_threads: `{report_state.get('processed_total', 0)}`",
        f"- remaining_priority_threads: `{report_state.get('remaining_priority_threads', 0)}`",
        "",
    ]
    if pattern_ledger is not None:
        lines.append(f"- merged_patterns: `{len(pattern_ledger.get('patterns', []))}`")
        lines.append("")

    rendered = 0
    for slug in order:
        path = root / f"{slug}.md"
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        rendered += 1
        lines.append(content)
        lines.append("")
    if rendered == 0:
        lines.append("_No report sections written yet. Process priority threads into thread cards, merge the ledger, then rewrite sections._")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_priority_batch_markdown(batch: list[dict[str, Any]], *, avatar_id: str) -> str:
    lines = [
        f"# Current Priority Batch - {avatar_id}",
        "",
    ]
    if not batch:
        lines.append("_No unread priority threads remain._")
        lines.append("")
        return "\n".join(lines)
    for item in batch:
        score = item.get("score")
        score_text = f"{score:.2f}" if isinstance(score, float) else "n/a"
        lines.append(f"- `{item.get('thread_id')}` | score `{score_text}` | {item.get('title')}")
    lines.append("")
    return "\n".join(lines)
