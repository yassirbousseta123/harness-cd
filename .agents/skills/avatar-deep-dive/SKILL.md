---
name: avatar-deep-dive
description: Build a founder-grade avatar dossier from the local Reddit corpus. Use after threads, packs, quote candidates, and avatar workspace artifacts exist. Output should grow from thread cards and pattern memory, not from representative-slice summary.
short-description: Founder-grade avatar workflow from priority threads to dossier
---

# Avatar Deep Dive

This skill exists to turn the local corpus into a real direct-response avatar dossier.

## Use when

- thread artifacts exist
- an avatar workspace exists
- priority manifests exist
- the user wants founder-grade reading depth, not just a summary

## Required deliverables

- `outputs/thread_cards/<thread_id>.json`
- `outputs/thread_cards/<thread_id>.md`
- `outputs/pattern_ledger.json`
- `outputs/pattern_ledger.md`
- `outputs/report_sections/*.md`
- `outputs/avatar_profile.json`
- `outputs/avatar_dossier.md`
- `outputs/report_state.json`

Use:

- `schemas/thread_card.schema.json`
- `schemas/pattern_ledger.schema.json`
- `schemas/report_state.schema.json`
- `assets/avatar_template.md`
- `assets/founder_grade_section_template.md`

## Workflow

1. Read the workspace summary, priority manifest, and report state first.
2. Treat quote candidates as routing aids, not final evidence.
3. Process unread priority threads into thread cards.
4. Preserve conversation dynamics, contradictions, and emotional density.
5. Merge thread cards into the pattern ledger.
6. Rewrite report sections from the ledger.
7. Rebuild the dossier/profile from the memory layer.
8. Keep coverage stats honest.

## Coverage gate

- Never call the report founder-grade when substantial priority backlog remains.
- Use quality labels in `outputs/report_state.json`:
  - `mapping-only`
  - `partial deep dive`
  - `founder-grade deep dive`

## Strong synthesis pattern

For each section:

1. Name the dominant repeated pattern
2. Back it with multiple thread cards
3. Keep exact language that can travel into copy later
4. Preserve disagreement instead of flattening it away
5. State why the pattern matters for direct response

## Quality bar

- No invented demographics
- No mechanism claims masquerading as facts
- No quote-bank-only writing
- No “representative slice” shortcut when unread priority threads exist
- No founder-grade label without coverage to support it

## References

- `assets/avatar_template.md`
- `assets/founder_grade_section_template.md`
- `../../../../schemas/avatar_profile.schema.json`
- `../../../../schemas/thread_card.schema.json`
- `../../../../schemas/pattern_ledger.schema.json`
- `../../../../schemas/report_state.schema.json`
