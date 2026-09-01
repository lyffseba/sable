#!/usr/bin/env bash
# One local command. Same steps GitHub CI runs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f proto/game.js ]]; then
  if command -v node >/dev/null 2>&1; then
    node --check proto/game.js
  else
    echo "node missing — skip proto syntax" >&2
  fi
fi

python3 tools/check_protocol.py
python3 tools/license_scan.py
python3 tools/test_hid_fire.py
python3 tools/test_aim_verb.py
./tools/run_cv_tests.sh
