# Thread Merge Methodology

Read when:
- ingesting a new Arctic Shift subreddit export
- changing merge or normalization behavior
- debugging missing threads, missing comments, or weird depth/orphan counts
- interpreting `orphan_threads.jsonl` or `orphan_thread_index.csv`

## Purpose

Turn separate Reddit submissions/posts and comments exports into deterministic, thread-first research artifacts that are practical to read and safe to audit.

## Inputs

Required pair for one scope:
- submissions/posts export: `.jsonl`, `.ndjson`, `.json`, or `.zst`
- comments export: `.jsonl`, `.ndjson`, `.json`, or `.zst`

Example:
- `data/raw/tinnitus/r_Tinnitus_posts.jsonl`
- `data/raw/tinnitus/r_Tinnitus_comments.jsonl`

## Canonical Outputs

Primary:
- `data/intermediate/reddit.db`
- `data/threads/threads.jsonl`
- `data/threads/thread_index.csv`
- `data/threads/md/*.md`

Missing-post preservation:
- `data/threads/orphan_threads.jsonl`
- `data/threads/orphan_thread_index.csv`
- `data/threads/orphans_md/*.md`

## Merge Rules

1. Submission identity:
   - normalize `submission.id` or `submission.name`
   - canonical emitted thread id is `t3_<submission_id>`

2. Comment-to-thread attachment:
   - normalize `comment.link_id`
   - attach comment bundle to the submission whose normalized id matches that `link_id`

3. Comment nesting:
   - rebuild tree from `comment.parent_id`
   - if parent comment exists in the same bundle, nest under it
   - if parent comment is missing, keep the comment as a top-level orphan root and count it in `orphaned_root_count`

4. Missing-post handling:
   - if comments reference a `link_id` with no matching submission export row, preserve them
   - emit that bundle into orphan artifacts instead of dropping it
   - orphan markdown uses `[missing submission]` and `[submission missing from source export]`

5. Sorting:
   - normal threads sorted by submission `created_utc`, tie-broken by submission id
   - orphan threads sorted by earliest comment `created_utc`, tie-broken by thread id
   - comments sorted by `created_utc`, tie-broken by comment id
   - flattened output order is depth-first after the tree is rebuilt

6. Normalization:
   - ids normalized from fullname or bare id
   - numeric fields coerced when possible
   - text fields pass through `collapse_whitespace`, so repeated whitespace/newlines collapse to single spaces

7. Drop behavior:
   - records missing parseable ids are skipped
   - comments missing parseable `link_id` are skipped
   - comments are not dropped just because the post is missing; they move to orphan outputs

## Why Two Orphan Concepts Exist

- `orphaned_root_count` inside a normal thread: post exists, but one or more parent comments are missing
- `orphan_threads.jsonl`: comments exist, but the submission/post record is missing entirely

These are different failure modes. Keep both visible.

## Verified `r/tinnitus` Run

Verified on March 18, 2026 with:
- `22,456` submissions parsed
- `252,377` comments parsed

Actual deterministic ingest result:
- `22,456` normal threads
- `246,327` comments linked into normal threads
- `1,872` orphan threads
- `6,050` comments preserved in orphan threads

## Operational Rule

For research and synthesis, read thread artifacts first. Do not read posts and comments as separate raw files once thread artifacts exist.
