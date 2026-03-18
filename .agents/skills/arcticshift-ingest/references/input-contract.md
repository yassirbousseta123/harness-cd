# Input contract

Supported inputs:

- `.jsonl`
- `.ndjson`
- `.json`
- `.zst`

The harness expects a submissions file and a comments file for the same scope.

Thread reconstruction assumptions used by the deterministic scripts:

- a submission becomes one `thread_id`
- comments are attached to a submission via `link_id`
- comment nesting is rebuilt from `parent_id`
- missing parents become orphan roots and are counted

Generated artifacts should be treated as the working corpus for Codex.
