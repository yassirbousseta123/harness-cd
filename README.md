# Tinnitus Reddit Deep-Dive Harness for Codex CLI

This repo is a **Codex-first research harness** for turning Arctic Shift Reddit exports into an evidence-backed corpus that Codex can mine for:

- avatar dossiers
- customer language
- mechanism hypotheses
- landing-page angles
- Meta-safe ad angle banks
- compliance audits

It is built around four layers:

1. **`AGENTS.md`** for durable repo-wide behavior
2. **project skills** in `.agents/skills/` for repeatable workflows
3. **custom subagents** in `.codex/agents/` for parallel reading and auditing
4. **deterministic Python scripts** for ingest, reconstruction, packing, quote mining, and evidence validation

The point is simple: let Codex do the reasoning, but force the data prep and evidence trail to be deterministic.

## Reviewer Pack

If you are reviewing the current workflow and deliverables first, start here:

- workflow note: `docs/reviewer-workflow.md`
- founder-memory workflow: `docs/founder-grade-memory-workflow.md`

Important reviewer note:

- legacy synthesis artifacts were removed during the fresh reset
- committed repo now starts from the new founder-memory architecture, not from a stale PDF/dossier pair
- current research status should be read from `outputs/report_state.json` locally after a refresh run, not from old checked-in outputs

Current honest read depth for the committed report set:

- canonical corpus and workspace are generated locally
- founder-memory state starts at `mapping-only` until real thread cards are created

## What this harness expects

You already have local Reddit data from Arctic Shift in one of these forms:

- `.jsonl`
- `.ndjson`
- `.json`
- `.zst`

Best results come from having a **pair** of files for the same scope:

- submissions
- comments

## Why this harness is opinionated

Health + direct response + Meta is a high-risk combo. This repo is designed to stop common failure modes:

- invented avatar traits
- weak pattern matching from too few threads
- “mechanism” claims with no proof
- copy that implies the viewer has a medical condition
- research outputs with no thread-level audit trail

Everything in `outputs/` should be traceable back to real thread evidence.

## Repo layout

```text
AGENTS.md
AGENT.md
configs/
.codex/
  config.toml
  agents/
.agents/
  skills/
bin/
docs/
prompts/
schemas/
scripts/
src/reddit_dr_harness/
data/
outputs/
tests/
```

## Quickstart

### 1) Install dependencies

Using `uv`:

```bash
uv sync --extra dev
```

Or with standard Python tooling:

```bash
python -m pip install -e ".[dev]"
```

### 2) Put raw exports in `data/raw/`

Example:

```text
data/raw/tinnitus/tinnitus_submissions.jsonl
data/raw/tinnitus/tinnitus_comments.jsonl
```

### 3) Reconstruct threads

```bash
python scripts/ingest_arcticshift.py \
  --submissions data/raw/tinnitus/tinnitus_submissions.jsonl \
  --comments data/raw/tinnitus/tinnitus_comments.jsonl \
  --sqlite data/intermediate/reddit.db \
  --threads-jsonl data/threads/threads.jsonl \
  --threads-md-dir data/threads/md \
  --manifest data/threads/thread_index.csv
```

This also emits orphan bundle artifacts for comments whose `link_id` has no matching submission:

- `data/threads/orphan_threads.jsonl`
- `data/threads/orphan_thread_index.csv`
- `data/threads/orphans_md/*.md`

### 4) Mine quote candidates

```bash
python scripts/extract_quote_candidates.py \
  --threads data/threads/threads.jsonl \
  --out data/evidence/quote_candidates.jsonl
```

### 5) Build research packs for Codex

```bash
python scripts/build_research_packs.py \
  --threads data/threads/threads.jsonl \
  --out-dir data/packs \
  --manifest data/packs/pack_manifest.csv \
  --max-threads 25 \
  --max-chars 120000 \
  --max-comments-per-thread 80
```

### 5b) Refresh the full avatar workspace

For the current beachhead avatar:

```bash
python scripts/build_avatar_workspace.py \
  --config configs/avatar_states/jaw_clenching_nighttime_spike.json \
  --seed-csv /absolute/path/to/manual_source_log.csv
```

This will:

- detect new raw pairs under `data/raw/`
- refresh the canonical corpus only when needed
- refresh quote candidates
- build a broad avatar slice
- build a sharper priority slice
- build reading packs for both

Priority packs now default to smaller deep-reading units:

- `--priority-packs-max-threads 5`
- `--priority-packs-max-chars 45000`
- `--priority-packs-max-comments-per-thread 160`

### 5c) Refresh founder-memory artifacts

This is the new bridge layer between the workspace and the final dossier:

```bash
python scripts/refresh_founder_memory.py \
  --workspace data/avatar_states/jaw_clenching_nighttime_spike \
  --config configs/avatar_states/jaw_clenching_nighttime_spike.json
```

It creates or refreshes:

