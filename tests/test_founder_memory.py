from __future__ import annotations

from pathlib import Path

from reddit_dr_harness.founder_memory import (
    build_report_state,
    compile_sections_to_markdown,
    ensure_section_files,
    load_or_init_pattern_ledger,
)


def test_build_report_state_tracks_processed_ids_and_next_batch() -> None:
    priority_rows = [
        {"thread_id": "t1", "title": "one", "subreddit": "tinnitus", "markdown_path": "a.md", "score": "9.1"},
        {"thread_id": "t2", "title": "two", "subreddit": "tinnitus", "markdown_path": "b.md", "score": "8.4"},
        {"thread_id": "t3", "title": "three", "subreddit": "tmj", "markdown_path": "c.md", "score": "8.0"},
    ]
    state = build_report_state(
        avatar_id="jaw_clenching_nighttime_spike",
        priority_rows=priority_rows,
        existing_state={"processed_priority_thread_ids": ["t1", "missing"]},
        batch_size=2,
    )

    assert state["processed_total"] == 1
    assert state["remaining_priority_threads"] == 2
    assert state["report_quality_label"] == "partial deep dive"
    assert [item["thread_id"] for item in state["next_priority_batch"]] == ["t2", "t3"]


def test_section_scaffolding_and_body_compile(tmp_path: Path) -> None:
    template_path = tmp_path / "template.md"
    template_path.write_text("## Section name\n\nPlaceholder.\n", encoding="utf-8")
    sections_dir = tmp_path / "sections"

    created = ensure_section_files(
        sections_dir=sections_dir,
        template_path=template_path,
        section_order=["pain_points", "objections"],
    )

    assert len(created) == 2

    (sections_dir / "pain_points.md").write_text("## Pain Points\n\nCustom body.\n", encoding="utf-8")
    ledger = load_or_init_pattern_ledger(
        path=tmp_path / "pattern_ledger.json",
        avatar_id="jaw_clenching_nighttime_spike",
        processed_total=2,
        remaining_priority_threads=1,
        subreddits=["tinnitus", "tmj"],
    )
    body = compile_sections_to_markdown(
        sections_dir=sections_dir,
        report_state={
            "report_quality_label": "partial deep dive",
            "processed_total": 2,
            "remaining_priority_threads": 1,
        },
        pattern_ledger=ledger,
        section_order=["pain_points", "objections"],
    )

    assert "## Pain Points" in body
    assert "## Objections" in body
    assert "partial deep dive" in body
