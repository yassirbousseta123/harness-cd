---
name: arcticshift-ingest
description: Prepare local Reddit corpora from Arctic Shift exports. Use when submissions/comments dumps or JSONL files need to be reconstructed into SQLite, thread JSONL, thread markdown, selected subsets, or research packs before analysis. Do not use for final synthesis, copy generation, or compliance review.
short-description: Convert Arctic Shift exports into deterministic thread artifacts for Codex
---

# Arctic Shift Ingest

This skill is for **deterministic local corpus prep**.

## Use when

- raw `.zst`, `.jsonl`, `.ndjson`, or `.json` exports exist
- `data/threads/threads.jsonl` or `data/threads/md/` is missing
- the user wants packs or manifests before analysis
- the user wants a filtered subset of the corpus

## Do not use when

- the corpus is already prepared and the task is synthesis
- the task is the avatar dossier, mechanism work, lander angles, or compliance review

## Expected outputs

Default outputs:

- `data/intermediate/reddit.db`
- `data/threads/threads.jsonl`
- `data/threads/thread_index.csv`
- `data/threads/md/*.md`

Optional downstream outputs:

- `data/packs/*.md`
- `data/packs/pack_manifest.csv`

## Workflow

1. Read `data/README.md`.
2. Confirm the input paths for submissions and comments.
3. Run the deterministic script instead of writing a one-off parser:

```bash
python scripts/ingest_arcticshift.py   --submissions <path/to/submissions>   --comments <path/to/comments>   --sqlite data/intermediate/reddit.db   --threads-jsonl data/threads/threads.jsonl   --threads-md-dir data/threads/md   --manifest data/threads/thread_index.csv
```

4. If the user needs a narrower slice, run:

```bash
python scripts/sample_threads.py --help
```

5. If the user needs larger reading bundles for Codex, build packs:

```bash
python scripts/build_research_packs.py   --threads data/threads/threads.jsonl   --out-dir data/packs   --manifest data/packs/pack_manifest.csv
```

6. Spot-check at least one thread markdown file and the manifest count before saying the corpus is ready.

## Quality bar

- Do not manually rearrange thread trees.
- Do not hand-edit generated thread markdown.
- Surface orphan counts if parents are missing.
- Prefer preserving raw text over “cleaning it up.”

## References

See:

- `references/input-contract.md`
- `references/pack-format.md`
