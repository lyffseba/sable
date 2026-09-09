# SABLE tracking — product lock

## Juan LOCK (2026-09-09)
**Front camera tracks HANDS, not the mouse.**
- **Aim** = hand pointing (literally point to aim)
- **Shoot / reload** = hand gestures — not mouse-body tracking, not HID-as-gun
- Mouse may remain a pad HID for menus/movement when on the mat; webcam must **not** optically lock the mouse body for aim

### Shoot gesture
- Thumb **up** like a shark fin = **shoot**
- Thumb **parallel** to the other fingers = **not** shooting (safe)

### Reload gesture
- Index + middle fingers pointing **up toward the ceiling** = **reload**
- Analogy: the usual “plug in charger / insert mag” gesture (fingers up into the port/magwell)

## Verb
- Pad (on mat) → DESKTOP / OS cursor / menus / movement (HID ok)
- Hands up / point at screen → GUN; cam tracks hands; point aims; shark-fin thumb fires; index+middle up reloads
- Camera never becomes a selfie (no face PIP)

## Contract
- AimSample stays off-limits unless Juan unlocks
- Soft-lock / ship only cuts that match hand tracking
- HID click must not be the lie that replaces the shoot gesture in gun mode

## History (superseded for aim target)
Earlier research (mice YOLO / NCC optical-patch / ArUco sleeve / bare-mouse nose) targeted the mouse body. That path is **retired for aim**. Keep docs for archaeology; ship hand tracking (MediaPipe Hands-class or better) with gesture shoot/reload.

## Hardware floor
2021 G14 — clip cam top-center if needed, AE off, 720p+. Camera tilted down at hands.

Lid camera. Player **points the index at the glass**. Shot pixel = **index nail**, not palm, not wrist, not box center.

See `research/HANDS.md` for the audit (MediaPipe primary, skin/NCC else). Product brief: `research/PRODUCT.md`. Mouse-body YOLO / NCC / ArUco is **retired for aim** — archaeology in `research/mice/REPORT.md`.

## Muzzle

- Landmark **8**, extrapolated along 6→8 (nail).
- Mirror **X** (user-facing camera).
- One Euro in camera space, then homography / linear map → `AimSample.uv`.
- Fist (index not extended) is not GUN.

## Pipeline

Product gun path (lock above): shark-fin shoot; index+middle-up reload. Not implemented in this docs cut. DESKTOP cam-deny, HID pad, and Q4 Space `forceGun` remain shipped honesty fallbacks — do not drop those bars (`docs/PRODUCTION.md`, `docs/aim_pipeline.md`). HID click must not replace the shoot gesture in gun mode.

1. **MediaPipe Hands** (GPU WASM, `requestVideoFrameCallback`) — best pointing hand of up to two.
2. **Else the same frame:** `fallbackSkin` (`findHand` + NCC). If Hands never loads, this is the path.
3. **HID fire** peeks `AimBus`. Pinch (thumb↔index, hand-scaled, after lift, before `updateAim`) or trackpad. Shot never waits on a camera frame. Pinch must not publish the closed-finger UV first, and must not re-gate off the waiting Yard.
4. Gemini may **seed** a lock. Not the hot path.

`AimSample { uv, valid, lifted, confidence, t_hw }`
