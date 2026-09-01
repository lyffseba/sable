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

`cv_input.gdextension` (and `godot/addons/cv_input/`) points at `bin/`. Build the shared library after cloning [godot-cpp](https://github.com/godotengine/godot-cpp) for 4.7:

```bash
cmake -S . -B build -DCMAKE_CXX_COMPILER=g++ -DSABLE_GODOT_CPP=/path/to/godot-cpp
```

Until that `.so` exists, the Range runs in DESKTOP aim.

## Constants

See `include/sable/constants.hpp` and `docs/aim_pipeline.md`. One Euro: mincutoff 1.0 Hz, beta 0.007, dcutoff 1.0 Hz. Coast 100 ms. Seeking below confidence 0.35.
