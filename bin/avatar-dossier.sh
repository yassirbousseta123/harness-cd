#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/bin/run-codex-task.sh"   "prompts/avatar_dossier.prompt.md"   "schemas/avatar_profile.schema.json"   "outputs/avatar_profile.json"   "avatar_dossier"   "$@"