- `outputs/report_state.json`
- `outputs/current_priority_batch.json`
- `outputs/current_priority_batch.md`
- `outputs/thread_cards/`
- `outputs/pattern_ledger.json`
- `outputs/pattern_ledger.md`
- `outputs/report_sections/`
- `outputs/founder_report_body.md`

### 5d) Render the research report to PDF

Once report sections or a finished body exist, render the report wrapper plus the long-form body:

```bash
python scripts/build_avatar_report.py \
  --workspace data/avatar_states/jaw_clenching_nighttime_spike \
  --config configs/avatar_states/jaw_clenching_nighttime_spike.json \
  --sections-dir outputs/report_sections \
  --report-state outputs/report_state.json \
  --pattern-ledger outputs/pattern_ledger.json \
  --compiled-body-out outputs/founder_report_body.md
```

Outputs:

- `outputs/reports/<avatar_id>/<avatar_id>_report.md`
- `outputs/reports/<avatar_id>/<avatar_id>_report.html`
- `outputs/reports/<avatar_id>/<avatar_id>_report.pdf`

### 6) Run Codex on top of the corpus

Interactive:

```bash
codex -p research
```

Then ask Codex to use the repo skills, or run one of the prompt files directly.

Non-interactive:

```bash
bash bin/avatar-dossier.sh
bash bin/mechanism-lab.sh
bash bin/lander-angles.sh
bash bin/ad-angle-bank.sh
bash bin/compliance-audit.sh
```

`bash bin/avatar-dossier.sh` now treats `outputs/report_state.json` as the structured status output for the founder-grade run. The dossier/profile remain side effects of the memory-first workflow.

## Core workflows

### A. Corpus build

- `scripts/ingest_arcticshift.py`
- `scripts/update_research_corpus.py`
- `scripts/sample_threads.py`
- `scripts/build_research_packs.py`

### B. Evidence surface

- `scripts/extract_quote_candidates.py`
- `scripts/validate_evidence_refs.py`
- `scripts/build_avatar_state_slice.py`
- `scripts/build_avatar_workspace.py`
- `scripts/refresh_founder_memory.py`
- `scripts/build_avatar_report.py`

### C. Codex synthesis

- `prompts/avatar_dossier.prompt.md`
- `prompts/founder_grade_run_prompt.md`
- `prompts/mechanism_lab.prompt.md`
- `prompts/lander_angles.prompt.md`
- `prompts/ad_angle_bank.prompt.md`
- `prompts/compliance_audit.prompt.md`

### D. Structured outputs

- `schemas/avatar_profile.schema.json`
- `schemas/thread_card.schema.json`
- `schemas/pattern_ledger.schema.json`
- `schemas/report_state.schema.json`
- `schemas/mechanism_hypotheses.schema.json`
- `schemas/lander_angle_bank.schema.json`
- `schemas/ad_angle_bank.schema.json`
- `schemas/compliance_audit.schema.json`

## Skills

Use `/skills` inside Codex to see them. This repo ships with:

- `arcticshift-ingest`
- `quote-corpus-miner`
- `avatar-deep-dive`
- `mechanism-angle-lab`
- `health-ads-compliance`

## Custom subagents

Project-scoped agents under `.codex/agents/`:

- `corpus_mapper`
- `quote_analyst`
- `claim_auditor`
- `thread_reader`
- `pattern_librarian`
- `report_editor`

Use them when a task is parallelizable. Example:

```text
Spawn corpus_mapper, quote_analyst, and claim_auditor in parallel.
Wait for all three, then consolidate into outputs/avatar_dossier.md and outputs/avatar_profile.json.
```

## Output standard

Every serious output should separate:

- **observed signal** — plainly supported by quotes / thread evidence
- **inference** — a reasonable synthesis from several signals
- **hypothesis** — useful but still needs validation

For health-related work:

- do not upgrade a messaging hypothesis into a medical claim
- keep “scientific proof required” separate from “copy angle worth testing”
- keep Meta personal-attribute and negative-self-perception risk visible

## State-Cluster Workflow

The repo supports a scalable avatar-state research system for direct-response work.

See:

- `docs/thread-merge-methodology.md`
- `docs/avatar-state-research-system.md`
- `docs/reviewer-workflow.md`

## Suggested working order

1. Build the local corpus
2. Select / pack the most relevant slice
3. Mine deterministic quote candidates
4. Generate the avatar dossier
5. Generate mechanism hypotheses
6. Generate lander angles
7. Generate ad angles
8. Run the compliance audit
9. Validate evidence references again before using anything downstream

## Testing

```bash
python -m pytest -q
```

## Notes

- `AGENT.md` is included as a human-friendly alias, but Codex should read `AGENTS.md`.
- `project_doc_fallback_filenames = ["AGENT.md"]` is set in `.codex/config.toml` so the alias still works if you use it in nested folders later.


## What gets logged

The `bin/*.sh` wrappers write:

- final structured JSON to `outputs/*.json`
- Codex event logs to `outputs/logs/*.events.jsonl`

That gives you both a machine-readable artifact and a replayable run log.
