# Hand tracking — strategies, counterexamples, verdict

**Only question:** how does a MacBook lid camera, in the browser, put the **index fingertip** into `AimSample.uv` at 60–120 FPS without extra hardware?

Fire stays HID. This file is the tracker. Ruled out only with a counterexample.

## Geometry (do not invert)

User-facing camera. Player **points at the glass**. Shot pixel = **index tip**, not palm, not wrist, not box center. Same lesson as the mouse-nose study (`research/mice/REPORT.md`): stock ≠ muzzle.

Mirror **X**. Unmirrored front camera maps “point left” to the right of the frame.

## Candidates

| ID | Strategy | In-browser? | Fingertip? | 60 FPS MacBook? | Extra kit? |
|----|----------|-------------|------------|-----------------|------------|
| A | Skin blob + farthest-from-centroid | yes | no (any extremity) | yes | no |
| B | HSV + connected components + face reject | yes | no | yes | no |
| C | NCC patch on a lock template | yes | only if lock was the tip | yes | no |
| D | Gemini / cloud VLM every frame | yes | maybe | **no** (100ms–2s) | API key |
| E | YOLO / detector + KLT | painful | box, not tip | maybe | weights |
| F | **MediaPipe Hands (Tasks Vision)** | **yes** | **landmark 8** | **yes (GPU WASM)** | no |
| G | TFJS `handpose` | yes | landmarks | slower than F | no |
| H | Apple Vision native helper | **no** | yes | n/a | install |
| I | Leap / Ultraleap / depth | yes if device | yes | yes | **hardware** |
| J | Marker / glove / tape | yes | yes | yes | **kit** |
| K | WebGPU custom CNN | someday | if we train | unknown | dataset |

## Adversarial audits (only counterexamples kill)

**A / B — skin blob (what we shipped as findHand)**  
Counterexample 1: face is skin; largest blob is the head.  
Counterexample 2: farthest point from palm centroid is often **thumb or wrist**, not index.  
Counterexample 3: dark room / backlit window; mask empties.  
→ **Ruled out as primary.** Keep as fallback if WASM fails.

**C — NCC**  
Counterexample: template on the wrong lock (face, sleeve) tracks the stock forever.  
→ **Fallback only**, after a real fingertip seed.

**D — Gemini hot path**  
Counterexample: one round-trip > one frame. Breaks “performance of a real game.”  
→ **Seed / lock assist only.** Already true.

**E — YOLO in the browser**  
Counterexample: box center is the palm (stock). Same failure as COCO mouse.  
→ Ruled out for muzzle.

**G — TFJS handpose**  
Counterexample: same landmark idea as F, worse FPS and maintenance.  
→ Ruled out vs F.

**H — native Apple**  
Counterexample: not the web SKU. Anyone-with-a-MacBook-in-Chrome fails.  
→ Ruled out for v1.

**I / J — extra hardware**  
Counterexample: “anyone with this MacBook” fails.  
→ Ruled out for v1. Ranked kit later.

**K — train our own**  
Counterexample: no consented in-house corpus; months.  
→ Not v1.

**F — MediaPipe Hands**  
Apache-2.0. 21 landmarks. GPU delegate on M-series. Landmark **8** = index tip, **4** = thumb (pinch later), **0** = wrist.  
Remaining objections (not fatal):  
- ~8–17 MB first download → cache.  
- Pointing *into* the camera foreshortens fingers → still returns 8; One Euro.  
- Safari may need nosimd WASM → Tasks ships both.  
No counterexample kills F for this SKU.

## Verdict

| Stage | Tracker | Proof it survived |
|-------|---------|-------------------|
| **Do it** | MediaPipe Tasks Vision HandLandmarker, landmark 8, mirror X, One Euro | Only in-browser fingertip at camera rate |
| **Do it right** | `detectForVideo` runs in `proto/hands_worker.js` (GPU, then CPU). Queue depth 1; drop stale. Main applies One Euro on UV then the mailbox. If WASM/landmarks fail **this frame**, `fallbackSkin` (findHand + NCC) still writes the muzzle. HID fire never waits on cam/worker. `initHands` promise must resolve before play. Pinch after `updateMode`. | Worker + fallback + mailbox |
| **Do it better** | Pinch (8↔4) as optional fire; 2nd hand ignore; 120 FPS | After lock is green on a lid cam |

**Model (confirmed):** Tasks Vision publishes one HandLandmarker `.task` — Google **float16/1 full** (`hand_landmarker.task`, 7819105 bytes). There is no `hand_landmarker_lite.task` on the model garden (404). Legacy Hands `hand_landmark_lite.tflite` is not a Tasks bundle. Keep the vendored float16/1 file. Sapiens / YOLO / egocentric are not defaults.

Do not converge on blobs because they were easy. Blob lost the audit.

## Landmark map (Hands)

`0` wrist · `4` thumb tip · `8` index tip · `12` middle · `16` ring · `20` pinky.

Muzzle = **8**. Pinch later = distance(`4`,`8`).
