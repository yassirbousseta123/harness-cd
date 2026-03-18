You are working inside the tinnitus direct-response research harness.

Goal: turn the avatar dossier + corpus evidence into mechanism theses and offer hypotheses without overclaiming.

Use these repo assets:
- AGENTS.md
- skill: mechanism-angle-lab
- skill: health-ads-compliance
- project agent: claim_auditor

Required inputs:
- `outputs/avatar_profile.json`
- `outputs/avatar_dossier.md`
- `data/evidence/quote_candidates.jsonl`
- `data/packs/pack_manifest.csv` and relevant pack files if present
- `data/threads/thread_index.csv`

Required behavior:
1. Read the avatar output first.
2. Generate mechanism theses in 3 buckets when supported:
   - market
   - identity
   - scientific
3. Keep scientific mechanism hypotheses clearly labeled as hypotheses unless the local corpus itself is only being used to explain resonance rather than medical fact.
4. For every hypothesis, list:
   - why it resonates
   - proof required
   - disconfirming signals
   - risk flags
5. Add offer hypotheses that map to awareness and objection patterns.
6. Run a skeptical pass with `claim_auditor` before finalizing.

Deliverables:
- write `outputs/mechanism_hypotheses.md`
- write `outputs/mechanism_hypotheses.json`
- final response must be the JSON object for `outputs/mechanism_hypotheses.json` and must match `schemas/mechanism_hypotheses.schema.json`

Quality bar:
- prefer 5–9 mechanism theses total
- prefer 3–6 offer hypotheses
- do not present a medical cure story
- do not hide proof gaps
- every evidence item must cite a real thread and explain why it supports the thesis

Final response rules:
- return JSON only
- ensure the final JSON exactly matches the mechanism schema
