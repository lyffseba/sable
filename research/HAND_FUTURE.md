# SABLE hand future — invent spike (2026-09-09)

Architecture invent for a **pure hand verb** on Chromium. Soft-lock this spike; do not merge from the agent. AimSample stays five fields. Original IP only. Yard is the sole map. Bay stays parked.

This file is the product-architecture soT for the hand-only future. Tracker archaeology stays in `research/HANDS.md`. Shipped mailbox / HID honesty bars stay in `docs/aim_pipeline.md` and `docs/PRODUCTION.md`. Product brief: `research/PRODUCT.md`. Tracking lock: `research/TRACKING.md`.

---

## LOCKS (verbatim — LiftShot PRODUCT+TRACKING ready on box 2026-09-09)

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

---

## Product path is hands-only

The shipping **product story** is: raise a hand at a MacBook lid camera, **point to aim**, **shark-fin thumb-up to shoot**, **thumb parallel = safe**, **index+middle to the ceiling to reload**. Camera + vision own every gun verb. There is **no mouse as an input verb**. There is **no mouse-body optical aim**. There is **no mouse-lift gun**. There is **no mouse mesh** as shipping product art. The sable-mouse track is **STOP**.

`AimBus.fire()` / `AimPipeline.fire()` remain a **peek** of the last committed `AimSample`. Gesture rising edges call that peek. They do not wait on a camera frame, the Hands worker, net, or the 128 Hz sim. They do not bloom. They do not aim-assist. They do not hide noise with RNG.

HID pad, DESKTOP / cam-deny, and Space `forceGun` may remain in the tree as **engineering fallbacks** — labeled **non-product**. They are honesty bars for a denied camera or a fail-to-lock escape. They are never the product story, never the trailer, never the GUN-mode trigger.

---

## Architecture — capture → landmarks → gesture FSM → AimBus

```
lid cam (getUserMedia, user-facing, mirror X)
    │
    ▼
Worker detect  ── queue depth 1, drop stale ──  GPU then CPU
    │
    ▼
landmarks (21) + optional SAM-class hand mask (invent)
    │
    ▼
gesture FSM (same frame, main thread, no sixth AimSample field)
    │     AIM        index extended → nail muzzle → One Euro → publishAim
    │     SHOOT      shark-fin thumb-up rising edge → AimBus.peek / fire()
    │     SAFE       thumb parallel → no fire, hold last UV
    │     RELOAD     index+middle ceiling rising edge → reload hook stub
    │
    ▼
AimSample mailbox { uv, valid, lifted, confidence, t_hw }
    │
    ▼
hitscan peeks last UV  —  reticle may lag 50–80 ms; the shot must not
```

