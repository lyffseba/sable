# Aim pipeline — the engine's heart

SABLE is a physical-aim FPS. The unique verb is **raise your hand, point the fingertip at the monitor, click**. A MacBook webcam is enough. Everything else in this repo exists to serve that pose.

This document is the contract. The live tracker is `proto/hands.js`: MediaPipe Tasks Vision HandLandmarker (`mpTrack` kicks `proto/hands_worker.js`, landmark 8) then `fallbackSkin` (`findHand` + NCC) + One Euro on UV before the mailbox. `native/cv_input` holds the filter / AimSample tests. Fire is HID and must not wait on the worker. See `research/HANDS.md`.

## Hardware

- Built-in laptop webcam (lid camera). No mouse in the air. No sleeve. No marker.
- Point the index finger at the screen. Trackpad click or pinch (thumb↔index) fires.
- Target camera: cheap laptop modules. **720p30, MJPEG, auto-exposure, noisy, rolling shutter.** Immaculate aim must still work here.

Turn **auto-exposure and auto-white-balance off** when the driver allows it (V4L2: `V4L2_CID_EXPOSURE_AUTO` manual, `V4L2_CID_AUTO_WHITE_BALANCE` = 0). If the platform ignores the lock, the pipeline **adapts thresholds every N frames** instead of fighting AE.

## AimSample

Shared. No engine types in the native struct.

```
AimSample {
  uv: Vector2      # monitor UV in [0, 1]
  valid: bool
  lifted: bool
  confidence: float
  t_hw: int        # hardware timestamp, microseconds
}
```

An optional ray is later, not required for Range.

## Fire is HID

Click is **always** HID / Raw Input against the **latest** AimSample.

- The reticle may lag **50–80 ms**. The shot must not.
- Never wait for the next camera frame to shoot.
- Never gate fire on `valid` from the current frame. Peek the mailbox.
- A missing frame does not invent a new pose. It leaves the last sample in the bus.

`AimBus.fire()` / `AimPipeline.fire()` are peek, not poll.

SablePort (`docs/port.md`) may later swap a host *feel*. The verb does not move: click still peeks `AimBus`. `proto/port.js` labels that seam `aimbus-hid-peek`. Do not grow a second fire path for a later migrate.

## Pipeline (camera space, then map)

Capture runs on a **worker thread**. Queue depth is effectively **1**: always the newest frame, drop stale. Prefer **YUY2 / raw**; MJPEG is a fallback (decode when OpenCV is linked).

Once a frame is in:

1. **Lock exposure** if possible. Else adapt HSV / luma floors every `kAdaptEveryNFrames` (15).
2. **ROI after lock.** Full-frame search only when `Lost`. Once locked, search **~3× blob radius** around the predicted fingertip (`p + v·dt`). This is what makes 30 fps cheap cameras viable.
3. **Skin + hand.** HSV skin mask, connected components, reject the face blob, fingertip = farthest skin pixel from the palm centroid. Gemini may seed the fingertip once.
4. **Sub-pixel NCC** on a patch around the fingertip, then One Euro. Same `AimSample`.
5. **Hand reacquire** if NCC drops: `findHand` writes the fingertip and coasts.
6. **Outlier reject.** If the new centroid jumps more than `kOutlierJumpPx` (28 px) versus the prediction, ignore that frame (rolling shutter / AE pop). After **2** rejects, relock (full-frame).
7. **One Euro filter** on the centroid **in camera space** (Casiez, Roussel, Vogel 2012), then map through homography (PnP later; same `AimSample` output).
8. **Constant-velocity coast.** If the blob is missing **≤ 100 ms**, extrapolate with last velocity and decay confidence. After 100 ms: `valid = false`, **hold last UV**, chip `SEEKING`. **Do not snap to (0, 0).**
9. **Quality meter.** SNR, mask area, reprojection residual → `confidence` in `[0, 1]`. Range shows it. Below **~0.35**: `SEEKING`. No ranked play later on seeking samples.

Homography fallback (uncalibrated): `u = x / width`, `v = y / height`. Five-point calib writes a real `H`.

## One Euro constants

Tuned for **pointing**, not for smoothing a mouse.

