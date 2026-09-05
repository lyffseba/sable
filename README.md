# SABLE

[![ci](https://github.com/lyffseba/sable/actions/workflows/ci.yml/badge.svg)](https://github.com/lyffseba/sable/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Open-source physical-aim arena FPS. **Apache-2.0.** Original IP only — no third-party game assets, names, maps, audio, or code. Codename only.

**Your hand is the gun.** Raise it at a MacBook lid camera, point the index, pinch or tap the pad. MediaPipe Hands (landmark 8) is primary; skin/NCC is the else path. One Euro. Gemini only seeds. Fire is HID against the `AimSample` mailbox — never gated on a camera frame. Yard spec: `docs/yard.md`. Hands audit: `research/HANDS.md`.

Stack: **Mojo 1.0** (open source, Apache-2.0 + LLVM) SIMD NCC / moments / hitscan via Pixi; **Three.js** WebGL client; C++17 reference tests. Fire stays HID-local. Native kernels run at hardware SIMD width (`std.sys.info.simd_width_of`).

## Requirements

- Modern web browser (Chrome, Edge, Safari, Firefox).
- Python 3 to serve the client locally (`python3 tools/serve_proto.py`).
- C++17 toolchain for `native/cv_input` standalone tests (`./tools/run_cv_tests.sh`).
- Built-in laptop webcam is enough. Desktop aim (**T** key) still works without a camera.

## Run SABLE

```bash
python3 tools/serve_proto.py
```
Open **http://127.0.0.1:8080** in your browser.

- **OFFLINE**: Straight into the 60s Salt House gallery on the Yard — one click. Score the clock. End state is GALLERY CLEAR.
- **ONLINE**: Waiting arena is HUD-on-Yard always-practice (thin chips, live plates). **WARM UP** is one-click local 60s without leaving the room (RETURN TO LOBBY is one click). Host **ENTER RANGE** shares the Yard gallery. Bay booth is parked — not a player mode.
- **HANDS**: MediaPipe fingertip lock. PLAY ANYWAY if the camera misses. Pinch or trackpad fires.

### Keys

| Key | Action |
|-----|--------|
| Trackpad / pinch | Fire at the **latest** `AimSample.uv` (never waits on camera) |
| **WASD** | Move on the pad (parked Bay booth only, locked during lift) |
| **L** | Cycle CANCHO outfit style (`default`, `ranked`, `night`) |
| **T** | Desktop aim toggle (OS cursor fallback) |
| **Space** | Force gun (simulates physical lift) |

Reticle may lag 50–80 ms on a bad camera. The shot does not: fire is HID against the mailbox, never gated on the next frame.

## Native aim tests

```bash
./tools/run_cv_tests.sh
```

Validates the One Euro filter, centroid extraction, coasting, and HID peek contract. Also builds via CMake if available:
```bash
cmake -S native/cv_input -B native/cv_input/build
cmake --build native/cv_input/build
./native/cv_input/build/sable_cv_tests
```

## Other computer

Latest zip: <https://github.com/lyffseba/sable/releases/latest>.

```bash
gh release download --repo lyffseba/sable -p 'sable-proto-*.zip'
unzip sable-proto-*.zip -d sable-proto && cd sable-proto
python3 serve_proto.py
```

Open http://127.0.0.1:8080 — allow camera, raise a hand, point, click the pad.

Or clone `main` and `cd proto` with the same server command. Tag `v*.*.*` publishes a new zip.

## Legal

Apache-2.0. No GPL/AGPL/SSPL in client/server. Notices: `docs/THIRD_PARTY_NOTICES.md`. Details: `docs/legal.md`. Later-migrate seams (feeling / architecture, original IP): `docs/port.md`.

## Mojo 1.0 (Pixi)

```bash
pixi install
pixi run serve      # http://127.0.0.1:8080
pixi run test-aim   # Mojo unit suite
pixi run bench      # SIMD microbenchmarks
pixi run ci         # full Python + C++ + Mojo CI
```
