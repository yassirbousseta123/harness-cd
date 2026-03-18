#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/bin/run-codex-task.sh"   "prompts/compliance_audit.prompt.md"   "schemas/compliance_audit.schema.json"   "outputs/compliance_audit.json"   "compliance_audit"   "$@"
