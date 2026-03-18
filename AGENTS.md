# AGENTS.md

## Mission

Turn local Reddit exports into **evidence-backed direct-response research assets** without guessing, fabricating support, or drifting into unsafe health claims.

This repo is for **research and synthesis**, not for blind creative generation.

## Non-negotiables

- Never invent evidence.
- Every non-trivial claim in `outputs/` must trace back to real corpus evidence.
- Use `null`, `unknown`, or low confidence instead of guessing age, gender, causal story, or awareness level.
- Separate:
  - **observed signal**
  - **inference**
  - **hypothesis**
- Do not convert a messaging hypothesis into a medical efficacy claim.
- For health-related copy or angle work, keep Meta personal-attribute risk and FTC substantiation risk visible.
- Prefer deterministic scripts for corpus prep. Do not manually hand-edit generated corpora unless the user explicitly asks.

## Repo map

- `data/raw/` — raw Arctic Shift exports
- `data/intermediate/` — SQLite and other deterministic working files
- `data/threads/` — reconstructed per-thread JSONL + markdown + manifest
- `data/packs/` — larger markdown bundles for Codex
- `data/evidence/` — mined quote candidates and supporting tables
- `outputs/` — final research deliverables
- `schemas/` — structured output schemas for `codex exec --output-schema`
- `prompts/` — reusable run prompts
- `.agents/skills/` — project skills
- `.codex/agents/` — custom subagents

## Standard workflow

1. **Ingest first**
   - If raw exports exist but thread artifacts do not, use `arcticshift-ingest`.
   - Do not start synthesis from raw dumps if `threads.jsonl` / markdown / packs are missing.

2. **Select and pack**
   - If the corpus is broad, filter it with `scripts/sample_threads.py`.
   - Build packs with `scripts/build_research_packs.py` before large reading tasks.

3. **Mine evidence**
   - Use `quote-corpus-miner` and `data/evidence/quote_candidates.jsonl` as a starting surface.
   - Verify important quotes against the raw thread markdown before relying on them.

4. **Synthesize**
   - Use `avatar-deep-dive` first.
   - Only after the avatar dossier exists should you use `mechanism-angle-lab`.

5. **Audit**
   - Use `health-ads-compliance` and `claim_auditor` before finalizing outputs.

## Output rules

- Write human-readable deliverables in `outputs/*.md`.
- Write machine-readable deliverables in `outputs/*.json` that match the relevant schema in `schemas/`.
- When a field has weak support, keep the content but lower confidence and name the gap.
- Each section should prefer **multiple supporting examples** over one loud anecdote.
- Use first-person experience threads as the strongest inputs for avatar and language work.

## Evidence standard

An acceptable evidence item should usually include:

- `thread_id`
- `submission_id`
- `comment_id` when relevant
- subreddit
- quote
- a short note explaining why the quote matters

If the output schema requires evidence arrays, fill them. If the evidence is sparse, say so.

## Health + direct-response guardrails

- Do not write “cures,” “treats,” “prevents,” or guaranteed outcome language unless the user explicitly asks for substantiated scientific research and you have actually verified it.
- Treat “mechanism” in two buckets:
  - **market mechanism**: how the market talks about the problem and why a frame may convert
  - **scientific mechanism**: biological or technical explanation that needs external verification
- For Meta-oriented copy work, avoid phrasing that implies the viewer has a diagnosed or sensitive condition.
- Avoid negative-self-perception hooks as default framing.

## Tools and skills

Prefer these existing scripts over one-off reinventions:

- `python scripts/ingest_arcticshift.py`
- `python scripts/sample_threads.py`
- `python scripts/build_research_packs.py`
- `python scripts/extract_quote_candidates.py`
- `python scripts/validate_evidence_refs.py`

Prefer these skills over ad-hoc prompting when the scope matches:

- `arcticshift-ingest`
- `quote-corpus-miner`
- `avatar-deep-dive`
- `mechanism-angle-lab`
- `health-ads-compliance`

## Custom subagents

Use project agents when parallel reading helps:

- `corpus_mapper` — map clusters, gaps, and coverage
- `quote_analyst` — extract exact language and situational detail
- `claim_auditor` — challenge unsupported claims and risky phrasing

If you spawn subagents, wait for all of them and reconcile differences before writing final outputs.

## Verification

After changing Python code:

```bash
python -m pytest -q
```

After generating a structured research output, validate evidence refs:

```bash
python scripts/validate_evidence_refs.py   --json outputs/avatar_profile.json   --thread-index data/threads/thread_index.csv   --threads data/threads/threads.jsonl
```

Use the matching schema with `codex exec --output-schema` whenever the deliverable is machine-readable.

## Decision policy

- If the task is about corpus prep: use scripts.
- If the task is about repeated research workflow: use skills.
- If the task is about large evidence synthesis: consider subagents.
- If a claim touches current platform policy, regulation, or science: verify it before asserting it.
- If uncertain: preserve uncertainty explicitly instead of smoothing it away.

## What “done” looks like

A task is not done when there is just a slick summary.

A task is done when:

- the corpus is prepared deterministically
- the output exists in the right path
- the output matches the requested schema/template
- evidence references are present
- obvious compliance / overclaim risk has been surfaced
