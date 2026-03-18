You are working inside the tinnitus direct-response research harness.

Goal: produce an evidence-backed avatar dossier from the local Reddit corpus.

Use these repo assets:
- AGENTS.md
- skill: avatar-deep-dive
- skill: quote-corpus-miner
- project agents when useful: corpus_mapper, quote_analyst, claim_auditor

Required behavior:
1. If `data/threads/threads.jsonl` is missing, build it with the deterministic ingest scripts before synthesis.
2. If `data/evidence/quote_candidates.jsonl` is missing, generate it before synthesis.
3. Read:
   - `data/threads/thread_index.csv`
   - `data/packs/pack_manifest.csv` if it exists
   - a representative slice of packs and/or per-thread markdown
   - `data/evidence/quote_candidates.jsonl`
4. Prefer multiple supporting threads per major claim.
5. Do not guess age or gender. Use `null` with low confidence when evidence is weak.
6. Separate observed signal from inference in the markdown write-up.
7. Keep health-claim language out of the avatar. This is customer understanding, not efficacy copy.

Deliverables:
- write `outputs/avatar_dossier.md`
- write `outputs/avatar_profile.json`
- final response must be the JSON object for `outputs/avatar_profile.json` and must match `schemas/avatar_profile.schema.json`

Quality bar:
- use thread-level evidence arrays everywhere the schema expects them
- give at least 3 pain points, 3 day-to-day struggles, 2 victories, 3 failures, 3 goals, 3 beliefs, 2 desire chains, 3 objections, 5 real customer language items, 3 trigger moments when the corpus supports it
- if the corpus does not support a section strongly, keep the section but lower confidence and explain the gap
- every `why_it_supports` should say why the quote matters, not restate the quote

Markdown structure for `outputs/avatar_dossier.md`:
- executive summary
- source coverage
- each requested avatar section
- gaps and unknowns
- next research questions

Final response rules:
- return JSON only
- ensure the final JSON exactly matches the avatar schema
