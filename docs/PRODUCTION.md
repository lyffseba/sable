# SABLE — production bible

Codename only. Apache-2.0. Original IP. This is the document a producer, engineer, and art lead can share.

## One sentence

You raise a hand at a laptop or TV, the house throws plates, the click is the shot — and friends can stand in the same house.

## Player fantasy (locked)

The feeling is **arcade light-gun on a living-room TV**, not an aim-trainer, not a military FPS.

- Duck Hunt class: things fly, you point at the glass, they pop or they escape.
- Cabinet-with-friends class: same room, same screen energy; later the same house over a room code.
- The gun is **your hand**. The trigger is **HID** (trackpad, mouse click, later a pedal). The reticle may lag; the shot never waits on a camera frame.

We take the *feeling*. We never take ducks, malls, zombies, cabinets, names, maps, or guns from those games.

## Pillars (do not violate)

1. **Pointing is the gun.** Index tip / AimSample.uv is the muzzle. Not box-center, not palm, not OS cursor (except DESKTOP debug).
2. **Click is HID.** `AimBus.fire()` peeks. No camera gate, no bloom, no aim-assist, no RNG on the lifted shot.
3. **Broadcast the lift.** Cuff rises, mint rail, PAD/GUN chip. First kill under 60 s. No tutorial wall.
4. **One house.** Offline and online share the Salt House. Online is a lobby layer, not a second map.
5. **Original silhouette.** Charcoal / bone / mint / rust. CANCHO cuff, not a rifle. Bone plates, not orbs from a trainer.

## Modes (v1)

| Mode | What it is | Ship bar |
|------|------------|----------|
| **Salt House / Gallery** | 60 s scored gallery. Sit plates, crossing clays, rising flushes. Escape = miss. End state: GALLERY CLEAR. | Playable now — a mode, not leftover Range |
| **Waiting arena** | Room code, 10 slots, WARM UP anytime, host ENTER RANGE | Rooms work; ENTER RANGE shares plates |
| **Bay 1v1** | Original booth, cover vs open middle, first to 5 | Playlist from lobby / boot — local first-to-5 |

v1 is **not** an on-rails walk through a mall. If we ever add a “house walk,” it is a later mode with original rooms, not a clone.

## Loop (30 seconds of fun)

Raise cuff → plate appears (PULL) → point at glass → click → shatter or escape → drop-strafe / rest hand → next plate.

## Input contract

```
webcam  →  fingertip lock (landmarks preferred, skin+NCC fallback)
         →  One Euro in camera space
         →  homography → AimSample.uv
HID click → peek AimSample → hitscan
```

Desktop **T** is a debug gun, not the product. Space is force-lift for development.

## Art contract

Paint sheets (`art/concepts/*.svg`) are the look. Runtime meshes in `proto/house.js` must match. Blender (`art/blender/build_sable_kit.py`) rebuilds the same kit for stills/GLB. No Marketplace packs, no scans, no third-party guns.

Runtime Look is unshaded/baked CANCHO (charcoal / bone / mint / rust). `MeshBasic` / `bayUnshaded`, no ACES, no mint emissive bloom. Bay and Salt House share this bible. Aim noise stays readable.

Gallery polish bar: Fortnite-class CANCHO silhouettes — charcoal barrel ribs with rust edge, mint centerline, solid rust backstop; yard bunkers few and low so bone plates stay readable.

CANCHO tell: mint rail on the index, rust cuff, bone palm. No face.

## Tech that is already right

- WebGL client, zero install, 1080p60 floor / 1080p120 stretch.
- Fire-is-HID mailbox.
- One Euro pointing constants.
- Apache-2.0, license scan, DCO.
- In-memory lobby rooms.
- Mojo 1.0 kernels for later SIMD (NCC, moments, hitscan) — not on the HID path.

## What is proto (honest)

`proto/game.js` is the module entry (`import "./boot.js"`). Ownership is split: `aim.js` (mailbox / fire peek / sticky lift / SablePerf / desktop), `hands.js` (MediaPipe + skin/NCC + One Euro; `detectForVideo` in `hands_worker.js`), `house.js` (Salt House / Yard plates / shared match hooks / Bay), `boot.js` (lobby UI / phase machine / rAF glue).

Tick contract (`docs/tick.md`): render is rAF (consumer only); named sim is **128 Hz** (`server/tick.py` + client `stepSim` / `S.simTick`) and owns plates / hitscan pose; HID fire peeks `AimBus` and waits on neither. `fire_ms` rewind speaks that grid (`quantize_fire_ms`). Shared house stays a lazy lobby snapshot + fire-tick rewind — not a global 128 Hz friend loop.

Hand tracking: MediaPipe Tasks Vision HandLandmarker (Apache-2.0, published float16/1 `.task`, landmark 8) is the primary muzzle. Detect runs in a Web Worker (GPU, then CPU). Main applies One Euro, then the mailbox. skin/NCC is the else path when landmarks die. Fire never waits on the worker.

Online: rooms are real. After host **ENTER RANGE**, the lobby room owns the plate seed and hit resolve. Two tabs see the same spawn / escape / shatter. The owning client sends the last committed `AimBus` sample (UV + `t_hw` + lift bit). The server rewinds to that fire tick and ray-tests that UV — it does not re-aim, does not read cam confidence, and a miss stays a miss.

