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
python3 tools/test_lobby.py
python3 tools/test_warmup_flow.py
./tools/run_cv_tests.sh

python3 tools/test_mojo_python.py

if command -v pixi >/dev/null 2>&1; then
  echo "Running Mojo 1.0 test suite via Pixi..."
  pixi run test-aim
  pixi run python server/tick.py
fi
