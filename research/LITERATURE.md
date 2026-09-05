# Literature — techniques we keep, IP we never take

SABLE is original. This note is the homework: what pointing-shooters, aim tools, and stylized games actually taught, and what we refuse to import. No third-party maps, guns, names, audio, or code enter the client.

## 1. Arcade light-gun (Duck Hunt class / Time Crisis class / House of the Dead class)

**Technique:** the bullet is the screen pixel you pointed at. Trigger is a physical click, not a camera frame. Cabinets used CRT timing or IR; LCDs later needed a bright border (Sinden / Gun4IR).

**Keep:** 1:1 shot pixel. HID fire. No aim-assist, no stock-center offset (see `research/mice/REPORT.md`: box center is the stock; the nose is the muzzle).

**Refuse:** cabinet IP, light-gun meshes, border-tracker hardware as a requirement. A MacBook lid camera is the sensor.

## 2. Wii pointing

**Technique:** a sensor bar plus a fast pose filter. Players forgive 50–80 ms of reticle lag if the *shot* is instant. Over-smoothing kills flicks.

**Keep:** One Euro tuned for pointing (`EURO_MINCUTOFF ≥ 2.5`), not 1 Hz soup. Reticle may lag; fire never does (`docs/aim_pipeline.md`).

**Refuse:** Wiimote / sensor-bar copies, Nintendo chrome.

## 3. Kinect / EyeToy / Just Dance cameras

**Technique:** full-body is too coarse for a hitscan FPS. Novelty, not a muzzle.

**Keep:** camera as a *pointing* device, not a dance-mat. One landmark (index tip) is the gun.

**Refuse:** full-skeleton minigames, silhouette toys as the product.

## 4. Leap Motion / Ultraleap / VR hand pinch

**Technique:** 21–32 landmarks at high rate. Pinch-to-shoot adds gesture latency and false fires.

**Keep:** landmark fingertip as muzzle (hand analog of the mouse *nose*). **Fire stays HID** (trackpad / click). MediaPipe Hands is Apache-2.0; it is a library, not a game.

**Refuse:** pinch-as-trigger as the ranked path. Do not wait on a landmark to shoot.

## 5. Webcam “DIY light guns” and YOLO-on-mice

**Technique:** our own corpus (`research/mice/REPORT.md`). YOLO11n COCO class 64 is a *proposal*, 50% recall, confuses phones. KLT on the front taper is the 30 fps path. Neon tape is ranked kit, not v1.

**Keep:** hybrid lock (slow recognizer seeds, fast tracker holds). Extremum toward camera = barrel.

**Pivot (2026-09):** the MacBook product is **hand-as-gun**. Same geometry, different object: index tip = nose. Skin-blob-only is the same failure mode as global Otsu (face / desk eats the lock). Landmarks beat blobs.

## 6. Aim Lab / KovaaK / OSK-class trainers

**Technique:** mouse-on-pad flicks, scenario playlists, endless orbs.

**Keep:** a 60 s Range so the first kill is under 60 s (`research/design-lessons.md`). Score, combo, one volume.

**Refuse:** their maps, target packs, UI chrome, and the verb itself (pad-only). SABLE’s verb is **raise → point → click → drop**.

## 7. Halo’s “30 seconds of fun”

**Technique:** a short combat loop you want again. Not a live-ops treadmill.

**Keep:** pad-strafe → lift (physical ADS) → click → drop-strafe. Broadcast the lift (mode chip, cuff rise, mint stripe). No tutorial wall.

**Refuse:** Halo maps, guns, sandbox, names.

## 8. Stylized shooters (Pistol Whip / SUPERHOT / Rez — look, not content)

**Technique:** a *tiny* palette, readable silhouettes, almost no post. Unshaded or flat. Bloom hides bad aim.

**Keep:** charcoal / bone / mint / rust (CANCHO locker). Flat shading. **No reticle bloom, no world bloom** (`docs/perf_budget.md`, `docs/design.md`). 1080p60 floor.

**Refuse:** their levels, enemies, audio, typography, and any silhouette that reads as those games.

## 9. One Euro Filter (Casiez, Roussel, Vogel, CHI 2012)

**Technique:** speed-based low-pass. Pointing, not cinematic cameras.

**Keep:** first-party implementations only (equations, not a copied tree).

## 10. What the locker already decided (`docs/operators/cancho.md`)

CANCHO is operator 1. Mint stripe on the **lifting glove**. Rust at the wrist. Bone HUD. No face, no likeness, no catalog. **AimSample is the gun** — so the first-person mesh is a **cuff / gauntlet**, not a rifle from another shooter and not a floating mouse.

## Applied in this tree

| Lesson | Where |
|--------|--------|
| Shot = pointed pixel | `AimSample.uv` → camera ray |
| Trigger = HID peek | `fire()` / `AimBus.fire()` |
| Nose not stock | index landmark / fingertip, not palm centroid |
| Fast filter + slow lock | One Euro + optional Gemini seed |
| 30 s loop, first kill < 60 s | Range 60 s |
| Broadcast lift | cuff pose, mint rail, PAD/GUN chip |
| Limited palette, no bloom | Salt House materials |
| Original map | Salt House range, original Bay booth |
| Original operator | CANCHO cuff, not a body scan |

## Paint → model

Concept sheets live in `art/concepts/` (SVG, first-party). Blender rebuild is `art/blender/build_sable_kit.py`. Runtime meshes in `proto/game.js` match those sheets so the browser game does not wait on an editor.