| Parameter   | Symbol   | Value  |
|-------------|----------|--------|
| min cutoff  | fcmin    | 1.0 Hz |
| speed slope | β        | 0.007  |
| derivate fc | dcutoff  | 1.0 Hz |
| fallback fs | freq     | 30 Hz  |

`α = 1 / (1 + τ / Te)`, `τ = 1 / (2π fc)`, `fc = fcmin + β |ẋ̂|`.

Do not bloom the reticle. Do not aim-assist. Do not hide noise with RNG. Filter the pose.

## Lift FSM

Physical ADS. Hand-visible / recent landmark (or recent good `AimSample`) owns GUN.

- Camera: blob in air / **size jump** versus the pad-area baseline (`kLiftAreaScale` = 1.45), or a live / recent fingertip lock in `proto/game.js`.
- Charge hysteresis: **80–150 ms** native (`kLiftHysteresisMs` = 110); proto `LIFT_ON_MS` = 50.
- **Sticky lift:** last good sample keeps `lifted` for `kLiftStickyMs` / `LIFT_STICKY_MS` (550 ms) after the hand leaves the lid cam. UV coast stays **100 ms** — do not invent pose. The reticle may lag; the shot peeks the mailbox.
- Trackpad / HID motion does **not** demote lift during the click (`kLiftHidHoldMs` / `LIFT_HID_HOLD_MS` = 180). HID idle is not required to charge.
- `fire()` peeks `AimBus` (`shot.lifted` or recent sample). It must not reject a shot only because `S.lifted` flickered while the hand reached the pad.
- `fire()` must **not** call `coastTrack` or `updateAim`. Hitscan peeks the last committed mailbox UV (`shot.uv`) against the house sphere (`hitscanRange` / `plateRadius` — same 0.50 / 0.62 as lobby rewind). The spun hex mesh is Look only. The track loop publishes; the click only peeks.

`Space` force-guns the Range without a camera so the verb can be tested. `T` forces desktop aim (OS cursor → UV).

## Latency budget

| Stage                         | Budget        |
|-------------------------------|---------------|
| Sensor + USB (720p30 MJPEG)   | 33–50 ms      |
| Capture thread, drop-old      | 0–8 ms        |
| ROI + moments + One Euro      | 1–3 ms        |
| Homography map                | < 0.1 ms      |
| Reticle present               | **50–80 ms**  |
| HID click → hitscan           | **< 8 ms**    |
| Filter-only lag (pointing)    | 8–20 ms       |

The shot reads `AimBus` on the click. It does not wait for the next 128 Hz sim step, the next rAF, the Hands worker, or net. It does not recompute aim. Range hitscan is the same closed-form sphere the room rewinds — not `Raycaster.intersectObjects` on the plate mesh. Shared `fire_ms` is the last committed sim tick, not rAF present. Local Bay stamps the same grid (`Bay.fireMs = committedSimMs()`). Shared Bay `reportSharedBayFire` runs **after** `SablePerf.markHid` — fire-and-forget, never inside the 8 ms bar. Pose mailbox and lobby poll stay off the click. `?sableperf=1` (or `localStorage.SablePerf=1`) records HID→hitscan samples (`t0` before `bang()`); `SablePerf.stats()` reports p50/p99 against this 8 ms bar. The 8 ms p99 still holds with Shared Bay present.

## Desktop fallback

If `cv_input` is not loaded, or the operator presses **T**, UV is the OS cursor over the viewport. Confidence = 1. The Range stays testable without a webcam.

## Tests

`native/cv_input/tests/test_aim.cpp` (no webcam):

- Synthetic blob path + Gaussian noise + 1-frame dropouts + AE-like brightness pops. **RMS < 7.0 px** after One Euro + coast (settle 20 frames; observed ~5.8 px on g++ 13).
- Two-frame dropout: UV continues, does not jump to the origin.
- HID fire uses the last sample while frames are missing.

`tools/test_hid_fire.py` repeats the fire contract against the proto mailbox. `tools/test_sableperf.py` fails loud if Worker `detectForVideo` sneaks back onto main rAF, if `SablePerf` `t0` is not before `bang()`, if fire waits on the worker, or if Shared Bay `reportSharedBayFire` / pose / lobby poll land inside the HID→hitscan probe. `tools/test_shared_bay.py` repeats the room-owned booth lock.
