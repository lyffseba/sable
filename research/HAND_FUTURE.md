# SABLE hand future — invent spike (2026-09-09)

Architecture invent for a **pure hand verb** on Chromium. Soft-lock this spike; do not merge from the agent. AimSample locked. AimSample stays five fields. Original IP only. Yard is the sole map. Bay stays parked. Ship floor is **Chromium on MacBook Pro–class** (`docs/port.md`): surface `chromium-macbook`, verb `aimbus-hand-gesture`.

This file is the product-architecture soT for the hand-only future. Tracker archaeology stays in `research/HANDS.md`. Shipped mailbox / HID honesty bars stay in `docs/aim_pipeline.md` and `docs/PRODUCTION.md`. Product brief: `research/PRODUCT.md` (box north star — do not rewrite). Tracking lock: `research/TRACKING.md`. **#86 shark-fin and #87 charger-plug reload are on tip.** Do not regress those verbs. Do not block invent docs. Do not merge from the agent.

---

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

---

## Product path is hands-only

The shipping **product story** is: raise a hand at a MacBook lid camera, **point to aim**, **shark-fin thumb-up to shoot**, **thumb parallel = safe**, **index+middle to the ceiling to reload**. Camera + vision own every gun verb. **No mouse as product verb.** There is **no mouse-gun product verb**. There is **no mouse-body optical aim**. There is **no mouse-lift gun**. There is **no mouse mesh prototype path**. The sable-mouse track is **STOP** (Kruidenhof, not SABLE).

`AimBus.fire()` / `AimPipeline.fire()` remain a **peek** of the last committed `AimSample`. Gesture rising edges call that peek. They do not wait on a camera frame, the Hands worker, net, or the 128 Hz sim. They do not bloom. They do not aim-assist. They do not hide noise with RNG.

HID pad, DESKTOP / cam-deny, and Space `forceGun` may remain in the tree only as a **non-product emergency** — labeled **non-product**. They are honesty bars for a denied camera or a fail-to-lock escape. They are never the product story, never the trailer, never the GUN-mode trigger.

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

