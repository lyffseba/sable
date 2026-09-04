#!/usr/bin/env bash
# 128 Hz dedicated tick (Mojo hitscan when Pixi is available).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if command -v pixi >/dev/null 2>&1; then
  exec pixi run python server/tick.py
fi
exec python3 "$ROOT/server/tick.py"
