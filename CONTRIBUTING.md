# Contributing to SABLE

Apache-2.0. Original IP only. Sign off every commit (`Signed-off-by:`) per `CLA.md` (DCO 1.1).

## Do

- One task per branch from `main`. Never push `main`.
- Keep fire as HID peek of `AimSample`. Never wait on a camera frame.
- Run `./tools/ci.sh` (or `pixi run ci`) before you open a PR.
- Keep `license_scan.py` green. No GPL/AGPL/SSPL in client or server.

## Don't

- Third-party game names, maps, guns, audio, or code in runtime art (`proto/` minus vendor, `art/`). Architecture notes in `docs/port.md` / `research/` may name destinations as refuse only.
- Aim-assist, bloom, or RNG covering tracker noise.
- Kernel anti-cheat or vendored Steamworks SDK.

## Dev

```bash
pixi install
pixi run serve      # http://127.0.0.1:8080
pixi run test-aim   # Mojo unit suite
pixi run ci         # full gate
```
