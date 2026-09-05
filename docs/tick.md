# Tick

Honest contract (R6). One named rate. Three clocks. HID fire sits outside all of them.

## Named sim rate: **128 Hz**

`server/tick.py` `HZ = 128` is the discrete stepper. Client local Range / Bay step the same `SIM_DT` (`1/128`) from `proto/boot.js`. **64 Hz was leftover docs** — nothing in tree stepped at 64, and there is no Jolt / `physics_interpolation` clock.

Render stays `requestAnimationFrame`. Shared house is **not** this stepper.

## Three clocks

1. **Render (rAF).** Paint, recoil decay, shards, tracers, gun pose, HUD. Variable frame `dt` (capped). Never chooses the shot UV.
2. **Sim (128 Hz).** Dedicated headless peek (`server/tick.py`). Client `stepSim` advances local Range plates and Bay pose at `SIM_DT`. This loop does not shoot.
3. **Shared house (rewind, not a tick).** Lobby sim is closed-form pose at `elapsed_ms` plus fire-tick rewind (`tools/lobby.py` `_pose_at` / `hit`). Clients poll a lazy snapshot. There is no global 128 Hz friend loop — inventing one would lie about how two tabs already share plates.

## HID fire

Fire is an HID event. It peeks the latest `AimSample` on `AimBus` and does not wait for the next 128 Hz step, the next rAF, the Hands worker, or net to choose a UV.

Camera capture is asynchronous. It publishes `AimSample` whenever a frame finishes.

Gameplay motion belongs in the 128 Hz step (or the closed-form rewind). Hitscan resolution belongs in the input event that already carries the sample.

Dedicated server boots headless at the same 128 Hz rate. Browser fire stays HID-local; that process is the sim peek, not a gate on the shot.
