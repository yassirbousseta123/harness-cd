# Founder-Grade Memory Workflow

Read when:
- upgrading the avatar workflow from representative-slice synthesis to founder-grade deep dive
- reviewing how thread cards, pattern memory, and report sections fit together
- deciding whether the report quality label is honest

## Core rule

Quote candidates are routing aids.
Packs are reading aids.
Thread cards are the real research memory.

The final report may only be written from:
- thread cards
- pattern ledger
- coverage stats

It may not be written from quote candidates alone.

## Architecture

The intended path is:

1. raw corpus
2. state slice
3. priority queue
4. thread cards
5. pattern ledger
6. report sections
7. dossier + profile
8. PDF

## Durable artifacts

The memory layer lives in:

- `outputs/thread_cards/`
- `outputs/pattern_ledger.json`
- `outputs/pattern_ledger.md`
- `outputs/report_sections/`
- `outputs/report_state.json`
- `outputs/founder_report_body.md`

## Thread-card standard

Each processed priority thread should preserve:

- why the thread matters
- the state the person is in
- what makes it worse
- what they think is causing it
- what they already tried
- what disappointed them
- what gave partial relief
- what they really want back
- what they fear or distrust
- 3 to 8 best quotes
- the conversation dynamic
- contradiction notes
- DR takeaways
- awareness guess
- sophistication markers
- evidence refs

## Pattern-ledger standard

Patterns should aggregate repeated signals across thread cards.
Each pattern should keep:

- class
- label
- description
- support count
- supporting thread IDs
- strongest quotes
- confidence
- contradiction notes
- DR significance

## Coverage gate

Quality labels:

- `mapping-only`
- `partial deep dive`
- `founder-grade deep dive`

Safe rule:

- `mapping-only` when `processed_total == 0`
- `partial deep dive` when some priority threads are processed but backlog remains
- `founder-grade deep dive` only when the priority backlog is empty or explicitly allowed near-empty

## Operating loop

1. ingest or update raw exports
2. rebuild avatar workspace
3. refresh founder memory artifacts
4. process only unread priority threads into thread cards
5. merge ledger
6. rewrite report sections from the ledger
7. compile founder report body
8. rebuild dossier/profile/PDF
