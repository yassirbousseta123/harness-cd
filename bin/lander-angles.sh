#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/bin/run-codex-task.sh"   "prompts/lander_angles.prompt.md"   "schemas/lander_angle_bank.schema.json"   "outputs/lander_angle_bank.json"   "lander_angles"   "$@"
