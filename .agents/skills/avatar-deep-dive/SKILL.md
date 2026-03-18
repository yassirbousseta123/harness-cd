---
name: avatar-deep-dive
description: Build an evidence-backed avatar dossier from the local Reddit corpus. Use after threads, packs, and quote candidates exist. Output should follow the avatar schema and template, and every major claim should map back to thread-level evidence. Do not guess unsupported demographics or causal stories.
short-description: Generate the avatar dossier from local Reddit evidence
---

# Avatar Deep Dive

This skill exists to turn the local corpus into a **real avatar dossier**, not a vibes-based persona.

## Use when

- thread artifacts exist
- quote candidates exist or can be generated
- the user wants the avatar sections filled with evidence

## Required deliverables

- `outputs/avatar_profile.json`
- `outputs/avatar_dossier.md`

Use:

- `schemas/avatar_profile.schema.json`
- `assets/avatar_template.md`

## Workflow

1. Read the corpus manifests and packs first.
2. Read `data/evidence/quote_candidates.jsonl` as a routing aid.
3. If the corpus is large, use subagents:
   - `corpus_mapper`
   - `quote_analyst`
   - `claim_auditor`
4. Fill every requested avatar section.
5. When evidence is weak:
   - keep the section
   - lower confidence
   - name the gap explicitly
6. Do not infer age or gender unless the corpus actually supports it. Use `null` when needed.

## Strong synthesis pattern

For each section:

1. State the pattern
2. Back it with multiple evidence items
3. Separate signal from interpretation
4. Capture the **exact language** that should travel into copy later

## Quality bar

- No invented demographics
- No “everyone believes” style claims from one loud thread
- No mechanism claims masquerading as facts
- No unsupported certainty

## References

- `assets/avatar_template.md`
- `../../../../schemas/avatar_profile.schema.json`
