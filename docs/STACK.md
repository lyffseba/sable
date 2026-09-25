# Stack

Snapshot **2026-09-25**. This is the map of tools and packages this tree actually builds, vendors, or runs. Each row names the pin in git, how that layer is used, and the latest stable official docs on the snapshot date. CI checks that this file still names the in-repo pins. It does not fetch release pages.

Workspace label in `pixi.toml` is `0.4.0`. `proto/package.json` is `0.3.0` and lists no npm dependencies. Those strings are names, not solved packages.

## Open these first

1. [Mojo — get started](https://mojolang.org/docs/manual/get-started/) (latest stable docs, **1.1.0**). The lock solves **1.0.0**: [Mojo 1.0.0 get started](https://mojolang.org/1.0.0/docs/manual/get-started/).
2. [Calling Mojo from Python](https://mojolang.org/docs/manual/python/mojo-from-python/) — `tools/sable_mojo.py` loads `native/mojo/sable_kern.mojo` through `mojo.importer`.
3. [`simd_width_of`](https://mojolang.org/docs/std/sys/info/simd_width_of/) — hardware SIMD width for NCC / moments.
4. [Pixi lock file](https://pixi.sh/latest/workspace/lock_file/) and [manifest](https://pixi.sh/latest/reference/pixi_manifest/).
5. [Hand Landmarker for web](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/web_js) — `HandLandmarker`, `detectForVideo`, model bundle.
6. [Three.js `WebGLRenderer`](https://threejs.org/docs/#api/en/renderers/WebGLRenderer) and [`MeshBasicMaterial`](https://threejs.org/docs/#api/en/materials/MeshBasicMaterial).
7. [Python `http.server`](https://docs.python.org/3/library/http.server.html) — `tools/serve_proto.py`.
8. [CMake](https://cmake.org/cmake/help/latest/) — `native/cv_input`.
9. In-repo contracts: `docs/aim_pipeline.md`, `docs/tick.md`, `docs/THIRD_PARTY_NOTICES.md`.

## Version snapshot

Latest stable means the current stable release on the vendor's own channel (not nightly, not rc). Node publishes both an Active LTS and a Current line; both are listed.

| Layer | In this tree | Latest stable on 2026-09-25 | Drift |
| --- | --- | --- | --- |
| Pixi | CLI unpinned. CI uses `prefix-dev/setup-pixi@v0.8.8` and does not set `pixi-version`. Lock schema header is `version: 6`. | [Pixi 0.81.0](https://github.com/prefix-dev/pixi/releases/tag/v0.81.0) (2026-09-15). Action [v0.10.2](https://github.com/prefix-dev/setup-pixi/releases/tag/v0.10.2) (2026-08-28). | Action tag is behind. The Pixi binary CI installs follows that action's default. |
| Mojo | `pixi.toml`: `>=1.0.0b2,<2`. Lock: `mojo-1.0.0`, `mojo-compiler-1.0.0`, `mojo-python-1.0.0` on `https://conda.modular.com/max/` plus conda-forge. Platforms `linux-64`, `osx-arm64`. | [1.1.0](https://mojolang.org/releases/v1.1.0/) (2026-09-17). Nightly is `1.2.0.dev…`, not a pin. | Lock is one stable release behind. The manifest range already accepts 1.1.x. |
| Python | `>=3.12,<3.15`. Lock: `python-3.14.7`. | [3.14.7](https://docs.python.org/3.14/) (2026-08-05), newest stable series. | Solved interpreter matches. 3.12 and 3.13 remain inside the manifest range; the lock chose 3.14.7. |
| Three.js | Vendored `proto/vendor/three.module.js`, `REVISION = '170'` (npm `three@0.170.0`, 2024-10-31). | [0.186.1 / r186](https://github.com/mrdoob/three.js/releases) (2026-09-24). Docs: [threejs.org/docs](https://threejs.org/docs/). | Sixteen revisions. Client imports the vendored module only. |
| MediaPipe Tasks Vision | Vendored `@mediapipe/tasks-vision@0.10.21` (published 2025-02-06) plus Hand Landmarker `float16/1`. CDN fallback in `proto/hands.js` is the same JS pin. | npm `latest`: [@mediapipe/tasks-vision@1.0.1](https://www.npmjs.com/package/@mediapipe/tasks-vision) (2026-07-31). npm `nightly` `1.1.0-rc.20260924` is not stable. Guide: [Hand Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker). | JS/WASM package is a major behind. Official model table still serves `float16/1`. |
| CMake | `cmake_minimum_required(VERSION 3.16)`. CI `apt` installs distro `cmake`. | [4.4.3](https://cmake.org/download/) (2026-08-25). | 3.16 is a floor. The image's CMake is the one that builds. |
| C++ compiler | C++17 (`CMAKE_CXX_STANDARD 17`, `run_cv_tests.sh -std=c++17`). Prefer `g++`. `clang++` is the fallback. No compiler version pin. | [GCC 16.2.0](https://gcc.gnu.org/gcc-16/) (2026-08-07). [LLVM/Clang 23.1.2](https://github.com/llvm/llvm-project/releases/tag/llvmorg-23.1.2) (2026-09-22). | The language standard is the pin. |
| Node.js | `tools/ci.sh` runs `node --check` on proto scripts when `node` exists. No version pin. | Active LTS [24.21.0](https://nodejs.org/en/about/previous-releases). Current [26.10.0](https://nodejs.org/docs/latest/api/) (2026-09-22). `--check`: [CLI](https://nodejs.org/docs/latest-v24.x/api/cli.html#--check). | Syntax check only. |
| `actions/checkout` | `actions/checkout@v5` in CI and release. | [v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1) (2026-07-20). | Major tag is behind. `@v5` still floats inside v5. |
| GitHub-hosted runner | `ubuntu-latest`. | On this date the label is [Ubuntu 24.04](https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md). Ubuntu 26.04 is GA; `ubuntu-latest` migrates [2026-10-19 through 2026-11-19](https://github.blog/changelog/2026-09-17-ubuntu-26-generally-available-and-latest-migration/). | The label will move. Workflows do not pin `ubuntu-24.04`. |
| Blender | Optional. `art/blender/build_sable_kit.py` says Blender 4.x. Not in CI. | [5.2.2 LTS](https://www.blender.org/releases/) (2026-09-15). [4.5.14 LTS](https://www.blender.org/releases/) is also active. API: [docs.blender.org/api/current](https://docs.blender.org/api/current/). | Comment still says 4.x. |
| GitHub CLI | Release workflow calls `gh`. Binary comes from the runner. | [2.101.0](https://github.com/cli/cli/releases/tag/v2.101.0) (2026-09-15). Manual: [cli.github.com](https://cli.github.com/manual/). | Unpinned. |

### Notable drift

- **Three.js r170 → r186** and **MediaPipe 0.10.21 → 1.0.1** are the large client gaps. Both are vendored on purpose. A refresh is a separate change from this document.
- **Mojo lock 1.0.0 → 1.1.0.** Kernels already spell `def` and `comptime`. Mojo 1.1 removed the older `fn` / `@parameter if` spellings ([1.1.0 notes](https://mojolang.org/releases/v1.1.0/)). That is not a tested bump; `pixi update` plus `pixi run test-aim` belongs in its own PR.
- **Actions:** `actions/checkout@v5` vs v7.0.1, `prefix-dev/setup-pixi@v0.8.8` vs v0.10.2.
- **Python 3.14.7 matches** the latest stable CPython.
- **CMake 3.16** is the minimum the lists accept, not the compiler CI runs.
- **Blender 4.x** in the art script vs **5.2.2 LTS**. The script is optional and outside CI.

## How this tree uses each layer

### Pixi

`pixi.toml` is the workspace. Channels are the Modular **stable** MAX channel (`https://conda.modular.com/max/`) and conda-forge. The nightly channel (`max-nightly`) is a different product. Tasks:

| Task | What it runs |
| --- | --- |
| `serve` | `python3 tools/serve_proto.py --port 8080` |
| `ci` | `./tools/ci.sh` |
| `bench` | `mojo -I native/mojo native/mojo/bench.mojo` |
| `test-aim` | `mojo -I native/mojo native/mojo/test_aim.mojo` |
| `test-py` | `python tools/test_mojo_python.py` |
| `kern` | `python tools/sable_mojo.py` |
| `tick` | `python server/tick.py` |

`pixi.lock` solves linux-64 and osx-arm64. Docs: [lock file](https://pixi.sh/latest/workspace/lock_file/), [tasks](https://pixi.sh/latest/workspace/advanced_tasks/), [install](https://pixi.sh/latest/).

### Mojo

Kernels live in `native/mojo/`. They are the SIMD path for NCC, moments, and hitscan. Product shoot stays shark-fin → `AimBus.fire()` in the browser and does not wait on these kernels.

| Import in tree | Role | Latest stable API |
| --- | --- | --- |
| `std.sys.info.simd_width_of` | Width of the NCC / moments loops | [`simd_width_of`](https://mojolang.org/docs/std/sys/info/simd_width_of/) |
| `std.math.sqrt` | Hitscan and NCC | [`sqrt`](https://mojolang.org/docs/std/math/math/sqrt/) |
| `std.time.perf_counter_ns` | `bench.mojo` | [`perf_counter_ns`](https://mojolang.org/docs/std/time/time/perf_counter_ns/) |
| `std.python` / `PythonModuleBuilder` | `sable_kern.mojo` extension | [bindings](https://mojolang.org/docs/std/python/bindings/PythonModuleBuilder/), [from Python](https://mojolang.org/docs/manual/python/mojo-from-python/) |
| `std.os.abort` | Extension init failure | [`std.os`](https://mojolang.org/docs/std/os/) |

Index: [standard library](https://mojolang.org/docs/std/). Releases: [mojolang.org/releases](https://mojolang.org/releases/). Install: [mojolang.org/install](https://mojolang.org/install/).

### Python

Direct dependencies are the stdlib plus Mojo when Pixi is installed. `tools/serve_proto.py` is a `ThreadingHTTPServer` for `proto/` and the JSON lobby / mojo routes ([`http.server`](https://docs.python.org/3/library/http.server.html)). `server/tick.py` is the 128 Hz headless stepper ([`docs/tick.md`](tick.md)); it calls `tools/sable_mojo.py` and sleeps with the stdlib. Tests under `tools/` are stdlib `pathlib` / `re` / `sys`.

Language docs for the solved series: [docs.python.org/3.14](https://docs.python.org/3.14/). What's new: [3.14](https://docs.python.org/3/whatsnew/3.14.html).

### Three.js

`proto/aim.js` and `proto/house.js` import `./vendor/three.module.js`. The house builds a `WebGLRenderer` and unshaded `MeshBasicMaterial` meshes (CANCHO look). There is no npm install and no `three.webgpu.js`. Manual: [threejs.org/manual](https://threejs.org/manual/). Migration notes when re-vendoring: [Migration Guide](https://github.com/mrdoob/three.js/wiki/Migration-Guide).

### MediaPipe Tasks Vision

`proto/hands_worker.js` is a classic worker. It imports `vision_bundle.mjs`, builds `FilesetResolver.forVisionTasks`, then `HandLandmarker.createFromOptions` (GPU, then CPU) and calls `detectForVideo`. `proto/hands.js` tries the vendored files first:

- `proto/vendor/mediapipe/vision_bundle.mjs`
- `proto/vendor/mediapipe/wasm/`
- `proto/vendor/mediapipe/hand_landmarker.task` (`float16/1`)

The CDN strings in `hands.js` are a fallback at the same `@mediapipe/tasks-vision@0.10.21` pin, plus the Google model host for `float16/1`. Release zip checks in `tools/ci.sh` require the vendored files to be non-empty. API: [`HandLandmarker`](https://developers.google.com/edge/api/mediapipe/js/tasks-vision.handlandmarker). Upstream repo: [google-ai-edge/mediapipe](https://github.com/google-ai-edge/mediapipe).

### C++17 and CMake

`native/cv_input` is the reference aim pipeline (One Euro, centroid, coast, HID peek tests). `CMakeLists.txt` asks for CMake 3.16, C++17, and `Threads::Threads` ([FindThreads](https://cmake.org/cmake/help/latest/module/FindThreads.html)). `tools/run_cv_tests.sh` uses CMake when it is on `PATH`, otherwise compiles with `g++` or `clang++ -std=c++17`.

`src/capture.cpp` speaks Linux V4L2 and prefers YUY2 ([V4L2](https://docs.kernel.org/userspace-api/media/v4l/v4l2.html)). OpenCV is not linked. The optional `-DSABLE_GODOT_CPP=` hook is not a solved dependency; Godot is not in this tree.

Language: [C++17](https://en.cppreference.com/w/cpp/17). Compilers: [GCC 16.2](https://gcc.gnu.org/onlinedocs/gcc-16.2.0/gcc/), [Clang user's manual](https://clang.llvm.org/docs/UsersManual.html).

### Browser

Ship floor is Chromium on a MacBook Pro–class lid camera. No browser version is pinned. The client uses:

| API | Where | Docs |
| --- | --- | --- |
| `getUserMedia` | `proto/boot.js` — camera is a hidden `<video>`, never drawn | [MDN](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia) |
| WebGL via Three | `proto/house.js` | [WebGL](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API) |
| Classic `Worker` | `proto/hands_worker.js` (`importScripts` in the wasm glue; not `type=module`) | [Workers](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API) |
| `requestAnimationFrame` | `proto/boot.js` render loop | [rAF](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame) |

Chromium project: [chromium.org](https://www.chromium.org/Home/).

### Node.js

Only `node --check` in `tools/ci.sh`, and only when a `node` binary exists. Proto is not a Node app.

### GitHub Actions

`.github/workflows/ci.yml` and `release.yml` share checkout v5, `prefix-dev/setup-pixi@v0.8.8`, `ubuntu-latest`, and `pixi run ci`. Release then zips `proto/` plus `tools/serve_proto.py`, `tools/sable_mojo.py`, and `tools/lobby.py`, and publishes with `gh`. Actions docs: [GitHub Actions](https://docs.github.com/en/actions). Runners: [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

### Blender

`art/blender/build_sable_kit.py` runs inside Blender (`bpy`: cube primitives, Principled BSDF, GLB export). Paint sheets stay SVG. Runtime meshes stay `proto/house.js`. This path is outside CI.

### Lock companions

These conda packages are solved because the Mojo 1.0 package pulls a Python tooling stack. SABLE tasks do not import them. Their versions move when Mojo's package moves. System libraries in `pixi.lock` (OpenSSL, libffi, ncurses, and the rest) stay in the lock and are not repeated here.

| Package | Lock |
| --- | --- |
| mblack | 26.5.0 |
| click | 8.4.2 |
| jupyter_client | 8.6.3 |
| jupyter_core | 5.9.1 |
| pyzmq | 27.2.0 |
| zeromq | 4.3.5 |
| tornado | 6.5.8 |
| traitlets | 5.16.1 |
| importlib-metadata | 9.0.1 |
| packaging | 26.3 |
| mypy_extensions | 1.1.0 |
| pathspec | 1.1.1 |
| platformdirs | 4.11.6 |
| python-dateutil | 2.9.0.post0 |
| six | 1.17.0 |
| tomli | 2.4.1 |
| zipp | 4.1.0 |

## Maintenance

Update this file in the same change that bumps a pin, re-vendors Three or MediaPipe, or edits a `uses:` line. Read, in order:

1. `pixi.toml` and the `mojo-` / `python-` lines in `pixi.lock`
2. `REVISION` in `proto/vendor/three.module.js`
3. The `@mediapipe/tasks-vision@` string in `proto/hands.js`
4. `cmake_minimum_required` in `native/cv_input/CMakeLists.txt`
5. `.github/workflows/ci.yml` and `release.yml`
6. The official release page linked in the row (manual). Write the new latest-stable column and set the snapshot date at the top.

`tools/check_stack_doc.py` (from `./tools/ci.sh`) checks that `docs/STACK.md` exists, that `README.md` links it, that the headings below are present, and that the in-repo pin strings plus the snapshot markers in that script still appear. Refreshing the comparison column means editing the markers in the script in the same commit. The script reads the work tree only.

Keep the Hand Landmarker self-hosted, with the CDN fallback pinned to the same tasks-vision version as the vendor copy (`research/HAND_FUTURE.md`). Keep the Pixi channel on `conda.modular.com/max`, not the nightly channel.

Out of this solved set: OpenCV (not linked), Godot (not in the tree), a vendored Steamworks SDK, kernel anti-cheat.
