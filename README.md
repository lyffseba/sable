# SABLE

Private. Original IP. Do **not** add third-party game assets, names, maps, audio, or code. Codename only — do not write the eventual public title into this repository.

Physical-aim arena FPS. Lightweight wireless mouse on the pad = move / menus. The player **lifts** the mouse and points it at the monitor. A clip-on webcam at the **top-center** of the monitor tracks a **2–3-dot** (or 40 mm ArUco) sleeve on the mouse. Click (HID) fires. Unique verb = physical ADS.

Neon tape is a temporary blob fallback, not the product.

## Requirements

- **Godot 4.7.2** (Forward+, Jolt). Open the `godot/` folder as the project.
- C++17 toolchain to build `native/cv_input` tests and, later, the GDExtension.
- A clip-on webcam is optional. The Range is always testable with desktop aim.

## Open in Godot 4.7

1. Install Godot **4.7.2**.
2. Import `godot/project.godot`.
3. Run the main scene (`scenes/boot/Boot.tscn`).
4. **Enter Range** — or **Enable camera** (binds `cv_input` if the extension loaded; otherwise stays on DESKTOP aim).

### Range keys

| Key | Action |
|-----|--------|
| Mouse click | Fire at the **latest** `AimSample.uv` |
| **T** | Desktop aim (OS cursor) |
| **Space** | Force gun (lifted) |

Reticle may lag 50–80 ms on a bad camera. The shot does not: fire is HID against the mailbox, never gated on the next frame.

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

GDExtension (macOS dylib, godot-cpp **outside** this repo — no 4.7 tag, use `master` + API 4.7):

```bash
git clone --depth 1 --branch master https://github.com/godotengine/godot-cpp.git ../godot-cpp
cmake -S native/cv_input -B native/cv_input/build \
  -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_OSX_ARCHITECTURES=x86_64 \
  -DSABLE_GODOT_CPP="$PWD/../godot-cpp" \
  -DGODOTCPP_API_VERSION=4.7 \
  -DGODOTCPP_TARGET=template_debug
cmake --build native/cv_input/build --target cv_input
```

Output: `native/cv_input/bin/libcv_input.macos.debug.dylib` (gitignored). Linux V4L2 first (YUY2 preferred, MJPEG fallback). Windows Media Foundation later. See `native/cv_input/README.md` and `docs/aim_pipeline.md`.

## Legal red line

Proprietary game content. No GPL in client/server. Godot MIT notice: `docs/THIRD_PARTY_NOTICES.md`. Fan licenses are not commercial. Details: `docs/legal.md`.
