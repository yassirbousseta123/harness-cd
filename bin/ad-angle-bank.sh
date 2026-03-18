#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/bin/run-codex-task.sh"   "prompts/ad_angle_bank.prompt.md"   "schemas/ad_angle_bank.schema.json"   "outputs/ad_angle_bank.json"   "ad_angle_bank"   "$@"
