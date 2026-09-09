# SABLE tracking — hand is the gun

**Juan / LiftShot lock — 2026-09-09.** Front camera tracks **hands**, not the mouse.

- **AIM** = hand tracking, literally. Point with the hands. The mouse body is never the optical aim target.
- **SHOOT + RELOAD** = hand gestures. The cam owns **pose and gestures**.
- **SHOOT** (named): gun-hand **thumb UP like a shark fin** = SHOOT. Thumb **PARALLEL** along the other fingers = NOT shooting.
- Aim stays hand pointing (index nail / landmark 8).
- **Reload** is still a gesture — **TBD**. Do not invent a reload pose.
- `AimSample` stays five fields: `{ uv, valid, lifted, confidence, t_hw }`.
- Mouse remains **HID** (pad / menus / DESKTOP fallback) — not optical aim, not the product shoot path.

**Product shoot path** = shark-fin gesture. **HID click** = pad / DESKTOP fallback. Q4 Space `forceGun`, DESKTOP cam-deny, HID peek, and sticky lift already ship — do not pretend camera hand lock or shark-fin is the only gun.

Hand path: lid cam tracks the hand. Mouse body is never the optical aim target. HID click never waits on cam. **DESKTOP** is the cam-deny / OS-cursor fallback already locked in `docs/aim_pipeline.md` and `docs/PRODUCTION.md`.

Lid camera. Player **points the index at the glass**. Shot pixel = **index nail**, not palm, not wrist, not box center.

See `research/HANDS.md` for the audit (MediaPipe primary, skin/NCC else). Mouse-body YOLO / NCC / ArUco is **retired for aim** — archaeology in `research/mice/REPORT.md`.

## Muzzle

- Landmark **8**, extrapolated along 6→8 (nail).
- Mirror **X** (user-facing camera).
- One Euro in camera space, then homography / linear map → `AimSample.uv`.
- Fist (index not extended) is not GUN.

## Pipeline

1. **MediaPipe Hands** (GPU WASM, `requestVideoFrameCallback`) — best pointing hand of up to two.
2. **Else the same frame:** `fallbackSkin` (`findHand` + NCC). If Hands never loads, this is the path.
3. **HID fire** peeks `AimBus`. Product shoot path is shark-fin (above). Shipped peek: pinch (thumb↔index, hand-scaled, after lift, before `updateAim`) or trackpad — HID click is the pad / DESKTOP fallback. Shot never waits on a camera frame. Pinch must not publish the closed-finger UV first, and must not re-gate off the waiting Yard.
4. Gemini may **seed** a lock. Not the hot path.

`AimSample { uv, valid, lifted, confidence, t_hw }`

## Retired for aim (archaeology)

Mouse-body optical lock (YOLO11n COCO class 64, NCC on the mouse, ArUco / marker-on-mouse, Gemini mouse-nose) is **not** the live aim target. Keep the study in `research/mice/` for stock≠muzzle geometry. Do not revive it as the webcam gun.
