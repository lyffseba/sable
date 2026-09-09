# SABLE tracking — product lock

## LOCKS (verbatim — LiftShot PRODUCT+TRACKING ready on box)

NORTH STAR (LOCKED):
Gesture-only control. Mouse-shooter precision. No mouse control.
Hands + Meta vision models must feel as precise as a mouse shooter — CS honesty, Beat Saber energy, zero mouse as input verb.

CORE INVENT:
Hand-only. No mouse as product verb. Mouse-shooter precision.
Reinvent the mouse as a hand system: camera + best vision models own aim/shoot/reload/lift. No mouse-body optical lock. No mouse-lift gun. No mouse mesh as shipping product art (Blender ask was Kruidenhof — STOPPED for SABLE / sable-mouse track STOP).
Vision stack: Meta object-recognition invent path (SAM-class gate + landmark FSM hybrid as already briefed). MediaPipe Hands-class may stay interim until Meta stack ships. No mouse ever.

HAND VERBS unchanged: aim=point; shark-fin thumb up=shoot; thumb parallel=safe; index+middle ceiling=reload.
Soft rules: soft-lock/ship only hand-only cuts; AimSample locked; HID/DESKTOP/Space = engineering fallbacks never product story.
Platform: MacBook Pro + Chromium web floor.

## LiftShot product pivot (priority)

**SABLE = hand-only reinvent-the-mouse — NO mouse as product verb.** Cam tracks hands. Shark-fin / reload **stand**. **Mouse mesh / sable-mouse STOPPED** (Blender ask was **Kruidenhof, not SABLE**). No mouse-gun product verb. **No mouse mesh prototype path.** Vision-model stack **open to invent** (Meta SAM-class object gate + landmark FSM as already briefed). DESKTOP / HID = **non-product emergency** only if still in code. AimSample locked.

See `research/HAND_FUTURE.md` for capture → landmarks → gesture FSM → AimBus. Product brief: `research/PRODUCT.md`.

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

## History (superseded for aim target)
Earlier research (mice YOLO / NCC optical-patch / ArUco sleeve / bare-mouse nose) targeted the mouse body. That path is **retired for aim**. Mouse-as-gun / mouse-cam aim are **retired**. Mouse-gun product verb and **mouse mesh prototype path** are **STOPPED** (Mouse Blender / `lyffseba/sable-mouse` — Kruidenhof, not SABLE). Keep docs for archaeology only; vision stack stays **open to invent** (Meta SAM-class object gate + landmark FSM). MediaPipe Hands-class is **interim** until that stack ships.

## Hardware floor
Ship floor is **Chromium on MacBook Pro–class** lid-cam (`docs/port.md`). Godot/native is not the tracking host.

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
4. **Product shoot** peeks `AimBus` on shark-fin rising edge (`maybeSharkFinFire`, #86). **Reload** is index+middle ceiling (`chargerPlug` / `maybeReloadGesture` after pinch, before `updateAim`, #87) — rising-edge refill, mutually exclusive with shark-fin. Pinch is **interim**. Shot never waits on a camera frame. Neither gesture must publish UV first or re-gate off the waiting Yard. Do not force shark-fin or reload when `S.desktop`. Space `forceGun` is the Q4 fail-to-lock escape, not product shoot.
5. Gemini may **seed** a lock. Not the hot path.

`AimSample { uv, valid, lifted, confidence, t_hw }`
