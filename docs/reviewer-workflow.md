# Reviewer Workflow Note

Read when:
- reviewing the current research workflow
- auditing what was automated vs manually read
- evaluating the attached PDF deliverable

## Purpose

This note exists so a direct-response reviewer can inspect the harness honestly.

It separates:
- deterministic corpus prep
- state-cluster slicing
- manual thread reading
- final synthesis

It now also documents the founder-grade rebuild path:
- priority queue
- thread cards
- pattern ledger
- section-by-section report writing

## What The Harness Does Well

The harness is strong at:

- merging Reddit submissions + comments into readable threads
- preserving orphan comment bundles instead of dropping them
- building canonical thread artifacts
- creating a broad avatar slice and a tighter priority slice
- rendering a report wrapper with current counts
- validating evidence refs in the structured profile

This is the filing / retrieval / evidence layer.

## Current Research Workflow

### 1. Raw ingest

Current local raw source:

- `data/raw/tinnitus/r_Tinnitus_posts.jsonl`
- `data/raw/tinnitus/r_Tinnitus_comments.jsonl`

Those get reconstructed into:

- `data/threads/threads.jsonl`
- `data/threads/orphan_threads.jsonl`
- manifests
- per-thread markdown

### 2. Avatar-state slicing

Current beachhead config:

- `configs/avatar_states/jaw_clenching_nighttime_spike.json`

That config scores the canonical corpus for this state cluster:

- nighttime ringing
- jaw tension / clenching
- quiet-room amplification
- sleep dread / lying-down spike
- night-guard confusion
- normal-hearing-test-but-still-miserable

### 3. Pack generation

The system builds:

- broad slice packs
- priority slice packs

These are reading aids, not the final research themselves.

### 4. Manual reading

For the currently committed PDF/report set, the manual reading depth is limited.

Current honest counts:

- threads scored by system: `24,328`
- broad matched slice: `2,797`
- priority slice: `712`
- manually context-read for the current synthesis: `16` full threads
- unique threads cited in structured evidence: `13`
- pack/thread windows manually opened during synthesis: `9`

## Current Deliverable Status

The repo has been reset to remove stale legacy deliverables that were created before the founder-memory rebuild.

Important:

- old committed dossier/profile/PDF artifacts were intentionally removed
- current truth should come from the active local workspace plus founder-memory state
- a founder-grade report should only reappear after thread cards and pattern ledger coverage exist

## Founder-Grade Rebuild Path

The repo now includes the stronger forward path:

- `docs/founder-grade-memory-workflow.md`
- `scripts/refresh_founder_memory.py`
- `outputs/thread_cards/`
- `outputs/pattern_ledger.*`
- `outputs/report_sections/`
- `outputs/report_state.json`

That rebuild changes the intended order to:

1. workspace
2. unread priority queue
3. thread cards
4. pattern ledger
5. report sections
6. dossier/profile/PDF

So the repo should now be read as:

- committed architecture: materially better aligned with founder-grade deep reading
- committed research output: intentionally reset so stale artifacts do not masquerade as finished work

## Known Gap

The key gap is not infrastructure. It is reading depth.

The current workflow still leans too much on:

- state scoring
- quote surface mining
- representative-thread reading

and not enough on:

- exhaustive thread-by-thread manual reading
- preserving full conversational context
- building the avatar from repeated thread snapshots at the density of the benchmark PDF

## Corpus Limitation

The current validated local evidence base is still:

- `r/tinnitus` only

User-provided seed context includes:

- `r/TMJ`
- `r/bruxism`

But those two subreddits are not yet ingested locally as raw corpora.

## How A Reviewer Should Read This Repo

Treat the repo as:

- a strong research harness
- a strong corpus-prep layer
- a partial deep-dive attempt

Do not treat the current PDF as proof that the manual deep-dive process is finished.

## Best Next Step

If the goal is a true DR avatar deep dive at the benchmark level:

1. ingest `r/TMJ` and `r/bruxism`
2. manually read the full `712` priority-thread slice
3. expand evidence-backed thread snapshots
4. rewrite the deep-dive from manual reading first, counts second
