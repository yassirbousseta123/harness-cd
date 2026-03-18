You are working inside the tinnitus direct-response research harness.

Goal: audit the current output set for health-claim, Meta, and substantiation risk.

Use these repo assets:
- AGENTS.md
- skill: health-ads-compliance
- project agent: claim_auditor

Audit these files when they exist:
- `outputs/avatar_dossier.md`
- `outputs/avatar_profile.json`
- `outputs/mechanism_hypotheses.md`
- `outputs/mechanism_hypotheses.json`
- `outputs/lander_angles.md`
- `outputs/lander_angle_bank.json`
- `outputs/ad_angle_bank.md`
- `outputs/ad_angle_bank.json`

Required behavior:
1. Read the output files directly.
2. Flag issues in three buckets:
   - pass
   - risky
   - block
3. Prioritize:
   - implied personal attribute violations
   - negative self-perception hooks
   - objective health claims needing proof
   - time-bound / guaranteed outcome claims
   - unsupported scientific mechanisms
   - thin evidence presented as certainty
4. Provide a specific fix for every risky or blocked item.
5. Keep this audit practical: the goal is to save good work, not just reject it.

Deliverables:
- write `outputs/compliance_audit.md`
- write `outputs/compliance_audit.json`
- final response must be the JSON object for `outputs/compliance_audit.json` and must match `schemas/compliance_audit.schema.json`

Quality bar:
- cite the asset type and asset name for every issue
- suggested fixes should be surgical, not generic
- if proof is required, say what type of proof is missing
- if there are no files to audit, say so explicitly in the summary and produce a high-risk audit due to missing artifacts

Final response rules:
- return JSON only
- ensure the final JSON exactly matches the compliance audit schema
