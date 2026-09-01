# Agent rules — SABLE

- **Original IP.** Never add, generate, or import third-party game names, assets, maps, audio, or code. Codename only. Do not write the public title.
- **One task per branch.** Branch from `main`. Never push `main`.
- **Aim is the engine.** Prefer finishing `native/cv_input` and `godot/src/input` over maps, guns, net, Steam, or anti-cheat.
- **Fire is HID.** Do not wait on a camera frame to shoot. Do not bloom. Do not aim-assist. Do not hide noise with RNG.
- **Tests.** Run `native/cv_input` tests and `tools/*.py` before you call a change done. Never skip `license_scan.py`.
- **No kernel AC. No vendored Steamworks SDK. No GPL** in client/server.
- Keep stubs as real files, not empty folders and not `TODO` comments where a no-op function will do.
