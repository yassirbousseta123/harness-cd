---
name: health-ads-compliance
description: Audit health-related research outputs, landers, and ads for unsupported claims, Meta personal-attribute risk, negative-self-perception framing, and weak substantiation. Use after strategic outputs exist. This skill is a risk screen, not legal advice.
short-description: Audit health and Meta policy risk in outputs
---

# Health Ads Compliance

Use this skill to pressure-test outputs before they leave the repo.

## Use when

- a mechanism bank, lander angle bank, or ad angle bank exists
- the task is to rewrite risky phrasing into safer alternatives
- the user wants a final compliance pass

## Core checks

- Unsupported objective health claims
- “cure / treat / prevent / guaranteed result” language
- Meta personal-attribute implications
- Negative-self-perception framing
- Overstated proof from testimonials or anecdotes
- Confusing market hypotheses with substantiated science

## Workflow

1. Read the relevant output file(s).
2. Classify each risky item as:
   - `pass`
   - `risky`
   - `block`
3. Explain why.
4. Rewrite into safer language when possible.
5. Keep an explicit “proof still required” note where needed.

## Deliverable

Use `schemas/compliance_audit.schema.json` and write:

- `outputs/compliance_audit.json`
- `outputs/compliance_audit.md`

## References

See `references/risk-checklist.md`.
