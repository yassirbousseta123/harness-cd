# Data layout

Place raw Arctic Shift exports in `data/raw/`.

Recommended conventions:

- `data/raw/<topic>/<subreddit>_submissions.jsonl`
- `data/raw/<topic>/<subreddit>_comments.jsonl`
- or the original `.zst` dump pair from Arctic Shift

Generated paths:

- `data/intermediate/reddit.db` — SQLite cache used for deterministic reconstruction
- `data/intermediate/ingest_registry.json` — raw-pair registry for incremental refreshes
- `data/threads/threads.jsonl` — one JSON object per reconstructed submission thread
- `data/threads/thread_index.csv` — manifest with counts and markdown paths
- `data/threads/md/*.md` — one markdown file per thread
- `data/threads/orphan_threads.jsonl` — comment bundles whose `link_id` has no matching submission row
- `data/threads/orphan_thread_index.csv` — manifest for orphan thread bundles
- `data/threads/orphans_md/*.md` — markdown for missing-post orphan bundles
- `data/packs/*.md` — larger bundles of many threads for Codex reading
- `data/evidence/quote_candidates.jsonl` — heuristic evidence snippets
- `data/avatar_states/<avatar_id>/` — avatar/state-cluster workspaces, reports, and packs
