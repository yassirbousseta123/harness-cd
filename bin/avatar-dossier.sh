#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/bin/run-codex-task.sh"   "prompts/avatar_dossier.prompt.md"   "schemas/report_state.schema.json"   "outputs/report_state.json"   "avatar_dossier_founder_grade"   "$@"
