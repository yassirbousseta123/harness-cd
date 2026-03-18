---
name: mechanism-angle-lab
description: Convert an evidence-backed avatar dossier into mechanism hypotheses, landing-page angles, and ad angle banks. Use only after the avatar dossier exists. Treat market mechanisms and scientific mechanisms separately, and do not turn hypotheses into substantiated health claims.
short-description: Turn avatar evidence into mechanism and angle banks
---

# Mechanism + Angle Lab

This skill is where evidence becomes strategy.

## Use when

- `outputs/avatar_profile.json` already exists
- the user wants hypotheses, lander angles, or ad angles
- the task is strategic conversion work, not raw corpus prep

## Distinguish these two things

### Market mechanism
How the market talks about the problem, why current solutions disappoint, and why a new frame might create intrigue.

### Scientific mechanism
A biological or technical explanation. This requires real substantiation and should usually be treated as:
- a research question
- a proof requirement
- a risk item

Do not blur these together.

## Required deliverables

Depending on the task:

- `outputs/mechanism_hypotheses.json`
- `outputs/mechanism_hypotheses.md`
- `outputs/lander_angle_bank.json`
- `outputs/lander_angle_bank.md`
- `outputs/ad_angle_bank.json`
- `outputs/ad_angle_bank.md`

Use the schemas in `schemas/`.

## Workflow

1. Read `outputs/avatar_profile.json`.
2. Pull supporting evidence from `data/evidence/quote_candidates.jsonl` and thread markdown when needed.
3. Generate hypotheses that stay grounded in customer language.
4. Keep proof requirements visible.
5. Mark risk flags when an angle drifts toward a health claim or a sensitive-personal-attribute implication.
6. Prefer angle banks and testable hooks over fully polished claims.

## Quality bar

- No fake certainty
- No “unique mechanism” phrasing unless genuinely supported
- No copying generic supplement clichés into the output
- Keep “copy angle worth testing” separate from “claim safe to make”

## References

- `assets/mechanism_template.md`
- `assets/lander_template.md`
- `assets/ad_angle_template.md`