Invent around the mailbox. Do **not** add a sixth field for gesture, reload, mag, shark-fin, or SAM confidence. Gesture state lives on `S` (`handLm`, `finHeld` after #86, `reloadHeld`). Pinch is not a trigger. `publishAim` / `peek` / `fire` stay the only AimSample verbs.

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

Order after lift (`updateMode`): **shark-fin** (#86 on tip) → **charger-plug reload** (#87 on tip) → `updateAim`. Gesture never publishes a closed-finger UV before the peek. Reload never calls `fire()`. Mag lives on `S` (#87) — not a sixth AimSample field.

#86 shark-fin is the only product shoot. Pinch is removed — `pinchStrength` is the shark-fin safe gate only. Space is **not** product shoot.

### AimBus peek fire / reload hook

- Shoot: rising-edge shark-fin (`maybeSharkFinFire`) calls the same `fire()` the mailbox already owns. No camera gate. No worker wait.
- Reload: #87 charger-plug (`maybeReloadGesture` / `chargerPlug`) on tip. No second stub. No sixth AimSample field. No hitscan.

---

## Vision stack — Meta invent path; MediaPipe Hands-class ship default (interim)

**Locked invent path:** Meta object-recognition (SAM-class gate + landmark FSM hybrid). Hands + Meta vision must feel as precise as a mouse shooter. MediaPipe Hands-class **is the default ship stack** until that Meta cut is game-ready on the Chromium floor. No mouse ever.

Non-binding vision research below was verified **2026-09-09**. Discarded where wrong (lite `.task`); kept where it matches live docs / author benches / SABLE proto.

### Default *ship* stack — MacBook Chromium (already in proto)

**MediaPipe Tasks Vision Hand Landmarker.** 21 landmarks, **MediaPipe order** (`0` wrist … `4` thumb tip … `8` index … `12` middle … `20` pinky). On-device **WASM + GPU/WebGL** (Tasks `delegate: "GPU"`, then CPU). Detect **off the main thread** in a classic Worker. Already shipped: `proto/hands_worker.js` + vendored `hand_landmarker.task`.

Verified against live Google AI Edge docs on **2026-09-09**:

| Claim | Live docs / garden / proto |
|-------|----------------------------|
| Tasks Vision **Hand Landmarker** | [Hand landmarks detection guide](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker) — 21 landmarks, VIDEO mode, GPU delegate |
| Published `.task` | **HandLandmarker (full)** float16/1 only. Pixel 6 bench: 17.12 ms CPU / **12.27 ms GPU** |
| `hand_landmarker_lite.task` | **404** on the model garden. Legacy Hands `hand_landmark_lite.tflite` is **not** a Tasks bundle. **Lite/full tradeoff is not a Tasks SKU choice** — there is one published full bundle |
| Vendored / pin | **Self-host first:** `proto/vendor/mediapipe/hand_landmarker.task` — **7819105** bytes, float16/1. CDN fallback is pinned `@mediapipe/tasks-vision@0.10.21` + garden `float16/1` (`handsModelTries`). Do not float an unpinned CDN |
| Worker + GPU | Official web samples run `detectForVideo` in a Worker. SABLE already does this |

**Three.js WebGL conflict (keep the Worker):** MediaPipe GPU is WebGL2. Three.js owns the main-thread WebGL context (`proto/house.js` renderer). Putting the GPU delegate on **main** next to that renderer can lose the context (`CONTEXT_LOST_WEBGL` / Emscripten `emscripten_webgl_create_context` failures — community + Google issues). **Prefer Worker + careful delegate:** GPU first inside the Worker (ImageBitmap), CPU if Worker GPU fails. Never `detectForVideo` on rAF beside Three.js. `initHandsMain` (main-thread last resort) must stay last resort.

**Hypothesis correction:** “Hand Landmarker **lite** + GPU + worker” is half-right. GPU + worker is the floor. **Lite `.task` does not exist.** Ship default is the published **full** float16/1 bundle + GPU Worker + One Euro on main + `fallbackSkin` if WASM/landmarks die this frame.

Apache-2.0. First download ~8 MB, cache. Safari may need nosimd WASM — Tasks ships both; we vendor both.

### Stretch — only if MediaPipe is the latency wall

**[micro-handpose](https://github.com/svenflow/micro-handpose)** (`@svenflow/micro-handpose`). Verified **2026-09-09** against the project README (not a SABLE bench):

| Claim | Held? |
|-------|--------|
| WebGPU compute (no WASM / no ONNX Runtime) | yes — 15 compute shaders + landmark model |
| 21 landmarks, **MediaPipe order** | yes — same `wrist` … `pinky_tip` indices our FSM already uses |
| Chrome 113+ / Edge 113+ | yes (Safari 18+ also claimed) |
| ~**2×** MediaPipe desktop | **author bench only** — Mac Mini M4 Pro / Chrome 134: 2.2 ms median vs MediaPipe WebGPU 4.0 ms. **Not** a MacBook Pro lid-cam + SABLE rAF + Three.js bench |
| License | MIT JS; weights derived from MediaPipe Hands (Apache-2.0). Not GPL. Still **do not vendor** until we bench |

**Not the invent default. Not the ship default.** Prototype path **only after** a MacBook Pro + Chromium bench on the Yard (`?sableperf=1` + Worker detect p50/p99 vs MediaPipe full). If MediaPipe is not the latency wall, discard. If it wins, it must stay a Worker, same 21-order FSM, self-hosted weights (no live jsDelivr in the zip), and never enter `fire()`.

Do not grow a second landmark schema. Do not run WebGPU compute on the Three.js device without a Worker experiment.

### Meta vision audit — MacBook Chromium (Juan lock 2026-09-09)

**Product invent target:** in-game hand tracking on **Meta models for object recognition**. Invent the gesture system (aim/point, shark-fin fire, charger reload) **on that stack**. No mouse.

**Honesty first:** Meta SAM-class is **not game-ready** as a Chromium 60 Hz hot path. No Meta-family model publishes a 21-landmark hand FSM that runs 60–120 FPS on MacBook Chromium today. Official SAM 2 “real-time” is **A100 + torch.compile** (hiera_tiny **91.2 FPS**, Hiera-B+ **43.8 FPS** — Meta README / paper). That is not a lid-cam Worker. **Do not pretend Detectron2 or full SAM runs real-time in the browser.**

Verified **2026-09-09** (keep / discard):

| Finding | Held? |
|---------|--------|
| **Runs in Chromium today** — Meta SAM / SAM2 / MobileSAM / SlimSAM via **onnxruntime-web** (WebSAM, [next-sam](https://github.com/karlorz/next-sam), sam-web). Encode once / decode with **point-box prompts** | **yes** — photo / interactive mask UI on Chrome/Edge WebGPU |
| Good for **object recognition / hand-as-object mask** — **NOT** a 21-landmark FSM by itself | **yes** — do **not** claim SAM alone is shark-fin |
| Tiny / MobileSAM ~**45–150 MB**; SAM2 tiny heavier (~151 MB community; official tiny encoder larger on WebSAM) | **yes** |
| Encode latency often **hundreds of ms** — not a free **120 Hz** gesture loop | **yes** — MobileSAM ~345 ms encode, SAM2 tiny ~700 ms (next-sam README). Not 60/120 Hz |
| **Detectron2 does not run real-time in the browser** — stays **Python/native**; only via thin local bridge; **not** the default MacBook Chromium zip | **yes** as a ship claim. A community ONNX→ORT-web export exists and is fragile (WASM masks OK, WebGPU masks broken) — that is **not** Detectron2 real-time and **not** the zip |
| **Meta Quest WebXR hand joints** — headset path, not lid-cam MacBook Chromium floor | **yes** |

Label every line **interim** vs **product invent**.

```
                    ┌─ PRODUCT INVENT (Meta object recognition) ─────────┐
 lid cam            │  SAM-class segmenter = hand / object gate          │
 getUserMedia  ──►  │  sparse encode; prompt last hand ROI / landmark hull│
                    │  mask extremum = muzzle when landmarks foreshorten │
                    └──────────────────────┬────────────────────────────┘
                                           │ same 21-order points
                    ┌─ INTERIM SHIP (until Meta is browser-ready) ───────┐
                    │  MediaPipe Tasks Hand Landmarker (default, in proto)│
                    │  micro-handpose stretch after MacBook Chromium bench│
                    │  gesture FSM: AIM / SHARK-FIN / SAFE / RELOAD      │
                    └──────────────────────┬────────────────────────────┘
                                           ▼
                              AimSample { uv, valid, lifted, confidence, t_hw }
                              fire() peeks — never waits on SAM / detect
```

#### 1. What runs in Chromium today (WASM / WebGPU / ORT-web)

| Family | In Chromium? | Lid-cam 60 Hz? | Honest use |
|--------|--------------|----------------|------------|
| **SAM / SAM2 / MobileSAM / SlimSAM** via onnxruntime-web (WebSAM, next-sam, sam-web) | **yes** on Chromium WebGPU (WASM fallback). Encode once / decode with point-box prompts. Worker. Pre-convert `.ort` | **no** — hundreds of ms encode. **Not** a 21-landmark FSM. **Not** a 120 Hz gesture loop | **Product invent:** hand-as-object **mask** + track. Never shark-fin by itself. Never inside `fire()` |
| **SAM2-tiny / MobileSAM** (named invent cut) | **yes** — MobileSAM ~45 MB / ~345 ms encode; SAM2 tiny ~151 MB / ~700 ms encode (next-sam, macOS Chrome/Edge) | **no** as a free gesture loop | **Product invent target** in a Worker — object recognition stack Juan named |
| **Detectron2** | **not** real-time in the browser. Stays **Python/native**. Not the MacBook Chromium zip | **no** | Thin local bridge **only if** the Chromium ORT SAM path fails the floor. Prefer **pure web**. Do not vendor |
| **DINOv2** INT8 ONNX | theoretically ORT-web; ViT-L INT8 still **~1.5 GB** | **no** | Encoder features. Not a hand. Research-only |
| **Sapiens / Sapiens2** 0.1B INT8 (community ORT-web) | **yes** on Chrome 113+ WebGPU | **no** — published **1–3 s/image WebGPU**, 20–60 s WASM. CLS embedding / whole-body, not 21 hand points | **Research-only.** Too heavy for MacBook floor |
| **Meta WebXR hands** | Quest Browser | n/a on lid cam | Ruled out for this SKU |
| **MediaPipe Hands-class** | **yes** — already in proto | **yes** (interim ship) | **Interim landmark FSM** until Meta is browser-ready |
| **micro-handpose** | **yes** Chrome 113+ WebGPU | author ~2× MediaPipe desktop — **not our bench** | Stretch interim, not invent default |

Apache-2.0 where it matters: SAM 2 / SAM 2.1 code+weights, Detectron2, MediaPipe Hands. Do not add GPL.

#### 2. Thin native / local bridge — prefer pure web

Detectron2 and full native SAM 2 stay **Python/native**. Meta’s official SAM 2 web demo is frontend + **Python backend**. A localhost helper could run hiera_tiny closer to A100-class rates than ORT-web.

**Prefer the Chromium ORT-web SAM2-tiny / MobileSAM path.** Open a thin local bridge **only if** that web path fails the MacBook floor (encode never usable even as a sparse gate). A required helper invents a **second product** and does **not** serve the Chromium zip.

| Question | Answer |
|----------|--------|
| Default zip | **Pure web** — SAM-family ORT-web in a Worker + MediaPipe landmark FSM |
| Detectron2 in the zip | **no** — Python/native only, not default MacBook Chromium |
| Allowed bridge | Optional seed / calib, fire-and-forget — same honesty as `/api/gemini/lock` |
| Forbidden | Ranking, GUN shoot, “must install Detectron2 / the Meta helper to play” |

#### 3. Research-only / too heavy for the MacBook floor

- **Detectron2** (Python/native, not the Chromium zip): not a Chromium gun. Keypoint heads are COCO **person**, not MediaPipe 21-hand.
- **SAM 2 large** (878 MB) / **DINOv2-L**: first-download and VRAM kill the zip + 1080p60 floor.
- **Sapiens2** (seconds per frame): whole-body research.
- **Heavy egocentric** (Ego4D / Hot3D class): datasets, not a vendored web SKU.
- **YOLO mouse-body**: retired for aim. sable-mouse **STOP**.
- Cloud VLM / Gemini every frame: seed only.

#### Invent architecture recommendation (labeled)

1. **Product invent target:** Meta-family **SAM2-tiny / MobileSAM** in a Worker for **hand/object mask + track** (the object-recognition stack Juan named). Encode is sparse (hundreds of ms) — gate / re-encode on lock loss, not every rAF. Point-box prompts from the last landmark hull. Apache-2.0 SAM 2 weights. Do not vendor until a MacBook Chromium encode p50 is honest as a gate.
2. **Landmark FSM (interim):** Gesture FSM (aim / shark-fin / reload) still needs landmarks or mask-derived tips. Keep **MediaPipe Hand Landmarker** (or micro-handpose after bench) as the **landmark FSM** until a Meta landmark model is browser-ready. **Do not claim SAM alone is shark-fin.**
3. **Hybrid (ship the mailbox, invent the gate):** SAM mask gates **“hand present / which blob.”** Landmarks drive **nail UV + shark-fin / charger geometry.** `AimBus` peek unchanged. **AimSample five fields locked.**
4. **Thin local bridge:** only if the Chromium ORT path fails the MacBook floor. **Prefer pure web.** Detectron2 is not the zip.

```
SAM2-tiny / MobileSAM (Worker, ORT-web)     PRODUCT INVENT — object / hand mask
        │  hand present? which blob?
        ▼
MediaPipe 21-order (or micro-handpose)      INTERIM — nail UV + shark-fin + reload
        │  rising edges
        ▼
AimSample { uv, valid, lifted, confidence, t_hw }   LOCKED
fire() peek — never waits on encode
```

Do **not** ship a SAM / Detectron encoder on the rAF or inside `fire()`. Do **not** grow a second mailbox. Do **not** vendor Detectron2 or Sapiens2.

---

## Retire — mouse-gun product verb and mouse mesh prototype path

LiftShot pivot: **no mouse as product verb.** Archaeology only. Do not reopen a mouse mesh / sable-mouse prototype.

| Retired | Why | Where the corpse lives |
|---------|-----|------------------------|
| Mouse-gun **product verb** | SABLE is hand-only reinvent-the-mouse. Cam tracks hands | this file; `research/PRODUCT.md` |
| Mouse-body optical aim (YOLO / NCC / ArUco / nose) | Cam tracks hands. Box center was the stock | `research/mice/REPORT.md` archaeology |
| Mouse-lift gun | Lift is a **hand** | `docs/aim_pipeline.md` DESKTOP bars |
| Mouse HID as **GUN** trigger | Product shoot is shark-fin. Pad is menus only if needed | `productGunHidFire` is false |
| **Mouse mesh prototype path** | Blender ask was **Kruidenhof, not SABLE**. Mouse Blender / `lyffseba/sable-mouse` SABLE art track — **STOP**. Do not generate, import, or prototype a mouse gun / mouse mesh | archaeology only |
| OS cursor as product aim | DESKTOP / HID = **non-product emergency** only | labeled fallback |

Feel DNA may name CS-class honesty and Beat Saber–class shoot energy in **research/** only. Runtime `proto/` + `art/` never take those names, maps, guns, or audio (`tools/foreign_dna.py`).

---

## Prototype path — #86 and #87 are on tip

**#86 shark-fin** (`maybeSharkFinFire`) and **#87 charger-plug reload** (`chargerPlug` / `maybeReloadGesture`) **are on tip**. This spike does **not** rewrite those verbs. Invent around the mailbox with docs + HID honesty + Meta SAM-class hybrid.

### (a) Charger-plug reload — #87 on tip

Index + middle up toward the ceiling is product reload. Keep the lock in PRODUCT / TRACKING / HAND_FUTURE. Do not land a second stub (`chargerReload` / `onReloadStub` / `reloadPulse`).

### (b) Deprecate product HID-as-gun in GUN mode

`productGunHidFire()` returns **false**. `onHidPointerDown` on range / bay / lobby calls `fire()` only when `S.desktop || productGunHidFire()`.

- Product GUN + live camera: pad is **menus only** (chrome still owns WARM UP / ENTER RANGE / LEAVE).
- DESKTOP / cam-deny: HID publish+peek **stays** — labeled **non-product** emergency honesty.
- Calibrate / lock HID for corners is not GUN shoot.
- Pinch is removed. It must not peek `fire()`. `pinchStrength` stays the shark-fin safe gate (>0.48).
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
| micro-handpose | stretch only | After MacBook Chromium bench if MediaPipe is the latency wall. Not the invent default |
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
| **Pinch** | Retired as a fire() caller | Removed. Safe-gate only (`pinchStrength` > 0.48 refuses shark-fin) |
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
- Soft-lock this invent/spike when MERGEABLE. **Do not merge from the agent.**
- #86 shark-fin and #87 charger-plug are on tip. Do not regress those verbs.
- Yard sole map. Bay parked. Apache-2.0. Original IP. No mouse ever.

## Adversarial

- Shark-fin / reload must not publish `updateAim` / `publishAim` before a peek. Pinch must not peek `fire()`.
- Parallel thumb cannot fire. Held shark-fin cannot auto-fire. Held charger cannot auto-reload.
- Reload cannot invent mag. Reload cannot `fire()`.
- Product GUN + `camReady` cannot HID-fire (`productGunHidFire === false`).
- DESKTOP / cam-deny never runs the product gesture FSM as the story — gestures no-op when `S.desktop`.
- Space still only sets `forceGun` + `updateMode` — no `fire()`.
- AimSample still five fields. SAM / Sapiens / YOLO are not the default tracker and must not enter `fire()`.
- No mouse-body optical lock. No mouse mesh. sable-mouse **STOP**.
- MediaPipe lite `.task` must not be invented. Full float16/1 is the ship default until Meta stack ships.
- GPU HandLandmarker must not share the Three.js WebGL context on main — Worker + careful delegate.
- micro-handpose must not land in proto until a MacBook Chromium bench says MediaPipe is the wall. Not the invent default.
- Sapiens2 / heavy egocentric / YOLO mouse-body stay not-defaults / retired for aim.
- Detectron2 / full SAM must not be documented as real-time in Chromium. Official SAM 2 FPS is A100. Detectron2 stays Python/native, not the zip.
- Do not claim SAM alone is shark-fin. Hybrid: mask gates blob; landmarks drive nail + shark-fin.
- Prefer pure web. Thin local bridge only if Chromium ORT fails the MacBook floor.
