# SABLE

Private. Original IP. Do **not** add third-party game assets, names, maps, audio, or code. Codename only — do not write the eventual public title into this repository.

Physical-aim arena FPS. Lift the Superlight, point it at the monitor, click. Webcam pose is the gun. Fire is HID.

## Engine

**Unity 2022.3 LTS** (`unity/`). Open that folder in Unity Hub. Godot is not in this tree.

This G14 has **no Unity Editor and no Unreal**. Unity is the right install: the webcam tracker we vendored is Unity compute shaders. Unreal would be 50–100 GB for no gain on the gun.

Until Hub is installed, the Chrome proto still plays:

```
python3 tools/serve_proto.py
```

### Range keys

| Key | Action |
|-----|--------|
| Mouse click | Fire at the **latest** `AimSample.uv` |
| **T** | Desktop aim (OS cursor) |
| **Space** | Force gun (lifted) |

The shot never waits on a camera frame.

## Headless dedicated server

```bash
# Editor / official binary, from repo root
export GODOT_BIN="${GODOT_BIN:-godot}"
"$GODOT_BIN" --headless --path godot

# Or:
./tools/headless_tick.sh
```

Export preset: **Linux Dedicated Server** in `godot/export_presets.cfg`. See `server/README.md`.

## Native aim plugin

```bash
cmake -S native/cv_input -B native/cv_input/build
cmake --build native/cv_input/build
./native/cv_input/build/sable_cv_tests
```

Linux V4L2 first (YUY2 preferred, MJPEG fallback). Windows Media Foundation later. See `native/cv_input/README.md` and `docs/aim_pipeline.md`.

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
