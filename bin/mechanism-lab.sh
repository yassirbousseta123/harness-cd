#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/bin/run-codex-task.sh"   "prompts/mechanism_lab.prompt.md"   "schemas/mechanism_hypotheses.schema.json"   "outputs/mechanism_hypotheses.json"   "mechanism_lab"   "$@"
