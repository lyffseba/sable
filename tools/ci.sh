#!/usr/bin/env bash
# One local command. Same steps GitHub CI runs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if command -v node >/dev/null 2>&1; then
  for f in proto/aim.js proto/hands.js proto/hands_worker.js proto/house.js proto/boot.js proto/audio.js proto/port.js proto/game.js; do
    if [[ -f "$f" ]]; then
      node --check "$f"
    fi
  done
else
  echo "node missing — skip proto syntax" >&2
fi

# Release zip is self-contained: Hand Landmarker must not depend on CDN.
test -s proto/vendor/mediapipe/vision_bundle.mjs
test -s proto/vendor/mediapipe/hand_landmarker.task
test -s proto/vendor/mediapipe/wasm/vision_wasm_internal.js
test -s proto/vendor/mediapipe/wasm/vision_wasm_internal.wasm
test -s proto/vendor/mediapipe/wasm/vision_wasm_nosimd_internal.js
test -s proto/vendor/mediapipe/wasm/vision_wasm_nosimd_internal.wasm

python3 tools/check_protocol.py
python3 tools/license_scan.py
python3 tools/test_hid_fire.py
python3 tools/test_aim_verb.py
python3 tools/test_lobby.py
python3 tools/test_warmup_flow.py
python3 tools/test_shared_range.py
python3 tools/test_sableqa_offline.py
python3 tools/test_tick_contract.py
python3 tools/test_hands_worker.py
python3 tools/test_sableperf.py
python3 tools/test_bay_playlist.py
python3 tools/test_bay_r6.py
python3 tools/test_shared_bay.py
python3 tools/test_gallery_mode.py
python3 tools/test_sablehud.py
python3 tools/test_sableaudio.py
python3 tools/test_sablelobby.py
# SableLook / SableYard: bone plates readable vs charcoal/rust bunkers.
python3 tools/test_sablelook.py
python3 tools/test_sableyard.py
# SablePort: fail loud if Valve/Epic DNA lands in runtime art.
python3 tools/test_sableport.py
./tools/run_cv_tests.sh

python3 tools/test_mojo_python.py

if command -v pixi >/dev/null 2>&1; then
  echo "Running Mojo 1.0 test suite via Pixi..."
  pixi run test-aim
  pixi run python server/tick.py
fi
