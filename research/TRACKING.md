# SABLE tracking — hand is the gun

Lid camera. Player **points the index at the glass**. Shot pixel = **index nail**, not palm, not wrist, not box center.

See `research/HANDS.md` for the audit (MediaPipe primary, skin/NCC else).

## Muzzle

- Landmark **8**, extrapolated along 6→8 (nail).
- Mirror **X** (user-facing camera).
- One Euro in camera space, then homography / linear map → `AimSample.uv`.
- Fist (index not extended) is not GUN.

## Pipeline

1. **MediaPipe Hands** (GPU WASM, `requestVideoFrameCallback`) — best pointing hand of up to two.
2. **Else the same frame:** `fallbackSkin` (`findHand` + NCC). If Hands never loads, this is the path.
3. **HID fire** peeks `AimBus`. Pinch (thumb↔index, hand-scaled, after lift) or trackpad. Shot never waits on a camera frame.
4. Gemini may **seed** a lock. Not the hot path.

`AimSample { uv, valid, lifted, confidence, t_hw }`
