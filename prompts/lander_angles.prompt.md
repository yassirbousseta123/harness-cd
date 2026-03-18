You are working inside the tinnitus direct-response research harness.

Goal: produce an evidence-backed landing-page angle bank that fits the avatar and mechanism work without drifting into risky health claims.

Use these repo assets:
- AGENTS.md
- skill: mechanism-angle-lab
- skill: health-ads-compliance
- project agent: claim_auditor

Required inputs:
- `outputs/avatar_profile.json`
- `outputs/mechanism_hypotheses.json`
- `data/evidence/quote_candidates.jsonl`
- relevant thread packs / markdown

Required behavior:
1. Read the avatar and mechanism outputs first.
2. Build landing-page angles that are emotionally resonant and evidence-backed.
3. Each angle must include:
   - big idea
   - opening move
   - emotional job
   - proof stack
   - objection handling
   - CTA theme
   - awareness fit
   - risk flags
4. Favor specific, vivid, lower-risk framing over broad promises.
5. If an angle risks implying diagnosis, cure, or guaranteed relief, flag it in `risk_flags` and soften the language.

Deliverables:
- write `outputs/lander_angles.md`
- write `outputs/lander_angle_bank.json`
- final response must be the JSON object for `outputs/lander_angle_bank.json` and must match `schemas/lander_angle_bank.schema.json`

Quality bar:
- produce 6–10 angles if the corpus supports it
- each angle should have multiple evidence items where possible
- proof stacks should mention proof types, not fabricated evidence
- objection handling should reflect real objections from the corpus

Final response rules:
- return JSON only
- ensure the final JSON exactly matches the lander schema
