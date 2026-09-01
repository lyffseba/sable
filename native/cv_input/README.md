# cv_input

Native aim plugin for SABLE. This is the engine's heart.

C++17. **No OpenCV required** for the filter, tests, or YUY2 path. OpenCV is optional later for MJPEG decode and PnP.

## Build

CMake. Prefer `g++` if `c++` is Clang without a C++ stdlib:

```bash
cmake -S . -B build -DCMAKE_CXX_COMPILER=g++
cmake --build build
./build/sable_cv_tests
```

That binary is the contract: synthetic 720p-class noise, dropouts, AE pops, coast, HID fire. No webcam.

## Layout

| Path | Role |
|------|------|
| `include/sable/aim_sample.hpp` | `AimSample { uv, valid, lifted, confidence, t_hw }` |
| `include/sable/one_euro.hpp` | Casiez 2012, pointing constants |
| `include/sable/pipeline.hpp` | ROI, moments, HSV, coast, outliers, quality |
| `include/sable/aim_bus.hpp` | Latest-sample mailbox; `fire()` peeks |
| `src/capture.cpp` | Worker thread, V4L2 YUY2, drop-old, `make_capture()` |
| `src/capture_avf.mm` | macOS AVFoundation, 32BGRA, drop-old |
| `src/cv_input_c_api.cpp` | Stable C ABI |
| `src/register_types.cpp` | GDExtension (needs godot-cpp) |
| `tests/test_aim.cpp` | No-webcam tests |

## Capture

- Linux **V4L2**. Prefer **YUY2**. MJPEG is fallback (skipped until OpenCV/libjpeg is linked — do not invent a pose).
- macOS **AVFoundation** (`capture_avf.mm`). Prefer **32BGRA**. `alwaysDiscardsLateVideoFrames`. Lock exposure / AWB when the device allows. No extra packages — system frameworks only.
- `buffer ≈ 1`: dequeue every pending buffer, keep the newest.
- Lock exposure / AWB when the driver allows. If not, the pipeline adapts thresholds every 15 frames.
- Windows **Media Foundation** is a later port of the same `CaptureThread` interface.
- Dummy capture publishes **no** fake aim. Godot desktop fallback (T) supplies UV.
- Unit tests never open a camera. `SABLE_LIVE_CAMERA=1 ./build/sable_cv_tests` probes a real device.
- Godot `.app` needs `NSCameraUsageDescription` in Info.plist before AVF will grant access.

## GDExtension

`cv_input.gdextension` (and `godot/addons/cv_input/`) points at `bin/`. Clone [godot-cpp](https://github.com/godotengine/godot-cpp) **outside this repo**. There is no `4.7` / `godot-4.7-stable` tag; use `master` (v10) with `GODOTCPP_API_VERSION=4.7`.

```bash
# outside the sable tree, once
git clone --depth 1 --branch master https://github.com/godotengine/godot-cpp.git ../godot-cpp

# debug dylib → bin/libcv_input.macos.debug.dylib
cmake -S . -B build \
  -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_OSX_ARCHITECTURES=x86_64 \
  -DSABLE_GODOT_CPP=/abs/path/to/godot-cpp \
  -DGODOTCPP_API_VERSION=4.7 \
  -DGODOTCPP_TARGET=template_debug
cmake --build build --target cv_input

# release (separate build dir; GODOTCPP_TARGET is cache)
cmake -S . -B build-release \
  -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_ARCHITECTURES=x86_64 \
  -DSABLE_GODOT_CPP=/abs/path/to/godot-cpp \
  -DGODOTCPP_API_VERSION=4.7 \
  -DGODOTCPP_TARGET=template_release
cmake --build build-release --target cv_input
```

macOS capture is in `sable_cv` (`capture_avf.mm`, `-fobjc-arc`, AVFoundation/CoreMedia/CoreVideo/Foundation). The shared target links that static lib; it does not recompile the `.mm`. Until the dylib exists, the Range runs in DESKTOP aim.

Optional: dump this editor's API and pass `-DGODOTCPP_CUSTOM_API_FILE=extension_api.json` instead of `GODOTCPP_API_VERSION`.

## Constants

See `include/sable/constants.hpp` and `docs/aim_pipeline.md`. One Euro: mincutoff 1.0 Hz, beta 0.007, dcutoff 1.0 Hz. Coast 100 ms. Seeking below confidence 0.35.
