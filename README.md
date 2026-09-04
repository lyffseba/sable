# SABLE

Private. Original IP. Do **not** add third-party game assets, names, maps, audio, or code. Codename only — do not write the eventual public title into this repository.

Physical-aim arena FPS. Lightweight wireless mouse on the pad = move / menus. The player **lifts** the mouse and points it at the monitor. A clip-on webcam at the **top-center** of the monitor tracks a **2–3-dot** (or 40 mm ArUco) sleeve on the mouse. Click (HID) fires. Unique verb = physical ADS.

Neon tape is a temporary blob fallback, not the product.

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

- **RANGE**: 60-second arcade wave. Lift the mouse, point, and click.
- **BAY 1v1**: 3D duel arena vs CANCHO capsule. WASD moves on pad, lift mouse locks walk to shoot, use cover to avoid open-middle exposure.

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

Latest zip: <https://github.com/lyffseba/sable/releases/latest> (private — log in as lyffseba).

```bash
gh release download --repo lyffseba/sable -p 'sable-proto-*.zip'
unzip sable-proto-*.zip -d sable-proto && cd sable-proto
python3 serve_proto.py
```

Open http://127.0.0.1:8080 — allow camera, tilt down at hands, lift.

Or clone `main` and `cd proto` with the same server command. Tag `v*.*.*` publishes a new zip.

## Legal red line

Proprietary game content. No GPL in client/server. Godot MIT notice: `docs/THIRD_PARTY_NOTICES.md`. Fan licenses are not commercial. Details: `docs/legal.md`.
