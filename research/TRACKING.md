# SABLE tracking — product lock

## North star (LOCKED)
**Gesture-only control. Mouse-shooter precision. No mouse control.**
Hands + Meta vision models must feel as precise as a mouse shooter — CS honesty, Beat Saber energy, zero mouse as input verb.

## Core invent (LOCKED)
**Hand-only. No mouse as product verb. Mouse-shooter precision.**
Reinvent the mouse as a **hand system**: the camera + best vision models own aim, shoot, reload, and lift/pose. No mouse-body optical lock. No mouse-lift gun. No mouse mesh as a shipping product art step (that Blender ask was Kruidenhof flat — out of SABLE scope).

Vision-model stack: **Meta object-recognition vision models** for in-game hand tracking (Juan lock). Invent/spike path open — win latency + honesty on MacBook lid-cam Chromium. MediaPipe Hands-class may stay interim until Meta stack ships. No mouse ever.

## Soft rules (from PRODUCT.md)
- Soft-lock / ship only cuts that match **hand-only** + this brief
- AimSample off-limits unless Juan unlocks
- Always-practice / lobby never soft-locks warm-up
- HID / trackpad / Space forceGun may remain **engineering fallbacks**, never the product story

## STOPPED
- Mouse Blender / `lyffseba/sable-mouse` SABLE art track — STOP
- Mouse-as-gun / mouse-cam aim — retired

See `research/HAND_FUTURE.md` for capture → landmarks → gesture FSM → AimBus (Meta SAM-class hybrid honesty). Product brief: `research/PRODUCT.md`. #86 shark-fin and #87 charger-plug are on tip — do not block invent docs. AimSample locked.

## Juan LOCK (2026-09-09)
**Front camera tracks HANDS, not the mouse.**
- **Aim** = hand pointing (literally point to aim)
- **Shoot / reload** = hand gestures — not mouse-body tracking, not HID-as-gun
- **No mouse as product verb.** Webcam must **not** optically lock the mouse body for aim. No mouse-lift gun. No mouse-gun product verb. **No mouse mesh prototype path** (sable-mouse STOP — Kruidenhof, not SABLE)

### Shoot gesture
- Thumb **up** like a shark fin = **shoot**
- Thumb **parallel** to the other fingers = **not** shooting (safe)

### Reload gesture
- Index + middle fingers pointing **up toward the ceiling** = **reload**
- Analogy: the usual “plug in charger / insert mag” gesture (fingers up into the port/magwell)

## Verb
- Hands up / point at screen → GUN; cam + vision own the hand; point aims; shark-fin thumb fires; index+middle up reloads
- Pad (on mat) → menus / movement only — **not** product shoot
- HID / DESKTOP / Space = **non-product emergency** only if still in code — never the product story (cam-deny honesty, KeyT debug, Q4 `forceGun` escape)
- Camera never becomes a selfie (no face PIP)

## Contract
- AimSample stays off-limits unless Juan unlocks
- Soft-lock / ship only hand-only cuts
- HID click must not be the lie that replaces the shoot gesture in gun mode
- Product path is hands-only (`research/HAND_FUTURE.md`)
- `productGunHidFire()` is false — pad tap on the product GUN path must not peek `fire()`; DESKTOP / cam-deny still does
- `forceGun` re-arms pad as Q4 emergency only; Space is not a shot; `productGunHidFire` stays false.

## History (superseded for aim target)
Earlier research (mice YOLO / NCC optical-patch / ArUco sleeve / bare-mouse nose) targeted the mouse body. That path is **retired for aim**. Mouse-as-gun / mouse-cam aim are **retired**. No mouse mesh as a shipping product art step (Kruidenhof flat — out of SABLE scope). Mouse Blender / `lyffseba/sable-mouse` SABLE art track — STOP. Keep docs for archaeology only; invent/spike path open (Meta SAM-class object gate + landmark FSM). MediaPipe Hands-class is **interim** until that stack ships.