**Product gate (locked):** Offline **GALLERY** (`play("range")`) and waiting-room **WARM UP** stay **local and one-click** — no warm-up tax. Salt House / gallery is never the only gun: Bay, WARM UP, and ENTER RANGE stay. Runtime geometry is original SABLE (Yard / Salt House / Bay). CS map literacy is architecture notes only — zero Valve / Epic asset DNA. Shared house is not the only way to shoot. Lift/HID must not wait on net, the Hands worker, the 128 Hz sim step, or rAF — if the lobby POST hangs or `detectForVideo` is in flight, local practice still fires. Look must not bloom over the reticle. Lock-never-cursor: the OS pointer writes `AimSample` only in **DESKTOP** (`T`). Main rAF must not run `HandLandmarker.detect` synchronously. `?sableperf=1` / `window.SablePerf` still proves HID→hitscan p99 < 8 ms (`t0` before `bang()`). `tools/test_sableperf.py`, `tools/test_sableqa_offline.py`, `tools/test_tick_contract.py`, and `tools/test_gallery_mode.py` fail loud if detect sneaks back onto main, the probe is reordered, Offline / WARM UP die, lock shows the OS cursor, fire waits on the worker or the tick, sim steps hitch to frame time, fire_ms couples to present, docs drift off 128 Hz, Look traps lift/HID, gallery loses score/clock/end, or Bay becomes the only gun. **`v0.19.0` stood.** Build tags after this soft-lock. Playlist: `docs/modes.md`.

Lift: hand-visible / recent landmark (or recent good `AimSample`) owns GUN. Trackpad HID does **not** demote lift during the click. `fire()` peeks `AimBus` and honors sticky lift so a MacBook pad reach can still shoot. UV coast stays 100 ms (no invented pose). The click does **not** call `coastTrack` / `updateAim` — hitscan uses the last committed `S.aim` / mailbox sample. Optional `?sableperf=1` records HID→hitscan p50/p99 vs the 8 ms bar (`window.SablePerf.stats()`).

## Proposed refactors (do not start all at once)

| # | Refactor | Why | Cost | When |
|---|----------|-----|------|------|
| R1 | Split `proto/game.js` into `aim.js`, `hands.js`, `house.js`, `boot.js` | Production ownership, test seams | ownership files + contract tests read the concat | **Done** (same verb; merge when CI green) |
| R2 | MediaPipe Hands as primary muzzle (landmark 8), skin/NCC fallback | Blob≠fingertip; face confusion | 1 day + vendor wasm | **Done** |
| R3 | Hand-visible **beats** trackpad HID for lift; sticky through pad reach | Trackpad click dropped GUN when the hand left frame | Half day + test rewrite | **Done** |
| R4 | Shared Range sim on the lobby room (plate seed + hits) | “Friends” is fake until this | seed + rewind ray resolve; not a global tick | **Done** (merge when CI green; zip after tip) |
| R5 | Blender GLB as optional load, procedural fallback | Art soT without breaking CI | 1 day | When a modeler is in Blender |
| R6 | Unify tick: render rAF, sim 128 Hz, HID outside both | Docs vs code | contract + local `stepSim` | **Done** |

Recommend **merge to main when CI green**. **`v0.19.0` stood.** Build tags after this soft-lock. Gallery is a playlist/label cut only — same fire verb, AimSample untouched, R6 128 Hz / `fire_ms` honesty stays. Shared house stays a lazy lobby snapshot + fire-tick rewind (not a fake global 128 Hz friend sim). Next after this: R5 when a modeler is in Blender, or competitive 1v1 on the R6 contract.

## Milestones

- **M0 (now):** Salt House visible, cuff, plates, HID fire, rooms, original IP.
- **M1:** Arcade gallery loop (plates/clays escape). Waiting-room WARM UP. Fire peeks only (no aim recompute on click). Sticky lift shipped. **Done.**
- **M2:** Landmarks + lift verb that allows trackpad fire. **Done** (Hands + R3).
- **M3:** Two clients, same plates, same house. **Done** for the room (seed + fire-tick ray). Offline / WARM UP stay local. Zip held until tip + SableQA offline-shoot gate.
- **M4:** Bay as a second playlist from the lobby, still one art bible. **Done** (boot **BAY** + lobby **ENTER BAY**; original booth; first to 5). Offline / WARM UP stay local one-click. Zip held until tip + SableQA (Bay must not be the only gun). **`v0.12.0` stands.**
- **M5:** Salt House is a playable **gallery mode** (60 s score / round clock / GALLERY CLEAR). Offline one-click stays. Bay / WARM UP / ENTER RANGE stay. **Done.** **`v0.19.0` stood.** Build tags after this soft-lock.

## Non-goals (v1)

Ranked, anti-cheat, Steam, on-rails campaign, voice, user-generated maps, marketplace cosmetics that change tracking.

## Open questions — blocking

See the end of this file. Do not invent answers in code until they are decided.

---

### Q1. SKU
Is v1 **laptop lid camera + trackpad** only, or must a living-room TV + USB webcam + a clicker work on day one?

### Q2. Friends
Is “with friends” **same couch / same screen** (pass the click, or two hands on one cam), **two laptops / room code**, or both?

### Q3. House fantasy — decided
Salt House v1 is a **clay gallery**: things fly at you, you stand still. Score the 60 s clock. WASD is Bay only. A house walk is a later mode, original rooms, not a clone.

### Q4. Fail to lock
If the camera never sees a hand: **desktop T forever**, **skip to gallery with a warning**, or **hard stop**?

### Q5. Art soT
Are runtime procedural meshes enough until Blender stills exist, or must GLB from Blender load in the client before a public tag?

### Q6. Violence analog
Plates only (sporting clays), or original creatures that are **not** zombies/ducks? This changes art, VO, and stores.

### Q7. Trigger hardware
Trackpad only, or also **space / USB foot pedal / second mouse** as first-class HID?
