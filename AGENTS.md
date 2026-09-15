# Agent rules — SABLE

- **Open source.** Apache-2.0. Never add GPL/AGPL/SSPL to client or server.
- **Original IP.** Never add, generate, or import third-party game names, assets, maps, audio, or code. Codename only. Do not write a public title.
- **One task per branch.** Branch from `main`. Never push `main`.
- **Aim is the engine.** Hand tracking (`proto/hands.js` `mpTrack` / Worker `detectForVideo` / `fallbackSkin`) first. Prefer that over maps, net, Steam, or anti-cheat.
- **Product fire is shark-fin.** Shark-fin → `AimBus.fire()` peek owns product shoot. Never wait on a camera frame, the Hands worker, the 128 Hz tick, or rAF. HID / trackpad / DESKTOP / Space `forceGun` are **non-product emergency** only. Do not bloom. Do not aim-assist. Do not hide noise with RNG.
- **Tests.** Run `./tools/ci.sh` (Python checks, C++ aim tests, Mojo 1.0 suite via Pixi) before you call a change done. Never skip `license_scan.py`.
- **No kernel AC. No vendored Steamworks SDK.**
- Keep stubs as real files, not empty folders and not `TODO` comments where a no-op function will do.