Invent around the mailbox. Do **not** add a sixth field for gesture, reload, mag, shark-fin, or SAM confidence. Gesture state lives on `S` (`handLm`, `finHeld` after #86, `reloadHeld`, `pinchHeld` interim). `publishAim` / `peek` / `fire` stay the only AimSample verbs.

### Capture

- MacBook Pro lid camera. User-facing. Tilt down at hands. No face PIP. Camera is never a selfie.
- Prefer 720p+; AE/AWB off when the driver allows. Chromium `getUserMedia` is the floor.
- `requestVideoFrameCallback` kicks a **classic Worker** (not `type:module` — MediaPipe wasm glue calls `importScripts`).
- Queue depth 1. Drop stale. Main never runs `detectForVideo` on rAF.

### Landmarks → muzzle

- Shot pixel = **index nail** (landmark **8**, extrapolated 6→8). Not palm, not wrist, not box center. Same geometry lesson as the retired mouse-nose study: stock ≠ muzzle.
- Mirror **X**.
- One Euro in camera space, then homography / linear map → `AimSample.uv`.
- Fist (index not extended) is not GUN.

### Gesture FSM

Product verbs, one hand (best pointing hand of up to two):

| State  | Geometry (MediaPipe-class 21) | Rising edge does | Held does |
|--------|-------------------------------|------------------|-----------|
| **AIM** | Index extended; muzzle = 8 along 6→8 | publish UV | keep publishing |
| **SHOOT** | Thumb **up** like a shark fin (`4` above palm scale, not parallel) | `fire()` peek | **safe** — not auto-fire |
| **SAFE** | Thumb **parallel** to the other fingers | nothing | nothing |
| **RELOAD** | Index **and** middle up toward ceiling (`8`+`12` up; ring/pinky folded) | reload hook stub | not a second reload |

Order after lift (`updateMode`): **shark-fin** (#86 — assume it lands) → **reload stub** → pinch (interim only) → `updateAim`. Gesture never publishes a closed-finger UV before the peek. Reload never calls `fire()`. Reload does **not** invent mag capacity, reserve, or ammo — that is a later unlock.

#86 shark-fin is the product shoot. Pinch stays interim until a later soft-lock removes it. Space is **not** product shoot.

### AimBus peek fire / reload hook

- Shoot: rising-edge shark-fin calls the same `fire()` the mailbox already owns. No camera gate. No worker wait.
- Reload: rising-edge charger calls `onReloadStub()` — a hook that pulses `S.reloadPulse` only. No mag. No sixth field. No hitscan.

---

## Vision stack — Meta invent path; MediaPipe Hands-class interim

**Locked invent path:** Meta object-recognition (SAM-class gate + landmark FSM hybrid). Hands + Meta vision must feel as precise as a mouse shooter. MediaPipe Hands-class **may stay interim** until that stack ships on the Chromium floor. No mouse ever.

### Default *shipped* tracker today (interim)

Verified against live Google AI Edge docs on **2026-09-09**:

| Claim | Live docs / garden |
|-------|--------------------|
| Tasks Vision **Hand Landmarker** | [Hand landmarks detection guide](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker) — 21 landmarks, VIDEO mode, GPU delegate |
| Published `.task` | **HandLandmarker (full)** float16/1 only. Pixel 6 bench: 17.12 ms CPU / **12.27 ms GPU** |
| `hand_landmarker_lite.task` | **404** on the model garden (`…/hand_landmarker_lite/float16/1/hand_landmarker_lite.task`). Legacy Hands `hand_landmark_lite.tflite` is **not** a Tasks bundle |
| Vendored file | `proto/vendor/mediapipe/hand_landmarker.task` — **7819105** bytes, float16/1. Keep it. Do not point at a lite 404 |
| Worker + GPU | Official web samples run `detectForVideo` in a Worker with `delegate: "GPU"` then CPU. SABLE already does this (`proto/hands_worker.js`) |

**Hypothesis correction:** “Hand Landmarker **lite** + GPU + worker” is half-right. GPU + worker is the floor. **Lite `.task` does not exist.** Interim default is the published **full** float16/1 bundle + GPU Worker + One Euro on main + `fallbackSkin` if WASM/landmarks die this frame.

Apache-2.0. First download ~8 MB, cache. Safari may need nosimd WASM — Tasks ships both; we vendor both.

### Meta object-recognition invent path (SAM-class gate + landmark FSM)

This is the **product vision invent**, not the v1 hot path.

**Why Meta / SAM-class:** Juan lock — hands + Meta vision models must feel as precise as a mouse shooter. A landmark-only tracker foreshortens when the player points *into* the glass; a mask gate can hold the **hand silhouette** (nail extremum toward the camera) when landmarks jitter. That is the mouse-nose lesson applied to a hand: mask = body, landmark 8 / mask extremum = muzzle.

**Hybrid (invent, not shipped):**

1. **SAM-class gate (sparse):** encode the lid-cam frame; prompt the hand ROI (palm detector box, or last landmark hull). Output: hand mask. Use as a **gate / extremum**, not as a per-frame 60 Hz encoder.
2. **Landmark FSM (dense):** 21 points drive AIM / SHARK-FIN / RELOAD at camera rate. Same FSM table as above.
3. **Muzzle:** landmark 8 when index is extended and the mask agrees; else mask extremum along the 6→8 ray. Still one UV into the five-field mailbox.

**Honesty — not game-ready on Chromium as a 60 Hz hot path (2026-09-09):**

| Stack | Chromium / MacBook? | Game-ready 60–120 FPS lid cam? | License / size | Verdict |
|-------|---------------------|--------------------------------|----------------|---------|
| **SAM 2 / MobileSAM in-browser** (ONNX Runtime WebGPU demos) | yes, experimental | **no** — encode is hundreds of ms to seconds per frame (community: MobileSAM ~345 ms encode; SAM2 tiny ~700 ms; some hybrid splits 5–10 s encode). Decoder 30–60 ms/click is a photo UI, not a gun | SAM 2 is Apache-2.0; **do not vendor until a cut fits the 1–3 ms aim-capture budget** | **Invent path.** Gate / seed only. Never the HID peek. Never a fire wait |
| Meta **Sapiens** (2D/3D whole-body) | research, not a Tasks WASM SKU | **no** | research weights; not a Chromium game bundle | Not default. Not interim |
| Meta **WebXR hands** (Quest joints) | Quest Browser / headset | n/a on MacBook lid cam | — | Ruled out for this SKU |
| YOLO / detector boxes | painful in-browser | box = palm = stock | weights | Ruled out for muzzle (same failure as COCO mouse) |
| Egocentric (Ego4D / Hot3D class) | research | not a vendored web SKU | datasets | Not v1. Not default |
| Cloud VLM / Gemini every frame | yes | **no** (100 ms–2 s) | API | Seed / lock assist only |

Do **not** ship a SAM encoder on the rAF or inside `fire()`. Do **not** grow a second mailbox. When a Meta cut is game-ready (Worker, GPU, ≤ aim-capture budget, Apache-2.0, no mouse), it **replaces** MediaPipe as primary and MediaPipe becomes the else-path the way `fallbackSkin` is today.

Until then: **MediaPipe Hands-class interim.** Invent docs must not pretend SAM is the live tracker.

---

## Retire — mouse as verb, mouse as body, mouse as art

| Retired | Why | Where the corpse lives |
|---------|-----|------------------------|
| Mouse-body optical aim (YOLO / NCC / ArUco / nose) | Cam tracks hands. Box center was the stock. Juan lock | `research/mice/REPORT.md` archaeology |
| Mouse-lift gun | Lift is a **hand**. DESKTOP lift is a fallback lie we keep honest, not a product | `docs/aim_pipeline.md` DESKTOP bars |
| Mouse HID as **GUN** trigger | Product shoot is shark-fin. Pad is menus only | this file; thin proto gate `productGunHidFire` |
| Mouse mesh as shipping product art | Blender ask was Kruidenhof — **STOPPED**. sable-mouse track **STOP** | do not generate or import a mouse gun |
| OS cursor as product aim | DESKTOP is cam-deny / KeyT **non-product** | labeled fallback |

Feel DNA may name CS-class honesty and Beat Saber–class shoot energy in **research/** only. Runtime `proto/` + `art/` never take those names, maps, guns, or audio (`tools/foreign_dna.py`).

---

## Prototype path — smallest next cuts after #86 shark-fin

#86 (shark-fin rising-edge `AimBus` peek) may still be open. **Do not block on the merge.** Assume it lands. This spike invents the next cuts around the mailbox.

### (a) Reload gesture rising-edge stub — no mag

`maybeReloadGesture` / `chargerReload` / `onReloadStub` in `proto/hands.js`.

- Geometry: index + middle extended **up** (image `y` toward the top of a user-facing frame = ceiling), ring + pinky folded.
- Rising edge only. Held charger is not a second reload.
- `onReloadStub` increments `S.reloadPulse`. It does **not** invent mag capacity, reserve, ammo, or a sixth AimSample field.
- `S.desktop` no-ops the gesture (fallback is not the product hand).
- Does not call `fire()`, `publishAim`, or `updateAim`.
- Frame order: `updateMode` → (shark-fin when #86 lands) → **reload stub** → pinch interim → `updateAim`.

### (b) Deprecate product HID-as-gun in GUN mode

`productGunHidFire()` returns **false**. `onHidPointerDown` on range / bay / lobby calls `fire()` only when `S.desktop || productGunHidFire()`.

- Product GUN + live camera: pad is **menus only** (chrome still owns WARM UP / ENTER RANGE / LEAVE).
- DESKTOP / cam-deny: HID publish+peek **stays** — labeled **non-product** emergency honesty.
- Calibrate / lock HID for corners is not GUN shoot.
- Pinch remains interim peek until a later soft-lock removes it.
- Space `forceGun` stays the Q4 fail-to-lock escape — **not** product shoot.

### (c) Chromium / MacBook Pro perf floor

| Bar | Floor | Notes |
|-----|-------|-------|
| Host | MacBook Pro–class + **Chromium** | Web SKU. Safari nosimd is a compatibility else, not the floor |
| Present | 1080p60 floor / 1080p120 stretch | `docs/perf_budget.md` |
| Aim capture | 1–3 ms on the Worker | MediaPipe full GPU ~12 ms Pixel-class; M-series GPU WASM is the bet. Drop stale |
| Aim filter | << 0.2 ms | One Euro on UV, main |
| Reticle | 50–80 ms may lag | Do not bloom to hide it |
| Gesture → peek | **< 8 ms** same as HID→hitscan | `fire()` peeks; shark-fin / reload must not wait on detect |
| SAM-class | **not** in the 8 ms bar | Sparse gate / seed only, after markHid, never inside `fire()` |
| Net | fire-and-forget | Shared house rewind. Bay parked |

Turn AE/AWB off when possible. 720p MJPEG noisy lid cam must still point.

---

## Engineering fallbacks — labeled non-product

Keep the honesty bars. Label them. Do not sell them.

| Fallback | When | Product? |
|----------|------|----------|
| **DESKTOP** / cam-deny (`armPracticeDesktop`, KeyT, Offline lock timeout `goDesktopRange`) | Camera denied or debug | **Non-product.** OS cursor + HID peek. Confidence 1. No mint reticle stacked |
| **Space** `forceGun` | Q4 fail-to-lock (`camReady`, no hand) | **Non-product.** SEEKING until lock or Space. Never auto-desktop. Not a shot |
| **HID pad** in GUN + `camReady` | MacBook reach | **Deprecated as gun.** Menus only. `productGunHidFire` is false |
| **Pinch** | Interim until shark-fin is the only shoot | Interim. Yields the frame when shark-fin is live (#86) |
| **`fallbackSkin`** (findHand + NCC) | WASM/landmarks fail this frame | Tracker else-path. Not a mouse. Not product shoot |
| **skin/NCC as primary** | — | Ruled out (`research/HANDS.md`) |

Q4 never auto-desktop. Camera deny is not fail-to-lock.

---

## AimSample — still locked

```
AimSample { uv, valid, lifted, confidence, t_hw }
```

Five fields. Existing `publish` / `peek` / `fire` only. Gesture bits stay on `S`. Juan must unlock before anyone adds a sixth.

---

## Soft-lock

- Soft-lock / ship only **hand-only** cuts that match this file + `research/PRODUCT.md` + `research/TRACKING.md`.
- Soft-lock this invent/spike when docs + arch land. **Do not merge from the agent.**
- Do not block on #86. Assume shark-fin lands; invent around it.
- Yard sole map. Bay parked. Apache-2.0. Original IP. No mouse ever.

## Adversarial

- Shark-fin / reload / pinch must not publish `updateAim` / `publishAim` before a peek.
- Parallel thumb cannot fire. Held shark-fin cannot auto-fire. Held charger cannot auto-reload.
- Reload cannot invent mag. Reload cannot `fire()`.
- Product GUN + `camReady` cannot HID-fire (`productGunHidFire === false`).
- DESKTOP / cam-deny never runs the product gesture FSM as the story — gestures no-op when `S.desktop`.
- Space still only sets `forceGun` + `updateMode` — no `fire()`.
- AimSample still five fields. SAM / Sapiens / YOLO are not the default tracker and must not enter `fire()`.
- No mouse-body optical lock. No mouse mesh. sable-mouse **STOP**.
- MediaPipe lite `.task` must not be invented. Full float16/1 stays until Meta stack ships.
