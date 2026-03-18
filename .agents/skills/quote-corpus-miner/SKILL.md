---
name: quote-corpus-miner
description: Mine candidate quotes from reconstructed Reddit threads for pain points, struggles, failures, small wins, goals, beliefs, desires, objections, trigger moments, and raw customer language. Use after the thread corpus exists. Do not use as the final source of truth without verifying important snippets against the original thread files.
short-description: Build an evidence surface of candidate quotes and language patterns
---

# Quote Corpus Miner

This skill turns a large thread corpus into a more searchable **evidence surface**.

## Use when

- `data/threads/threads.jsonl` already exists
- the user needs candidate quotes before the avatar dossier
- the user wants customer language, objections, or trigger moments extracted at scale

## Workflow

1. Run the deterministic miner:

```bash
python scripts/extract_quote_candidates.py   --threads data/threads/threads.jsonl   --out data/evidence/quote_candidates.jsonl
```

2. Verify important snippets against `data/threads/md/*.md` before final synthesis.
3. Use the mined quotes as routing help, not as a substitute for reading the underlying threads.

## Important rules

- The heuristic miner is allowed to over-include; final synthesis must verify.
- Prefer first-person experience quotes when available.
- Preserve vivid phrasing exactly.
- When multiple categories fit, keep all category candidates rather than collapsing them too early.

## References

See `references/quote-categories.md`.
