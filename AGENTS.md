# Agent rules — SABLE

- **Original IP.** Never add, generate, or import third-party game names, assets, maps, or audio. Codename only. Do not write the public title.
- The only allowed third-party *tracker* is Hydrargyrum Games’ webcam luma plugin (`unity/Assets/Plugins/HgWebcamObjectTracking`, MPL-2.0). Credit them. Do not paste YOLO/MediaPipe/TensorMouse.
- **One task per branch.** Branch from `main`. Never push `main`.
- **Engine is Unity 2022.3 LTS** (`unity/`). Chrome `proto/` is the no-editor fallback. Godot is gone.
- **Aim is the engine.** Webcam pose → `AimSample`. Fire is HID against the mailbox.
- **Fire is HID.** Do not wait on a camera frame to shoot. Do not bloom. Do not aim-assist. Do not hide noise with RNG.
- **Tests.** Run `tools/*.py` and `native/cv_input` tests before you call a change done. Never skip `license_scan.py`.
- **No kernel AC. No vendored Steamworks SDK. No GPL** in client/server.
- Keep stubs as real files, not empty folders and not `TODO` comments where a no-op function will do.
