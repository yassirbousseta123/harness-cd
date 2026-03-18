You are working inside the tinnitus direct-response research harness.

Goal: produce a Meta-safer ad angle bank from the avatar + mechanism outputs and the local corpus.

Use these repo assets:
- AGENTS.md
- skill: mechanism-angle-lab
- skill: health-ads-compliance
- project agent: claim_auditor

Required inputs:
- `outputs/avatar_profile.json`
- `outputs/mechanism_hypotheses.json`
- `outputs/lander_angle_bank.json` if present
- `data/evidence/quote_candidates.jsonl`
- relevant thread packs / markdown

Required behavior:
1. Read the avatar and mechanism outputs before writing angles.
2. Build ad angles that are direct-response useful but avoid:
   - personal attribute implications
   - negative-self-perception framing
   - cure/treat/prevent language
   - absolute or guaranteed outcomes
3. For each angle include:
   - hook
   - pattern interrupt
   - emotional job
   - proof device
   - CTA
   - awareness fit
   - Meta policy risk
   - safer rewrite if risky
4. `proof_device` should describe the type of proof or credibility element needed, not claim it already exists unless it is in the corpus.
5. Use `meta_policy_risk = "high"` whenever an angle plausibly implies the viewer has tinnitus or uses harsh shame/fear framing.

Deliverables:
- write `outputs/ad_angle_bank.md`
- write `outputs/ad_angle_bank.json`
- final response must be the JSON object for `outputs/ad_angle_bank.json` and must match `schemas/ad_angle_bank.schema.json`

Quality bar:
- produce 8–15 angles when supported
- ground each angle in real customer language and trigger moments
- prefer safer rewrites instead of deleting every risky idea
- do not fabricate compliance certainty

Final response rules:
- return JSON only
- ensure the final JSON exactly matches the ad angle schema
