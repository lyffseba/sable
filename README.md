# SABLE

**Apache-2.0 open source.** Original IP. Do **not** add third-party game assets, names, maps, audio, or code. Codename only.

Physical-aim arena FPS. Lightweight wireless mouse on the pad = move / menus. The player **lifts** the mouse and points it at the monitor. A clip-on webcam at the **top-center** of the monitor tracks the mouse muzzle via **Gemini 3.8 Flash** zero-shot spatial vision + client-side One Euro pointing filter. Click (HID) fires instantly. Unique verb = physical ADS.

Zero external engine installs. Web-native 3D WebGL (Three.js) + Mojo 1.0 SIMD kernels (Pixi). Sub-millisecond HID fire.

## Requirements

- Modern web browser (Chrome, Edge, Safari, Firefox).
- Python 3 to serve the client locally (`python3 tools/serve_proto.py`).
- C++17 toolchain for `native/cv_input` standalone tests (`./tools/run_cv_tests.sh`).
- A clip-on webcam is optional. The game is always testable with desktop aim (**T** key).

## Run SABLE

```bash
python3 tools/serve_proto.py
```
Open **http://127.0.0.1:8080** in your browser.

- **RANGE (3D)**: 60-second arcade wave with floating 3D crystalline targets, shattered fragments, and first-person gun ADS lift animation.
- **BAY 1v1 (3D)**: Full 3D arena duel vs CANCHO bot. WASD moves on pad; lifting mouse locks walk to aim and shoot; use window/angle cover to avoid open-middle sniper fire.
- **AI MUZZLE LOCK**: Click the button on the lock screen for instant zero-shot Gemini 3.8 Flash muzzle detection.

### Keys

| Key | Action |
|-----|--------|
| Mouse click | Fire at the **latest** `AimSample.uv` (HID click, never waits on camera) |
| **WASD** | Move on the pad (Bay 1v1 mode only, locked during lift) |
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

Open http://127.0.0.1:8080 — allow camera, tilt down at hands, lift.

Or clone `main` and `cd proto` with the same server command. Tag `v*.*.*` publishes a new zip.

## Legal

Apache-2.0. No GPL/AGPL/SSPL in client/server. Notices: `docs/THIRD_PARTY_NOTICES.md`. Details: `docs/legal.md`.

## Mojo 1.0 (Pixi)

```bash
pixi install
pixi run serve      # http://127.0.0.1:8080
pixi run test-aim   # Mojo unit suite
pixi run bench      # SIMD microbenchmarks
pixi run ci         # full Python + C++ + Mojo CI
```
