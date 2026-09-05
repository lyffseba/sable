# Agent rules — SABLE

- **Open source.** Apache-2.0. Never add GPL/AGPL/SSPL to client or server.
- **Original IP.** Never add, generate, or import third-party game names, assets, maps, audio, or code. Codename only. Do not write a public title.
- **One task per branch.** Branch from `main`. Never push `main`.
- **Aim is the engine.** Hand tracking (`proto/game.js` `mpTrack` / `fallbackSkin`) and HID fire first. Prefer that over maps, net, Steam, or anti-cheat.
- **Fire is HID.** Do not wait on a camera frame to shoot. Do not bloom. Do not aim-assist. Do not hide noise with RNG.
- **Tests.** Run `./tools/ci.sh` (Python checks, C++ aim tests, Mojo 1.0 suite via Pixi) before you call a change done. Never skip `license_scan.py`.
- **No kernel AC. No vendored Steamworks SDK.**
- Keep stubs as real files, not empty folders and not `TODO` comments where a no-op function will do.