## Hardware floor
Ship floor is **Chromium on MacBook Pro–class** lid-cam (`docs/port.md`). Surface `chromium-macbook`. Verb `aimbus-hand-gesture`. Godot/native is not the tracking host.

2021 G14 — clip cam top-center if needed, AE off, 720p+. Camera tilted down at hands.

Lid camera. Player **points the index at the glass**. Shot pixel = **index nail**, not palm, not wrist, not box center.

See `research/HANDS.md` for the MediaPipe interim audit (Tasks Vision HandLandmarker **full** float16/1 — no lite `.task` — GPU Worker; skin/NCC else). Mouse-body YOLO / NCC / ArUco is **retired for aim** — archaeology in `research/mice/REPORT.md`.

## Muzzle

- Landmark **8**, extrapolated along 6→8 (nail).
- Mirror **X** (user-facing camera).
- One Euro in camera space, then homography / linear map → `AimSample.uv`.
- Fist (index not extended) is not GUN.

## Pipeline

Product gun path (locks above): point aims; **shark-fin shoot** (`maybeSharkFinFire`) and **index+middle-up reload** (`maybeReloadGesture` charger-plug) **are on tip** (#86 / #87). Product GUN HID-as-gun is deprecated (`productGunHidFire` is false — pad menus only). DESKTOP cam-deny, HID pad, and Q4 Space `forceGun` remain **shipped engineering fallbacks, labeled non-product** — do not drop those honesty bars (`docs/PRODUCTION.md`, `docs/aim_pipeline.md`). They are never the product story. HID click must not replace the shoot gesture in gun mode. Do not invent reload on those fallbacks.

1. **Ship default (interim vs Meta invent):** MediaPipe Tasks Vision Hand Landmarker — 21 landmarks, MediaPipe order, WASM+GPU/WebGL in a Worker (do not share the Three.js WebGL context on main). Published full float16/1 `.task` only; self-host pinned, CDN pinned fallback. See `research/HAND_FUTURE.md`.
2. **Product invent:** Meta-family **SAM2-tiny / MobileSAM** in a Worker (ORT-web — WebSAM / next-sam / sam-web) for **hand-as-object mask + track**. Encode once / point-box decode. Hundreds of ms — not a 120 Hz loop. **SAM alone is not shark-fin.** Detectron2 stays Python/native, not the Chromium zip. Prefer pure web; thin local bridge only if ORT fails the MacBook floor. Never inside `fire()`.
2b. **Interim landmark FSM:** MediaPipe Hands-class (above) or micro-handpose after bench — nail UV + shark-fin / reload geometry until a Meta landmark model is browser-ready. Hybrid: SAM mask gates hand/blob; landmarks drive the FSM; AimSample five fields locked.
3. **Else the same frame:** `fallbackSkin` (`findHand` + NCC). If Hands never loads, this is the path.
4. **Product shoot** peeks `AimBus` on shark-fin rising edge (`maybeSharkFinFire`, #86). **Reload** is index+middle ceiling (`chargerPlug` / `maybeReloadGesture` after shark-fin, before `updateAim`, #87) — rising-edge refill, mutually exclusive with shark-fin. Mag tell = reload honesty (`drawModeChip` MAG n / DRY after CONF when `!S.desktop`). SAFE tell = thumb-parallel honesty (`drawModeChip` SAFE after CONF with MAG when pointing + thumbParallel). Additive — do not rename `S.mode`. DESKTOP / forceGun do not invent a pad mag story. Empty shark-fin stays missTick. Pinch is **not a trigger** — `pinchStrength` is the shark-fin safe gate only. Shot never waits on a camera frame. Neither gesture must publish UV first or re-gate off the waiting Yard. Do not force shark-fin or reload when `S.desktop`. Space `forceGun` is the Q4 fail-to-lock escape, not product shoot.
5. Gemini may **seed** a lock. Not the hot path.

`AimSample { uv, valid, lifted, confidence, t_hw }`
