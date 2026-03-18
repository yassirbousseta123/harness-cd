\
#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <prompt-file> <schema-file> <output-json> <task-name> [extra instructions...]" >&2
  exit 1
fi

PROMPT_FILE="$1"
SCHEMA_FILE="$2"
OUTPUT_JSON="$3"
TASK_NAME="$4"
shift 4

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/outputs/logs"
mkdir -p "$LOG_DIR"

EVENT_LOG="$LOG_DIR/${TASK_NAME}.events.jsonl"
EXTRA_INSTRUCTIONS="$*"

TMP_PROMPT="$(mktemp)"
trap 'rm -f "$TMP_PROMPT"' EXIT

cat "$ROOT/$PROMPT_FILE" > "$TMP_PROMPT"
if [[ -n "$EXTRA_INSTRUCTIONS" ]]; then
  {
    printf '\n\n## Additional run-specific instructions\n'
    printf '%s\n' "$EXTRA_INSTRUCTIONS"
  } >> "$TMP_PROMPT"
fi

echo "Running Codex task: $TASK_NAME"
echo "Prompt: $PROMPT_FILE"
echo "Schema: $SCHEMA_FILE"
echo "Final message output: $OUTPUT_JSON"
echo "Event log: $EVENT_LOG"

codex exec \
  --cd "$ROOT" \
  --skip-git-repo-check \
  -p research-batch \
  --output-schema "$ROOT/$SCHEMA_FILE" \
  -o "$ROOT/$OUTPUT_JSON" \
  --json \
  - < "$TMP_PROMPT" > "$EVENT_LOG"

echo "Done: $TASK_NAME"
