# Legal

SABLE is **original IP**, released as **open source under Apache License 2.0**.

## Red line

Do **not** add, generate, or import names, assets, maps, audio, code, UI chrome, or silhouettes from other games. Fan licenses are **not** a commercial license. Do not ship third-party game content under a "fair use" story.

Do not write an eventual public title into this repo. Codename only: **SABLE**.

## Licensing posture

- First-party code, design, and original content: Apache-2.0. See `LICENSE` and `CLA.md`.
- Three.js (vendored): MIT. Credit in `docs/THIRD_PARTY_NOTICES.md`.
- MediaPipe Tasks Vision (vendored `@mediapipe/tasks-vision@0.10.21` + Hand Landmarker float16/1): Apache-2.0. Credit in `docs/THIRD_PARTY_NOTICES.md`.
- Mojo compiler / std (when used via Pixi): Apache-2.0 with LLVM exceptions.
- OpenCV, when linked: Apache 2.0.
- **No GPL / AGPL / SSPL** in client or server binaries we ship.

## Anti-cheat / Steam

No kernel anti-cheat in this scaffold. Steamworks SDK is not vendored.
