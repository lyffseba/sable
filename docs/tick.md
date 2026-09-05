# Tick

Honest contract (R6). One named rate. Three clocks. HID fire sits outside all of them.

## Named sim rate: **128 Hz**

`server/tick.py` `HZ = 128` is the discrete stepper. Client local Range / Bay step the same `SIM_DT` (`1/128`) from `proto/boot.js` `stepSim`. **64 Hz was leftover docs** — nothing in tree stepped at 64, and there is no Jolt / `physics_interpolation` clock.

Render stays `requestAnimationFrame`. Shared house is **not** this stepper.

## Soft-lock bars

- **Fixed sim Hz owns plates / hitscan.** `S.simTick` advances only in `stepSim`. Local plates and Bay pose integrate at `SIM_DT`. Hitscan peeks that last committed pose. Render (rAF) is a consumer — paint, recoil, shards, HUD. It does not choose plate time.
- **HID fire outside both.** `fire()` peeks `AimBus` only. It never waits on rAF, the next sim step, the Hands worker, or a camera frame. Range hitscan peeks that UV against the last committed plate pose with the same sphere as lobby rewind (`hitscanRange` / `plateRadius`) — not the spun hex mesh. Look (gun kick / muzzle world) is after `markHid`, not inside the 8 ms bar. match_live SCORE / shatter snap from the room book after the report — the click does not locally credit.
- **`fire_ms` speaks sim Hz, not rAF.** Shared rewind snaps to the 128 Hz grid (`quantize_fire_ms`). Local Bay stamps `Bay.fireMs = committedSimMs()` on the HID peek. Shared Bay uses the same stamp plus a pose mailbox — not a 128 Hz friend loop. The lobby snapshot stays a view. Room hangar is that view (`wait`→`wait_practice`, `range`→`match_live`) — not a tick.
- **Fail loud** if sim steps hitch to frame time (`updateRange(dt)` / rAF `now`) or fire couples to present (`performance.now() - S.rangeStart`).
- **Offline one-click stays.** No warm-up tax. Fire at tick 0 is legal — the first plate is already on the pad.
- **HID→hitscan p99 ≤ 8 ms** still holds (`SablePerf`) with Shared Bay present. Look (gun kick / `getWorldPosition`) and `reportSharedBayFire` / `reportSharedBayPose` / lobby poll stay after `markHid` — never on the click critical path.

## Three clocks

1. **Render (rAF).** Paint, recoil decay, shards, tracers, gun pose, HUD. Variable frame `dt` (capped). Never chooses the shot UV or `fire_ms`.
2. **Sim (128 Hz).** Dedicated headless peek (`server/tick.py`). Client `stepSim` increments `S.simTick` and advances local Range plates and Bay pose at `SIM_DT`. This loop does not shoot.
3. **Shared house / Bay (rewind, not a tick).** Lobby Range is closed-form pose at `elapsed_ms` plus fire-tick rewind (`tools/lobby.py` `_pose_at` / `hit`). Sit plates use the same closed-form as local practice (`sit_pose_y` / `sitPoseY`: bob from life, then drop) — not a per-client phase that would split two friends. Flyers use the same closed-form (`flyer_pose` / `flyerPose`: `y0 + vy0*t - 0.5*g*t^2`) — not a local Euler step that would miss the rewind sphere. Gallery SCORE / combo / hits live on that same rewind (`_gallery_hit` / `_gallery_miss`). `applySharedSim` snaps the book. Shared Bay is a last-committed pose mailbox plus the same `fire_ms` rewind (`start_bay` / `_bay_hit`). `fire_ms` is quantized to `SIM_HZ`. Clients poll a lazy snapshot. Inventing a 128 Hz friend loop would lie about how two tabs already share plates and first-to-5.

## HID fire

Fire is an HID event. It peeks the latest `AimSample` on `AimBus` and does not wait for the next 128 Hz step, the next rAF, the Hands worker, or net to choose a UV.

Camera capture is asynchronous. It publishes `AimSample` whenever a frame finishes.

Gameplay motion belongs in the 128 Hz step (or the closed-form rewind). Hitscan resolution belongs in the input event that already carries the sample, against the last committed sim pose — the same sphere the room rewinds (`hitscanRange`). The hex plate is Look only; mesh-testing it would let a HID peek hit locally and miss the rewind sphere (and the reverse). Bay first-to-5 is the same contract: `tickBay(SIM_DT)` owns pose; `fireBay3D` peeks that pose and stamps `fire_ms`. Shared Bay rewinds that stamp on the room.

Dedicated server boots headless at the same 128 Hz rate. Browser fire stays HID-local; that process is the sim peek, not a gate on the shot.

## Port path

SablePort (`docs/port.md`) may later swap a host *feel*. The named 128 Hz stepper, rAF consumer, and HID-outside-both bars do not move. `proto/port.js` `SABLE_PORT_SIM_HZ` is a label, not a second clock.
