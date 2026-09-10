# SABLE — production bible

Codename only. Apache-2.0. Original IP. This is the document a producer, engineer, and art lead can share.

## One sentence

You raise a hand at a laptop or TV, the house throws plates, the click is the shot — and friends can stand in the same house.

## Player fantasy (locked)

The feeling is **arcade light-gun on a living-room TV**, not an aim-trainer, not a military FPS.

- Duck Hunt class: things fly, you point at the glass, they pop or they escape.
- Cabinet-with-friends class: same room, same screen energy; later the same house over a room code.
- The gun is **your hand**. Product shoot is the shark-fin thumb (see `research/HAND_FUTURE.md`). HID / DESKTOP / Space are a **non-product emergency** only if still in code — never the product story. The reticle may lag; the shot never waits on a camera frame.

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
| **Waiting arena** | HUD-on-Yard always-practice. Room code, WARM UP anytime, host ENTER RANGE | Live Yard under thin chips; ENTER RANGE shares the gallery |
| **Bay 1v1** | Original booth, cover vs open middle, first to 5 | **Parked** — not player-facing; Yard is the sole active map |

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

Product lock: front cam tracks hands — mouse body is never the optical aim target. **No mouse as product verb.** No mouse-gun product verb. **No mouse mesh prototype path** (sable-mouse STOP — Kruidenhof, not SABLE). Product gun path = shark-fin shoot + index+middle-up reload; HID click must not replace the shoot gesture in gun mode. `productGunHidFire()` is false — pad tap on the product GUN path must not peek `fire()`; DESKTOP / cam-deny still does. `forceGun` re-arms pad as Q4 emergency only; Space is not a shot; `productGunHidFire` stays false. DESKTOP cam-deny / HID pad / Q4 Space `forceGun` remain shipped **non-product emergency** honesty bars only if still in code (`research/TRACKING.md`, `research/HAND_FUTURE.md`). Juan / LiftShot product brief: `research/PRODUCT.md`. Vision invent: Meta SAM-class gate + landmark FSM; MediaPipe Hands-class is interim.

Desktop **T** is a debug gun, not the product. Space is the Q4 force-GUN escape on fail-to-lock. **Q4 fail-to-lock is SEEKING until lock or Space.**

## Art contract

Paint sheets (`art/concepts/*.svg`) are the look. Runtime meshes in `proto/house.js` must match. Blender (`art/blender/build_sable_kit.py`) rebuilds the same kit for stills/GLB. No Marketplace packs, no scans, no third-party guns.

Runtime Look is unshaded/baked CANCHO (charcoal / bone / mint / rust). `MeshBasic` / `bayUnshaded`, no ACES, no mint emissive bloom. Bay and Salt House share this bible. Aim noise stays readable.

Gallery polish bar: readable CANCHO silhouettes (Fortnite-class = silhouette literacy only — charcoal / bone / mint / rust). Charcoal barrel ribs with rust edge, mint centerline, solid rust backstop; yard bunkers charcoal / rust, few and low, so bone plates stay readable. No ACES. No mint emissive bloom over the reticle. Never Fortnite / UEFN / Valve DNA in `proto/` or `art/` — `tools/test_sableport.py` fails loud.

CANCHO tell: mint rail on the index, rust cuff, bone palm. No face.

## Tech that is already right

- WebGL client, zero install, 1080p60 floor / 1080p120 stretch.
- Ship floor: **Chromium on MacBook Pro–class** lid-cam (`SABLE_PORT_SURFACE` = `chromium-macbook`). Godot/native is an engineering path only — no second product. Invent / SAM stays in-browser or a thin local bridge.
- Fire-is-HID mailbox.
- One Euro pointing constants.
- Apache-2.0, license scan, DCO.
- In-memory lobby rooms.
- Mojo 1.0 kernels for later SIMD (NCC, moments, hitscan) — not on the HID path.

## What is proto (honest)

`proto/game.js` is the module entry (`import "./port.js"` then `import "./boot.js"`). Ownership is split: `aim.js` (mailbox / fire peek / sticky lift / SablePerf / desktop), `hands.js` (MediaPipe + skin/NCC + One Euro; `detectForVideo` in `hands_worker.js`), `house.js` (Salt House / Yard plates / shared match hooks / Bay), `boot.js` (lobby UI / phase machine / rAF glue), `audio.js` (SableAudio), `port.js` (SablePort host seams — identity only).

Tick contract (`docs/tick.md`): render is rAF (consumer only); named sim is **128 Hz** (`server/tick.py` + client `stepSim` / `S.simTick`) and owns plates / hitscan pose; HID fire peeks `AimBus` and waits on neither. `fire_ms` rewind speaks that grid (`quantize_fire_ms`). Shared house stays a lazy lobby snapshot + fire-tick rewind — not a global 128 Hz friend loop.

Hand tracking: MediaPipe Tasks Vision HandLandmarker (Apache-2.0, published float16/1 `.task`, landmark 8) is the primary muzzle. Detect runs in a Web Worker (GPU, then CPU). Main applies One Euro, then the mailbox. skin/NCC is the else path when landmarks die. Fire never waits on the worker.

Online: rooms are real. After host **ENTER RANGE**, the lobby room owns the plate seed, hit resolve, gallery SCORE (combo × worth), shots / ACCURACY, combo_max / COMBO, and the 60 s bell. The seed owns kind / peek / velocity / `born_ms` (`_next_spawn_ms`) — a late first poll must not stamp birth. Sit / flyer pose is the same closed-form as local practice (`sit_pose_y` / `sitPoseY` from life — bob then drop; `flyer_pose` / `flyerPose` — `y0 + vy0*t - 0.5*g*t^2`). Hitscan is the same sphere (`hitscanRange` / `_hitscan`, clay/rise 0.50, sit 0.62). Two tabs see the same spawn / escape / shatter / sit Y / flyer Y / hit volume / score book / ACCURACY / COMBO peak / GALLERY CLEAR. ESC is a room miss for combo (`_note_escapes` / `_gallery_escape`) — Offline still drops locally. ESC is not a shot. ESC does not rewrite `combo_max`. `applySharedSim` snaps sit, flyers, and SCORE, then tells ESC, then closes on `over`. A `fire_tick` at or past `RANGE_MS` does not credit and is not a shot. Do not bob from a per-client phase. Do not Euler-integrate flyers. Do not mesh-test the spun hex. Do not keep a local SCORE the rewind missed. Do not leave combo live after a shared escape. Do not locally zero combo before the room book. Do not locally end match_live from `simMs()`. Do not paint match_live ROUND remaining from local `simMs()` — snap `S.elapsedMs` from room `elapsed_ms`. Do not invent match_live ACCURACY from local `S.shots++` — snap `S.shots` from room `shots`. Do not invent match_live COMBO from a local `if (S.combo > S.comboMax)` — snap `S.comboMax` from room `combo_max`. Do not invent match_live plate life from a local `o.life += dt` after a poll — life is `(committedSimMs() - born_ms)`, the same clock `_pose_at` rewinds. Shared Bay (parked — not offered from lobby chrome) still room-owns first-to-5 score, last-committed pose, and `fire_ms` rewind against the foe capsule if the booth is invoked. The owning client sends the last committed `AimBus` sample (UV + `t_hw` + lift bit) and, in Bay, the last committed booth pose. The server rewinds to that fire tick and ray-tests that UV — it does not re-aim, does not read cam confidence, and a miss stays a miss. Shared Bay is the same lazy snapshot + fire-tick rewind as the house — not a global 128 Hz friend loop.

**Product gate (locked):** Offline **GALLERY** (`play("range")`) and waiting-room **WARM UP** stay **local and one-click** — no warm-up tax. Waiting arena is HUD-on-Yard always-practice (`startWaitingYard`) — live local plates, no 60 s lock, no net on the click. A fresh ONLINE arms the camera fire-and-forget (`armPracticeCam`) so lift / shark-fin / HID can live — no lock/calib tax. Do not leave the waiting Yard on a dead gun. Camera deny arms desktop on that live lobby (`armPracticeDesktop`) — do not dump into `goDesktopRange` / the 60s gallery. **Q4 fail-to-lock is SEEKING until lock or Space** (`forceGun`) when `camReady` and no hand — never OS cursor, never auto-desktop / `goDesktopRange` / `armPracticeDesktop` / `S.desktop=true` because lock timed out while `camReady`. Thin SableHUD SEEKING chip so the state is not silent — charcoal / bone / mint / rust, same 22px bar, do not thicken the lobby or hide the cuff. Camera deny is not fail-to-lock. Offline lock timeout → `goDesktopRange` stays Offline. KeyT stays debug — not the Q4 product path. KeyT must not disarm DESKTOP on cam-deny waiting Yard (`lobby` / `wait_practice`) — re-arm via `armPracticeDesktop`. When `camReady`, KeyT debug toggle-off stays. WARM UP from that live Yard phase-preserves (`lobbyWarmup`: skip `play()` lock when already lifted / on `lobby` / `range`) — `resetLockState` would disarm the gun. `alreadyLifted` treats DESKTOP as live without `camReady`; phase-preserve still skips `play()` lock. Host **ENTER RANGE** is SableNet phase-preserve (`enterRangePreserve`): share the live Yard, skip calib/lock when already lifted, lobby POST is fire-and-forget. Durable hangar session is `S.hangar` (`hangar` | `wait_practice` | `match_live`) so waiting-practice and shared gallery are not overloaded on `lobby` / `range` alone — **SableNet hangar lock:** the room owns that session class (`wait`→`wait_practice`, `range`→`match_live`; Bay stays parked); practice never promotes (only ENTER RANGE writes `match_live`); poll / snapshot is a view; Offline / WARM UP stay client-local parks (no wire gate). Server room `phase` stays `wait` | `range` | `bay`. HUD still reads `S.hangar`. Apply is sync — fire never waits on the hangar field. Fail loud if fire gates on hangar or Offline / WARM UP talk to the room for hangar. The Yard is the sole active map. Bay is parked (not player-facing). WARM UP and ENTER RANGE stay. Runtime geometry is original SABLE (Yard / Salt House / parked Bay). CS map literacy is architecture notes only — zero Valve / Epic asset DNA. Shared house is not the only way to shoot. Lift/HID must not wait on net, the Hands worker, the 128 Hz sim step, or rAF — if the lobby POST hangs or `detectForVideo` is in flight, local practice still fires. Look must not bloom over the reticle. Gallery arcade feedback is a thin **SableHUD** bar (`SCORE` / `ROUND` + time / end chip) plus hangar chips `WAIT` / `READY` / `LIVE` from `S.hangar` and a thin `ROOM` chip from `S.room` on `wait_practice` / `match_live` — charcoal / bone / mint / rust, no tutorial wall, no paint over the cuff. Overlay `ROOM` stays; the HUD chip is additive so friends see the code without thicker chrome. Gallery audio is sparse **SableAudio**: dry-tick miss + hit punch after shot resolve, plus a quiet mint-tell lift cue (`Mint. Lift.` — oscillator chirp this cut, under miss/hit gains) after the cuff goes GUN — no bed, no ambience, never louder than those chips. Mint-tell is the short audio cue only: do not paint VO over the cuff / hide the gun. Waiting-Yard `lobby` is live for mint-tell (`afterLiftState`) — same hysteresis as range; always-practice must not omit the tell until WARM UP / ENTER RANGE. `armPracticeDesktop` invokes `afterLiftState` after writing DESKTOP truth. `enterGame` invokes `afterLiftState` after `setPhase`. `Space` forceGun invokes `updateMode` before `afterLiftState`. `drawModeChip` does not prefer SEEKING when `S.forceGun` or `S.mode === "GUN"`. Do not thicken the lobby. Lock-never-cursor: the OS pointer writes `AimSample` only in **DESKTOP** (`T`). `syncCursor` shows the OS cursor when `S.desktop` — lock-never-cursor hides it otherwise. `draw2D` skips `drawCrosshair` when `S.desktop` — the mint reticle is the hand/GUN tell. `publishAim` writes confidence 1 when `S.desktop` — leftover tracker quality must not lie about a live DESKTOP gun. Main rAF must not run `HandLandmarker.detect` synchronously. `?sableperf=1` / `window.SablePerf` still proves HID→hitscan p99 < 8 ms (`t0` before `bang()`) with Shared Bay present — Look (gun kick / muzzle world, including parked Bay) and `reportSharedBayFire` / `reportSharedBayPose` / lobby poll stay fire-and-forget after `markHid`, never on the click. `fireBay3D` is the sphere only. `tools/test_sableperf.py`, `tools/test_sableqa_offline.py`, `tools/test_tick_contract.py`, `tools/test_gallery_mode.py`, `tools/test_sablehud.py`, `tools/test_sableaudio.py`, `tools/test_bay_r6.py`, `tools/test_shared_bay.py`, `tools/test_sablelobby.py`, `tools/test_hangar_wire.py`, `tools/test_shared_range.py`, `tools/test_sablelook.py`, and `tools/test_sableyard.py` fail loud if detect sneaks back onto main, the probe is reordered, Shared Bay taxes the HID→hitscan bar, Offline / WARM UP die, lock shows the OS cursor, fire waits on the worker or the tick, sim steps hitch to frame time, fire_ms couples to present, docs drift off 128 Hz, Look traps lift/HID, HUD hides the gun, mint-tell VO hides the gun, waiting-Yard lobby lift skips mint-tell, cam-deny DESKTOP omits `afterLiftState`, Offline DESKTOP / `enterGame` omits `afterLiftState`, Space forceGun skips `updateMode` before `afterLiftState`, `drawModeChip` prefers SEEKING over forceGun / GUN, SableHUD leaves the thin chip bar, the lobby thickens, gallery loses score/clock/end, Bay first-to-5 leaves the 128 Hz / HID-outside / `fire_ms` stamp, Bay HUD grows a tutorial wall, parked `lobbyStartBay` awaits net, shared Bay invents a friend tick, local Bay fire talks to `/api/lobby/*`, or Bay reappears on boot / lobby chrome, or the waiting arena becomes a match-start screen again, or ENTER RANGE promote forces calib/lock / awaits the lobby POST, or `S.hangar` collapses wait-practice / match-live back onto `lobby` / `range` alone, or a shared room omits hangar / two clients split WAIT/LIVE, or hangar chips thicken the lobby / hide the gun, or a ROOM chip hides the gun / thickens the lobby, or Look blooms ACES / mint emissive over the reticle, or Yard bunkers take bone fill and hide plates, or two clients split sit Y / flyer Y / SCORE / ESC combo / `applySharedSim` skips sit / the client bobs from an unsynced phase / the client Euler-integrates flyers / local fire mesh-tests the spun hex / `hitscanRange` leaves the house sphere / Look (gun kick / `getWorldPosition`) lands inside the HID→hitscan probe / match_live `fire()` locally credits SCORE before the room book / a shared escape leaves combo live / `applySharedSim` zeros combo before the snap / a late first poll stamps `born_ms` / two rooms with the same seed split spawn time / a `fire_tick` at or past `RANGE_MS` still credits / two clients split GALLERY CLEAR / `applySharedSim` skips `over` / match_live `updateRange` locally closes from `simMs()` / two clients split ROUND remaining / `applySharedSim` skips `elapsed_ms` / match_live HUD paints ROUND from local `simMs()` / two clients split ACCURACY / `applySharedSim` skips `shots` / match_live `fire()` locally increments `S.shots` before the room book / two clients split COMBO peak / `applySharedSim` skips `combo_max` / `applySharedSim` invents `S.comboMax` from a local combo snap / match_live `fire()` locally writes `S.comboMax` before the room book / match_live `updateRange` advances `o.life += dt` instead of `committedSimMs() - born_ms` / `spawnSharedPlate` drops `born_ms` / two clients split the rewind sphere / shark-fin publishes `updateAim` before `maybeSharkFinFire` / `maybeSharkFinFire` re-gates `phase === "range" || "bay"` and mutes the waiting Yard / pinch peeks `fire()` / `maybePinchFire` still calls `fire()` / DESKTOP is forced onto shark-fin / Space forceGun becomes product shoot / a waiting Yard never arms the camera / forces lock / awaits getUserMedia on fire / HID pointerdown lives on `canvasHUD` while `#hud` is `pointer-events: none` / WARM UP from the waiting Yard routes through `play()` lock / leftover JOIN/CODE eats waiting-Yard HID after join. / waiting-Yard camera deny leaves a dead gun / KeyT disarms DESKTOP on cam-deny waiting Yard / camera deny dumps lobby through `goDesktopRange` / waiting-Yard fail-to-lock invents OS cursor while camReady / Q4 SEEKING chip dies / Space forceGun leaves the fail-to-lock escape / a DESKTOP first pad peeks screen-center / `onHidPointerDown` skips publishAim when DESKTOP owns the mailbox / cam / GUN / pinch peek `fire()` on the click / a DESKTOP mailbox lies seeking+unlifted after cam deny / `updateMode` skips DESKTOP when `!camReady` / `syncCursor` hides the OS cursor while DESKTOP owns the mailbox / `draw2D` stacks the mint reticle on DESKTOP / `publishAim` writes leftover tracker quality as DESKTOP confidence. `tools/test_hand_future.py` fails loud if the LiftShot north star leaves `research/HAND_FUTURE.md` / `research/PRODUCT.md` / `research/TRACKING.md`, if AimSample grows a sixth field, or if SAM/Sapiens/YOLO become the shipped default. `tools/test_hid_fire.py` fails loud if the pad is rebound to the muted HUD canvas or a DESKTOP first pad peeks `{0.5,0.5}`. **SablePort** (`docs/port.md`, `proto/port.js`) is the later-migrate seam — feeling / architecture only, runtime host stays SABLE. Ship floor is Chromium on MacBook Pro–class (`SABLE_PORT_SURFACE` / `chromium-macbook`); Godot/native is an engineering path only — no second product. Verb label is `aimbus-hand-gesture` (hand point + shark-fin → AimBus peek; charger-plug reload; DESKTOP HID honesty fallback). `tools/test_sableport.py` fails loud if Valve / Epic DNA lands in runtime art, the Chromium/MacBook floor dies, the host id leaves `sable`, or the verb / tick / Look / mode bars drift. **`v0.20.0` stood.** Build tags after this gallery HUD tip. Playlist: `docs/modes.md`.

Lift: hand-visible / recent landmark (or recent good `AimSample`) owns GUN. Trackpad HID does **not** demote lift during the click. HID pointerdown lives on `window` (`onHidPointerDown`) — `#hud { pointer-events: none }` must not mute the pad. Chrome (`button` / `input`) still owns WARM UP / ENTER RANGE / LEAVE. After JOIN, leftover CODE/JOIN under the hidden cursor is not chrome (`muteJoinPad`). `onHidPointerDown` publishes click UV when DESKTOP owns the mailbox — first pad after cam deny / T / `goDesktopRange` must not peek `{0.5,0.5}`. Cam / GUN / shark-fin must not publish on the click. `updateMode` writes DESKTOP truth (`seeking` false, `lifted` true) even if `!camReady`. `fire()` peeks `AimBus` and honors sticky lift so a MacBook pad reach can still shoot. UV coast stays 100 ms (no invented pose). The click does **not** call `coastTrack` / `updateAim` — hitscan peeks the last committed mailbox UV (`shot.uv`) against the house sphere (`hitscanRange`). **Shark-fin is product shoot** on the hand / GUN path: thumb UP like a shark fin is a rising-edge peek; thumb parallel to the other fingers is safe. `updateMode` then `maybeSharkFinFire` then `maybeReloadGesture` then `updateAim` — the gesture must not rewrite the shot. `maybeSharkFinFire` must not re-gate phase; waiting-yard `lobby` uses `fire()`. Do not force shark-fin when `S.desktop` — DESKTOP / cam-deny keep HID publish+peek. Pinch is not a trigger — `pinchStrength` is the shark-fin safe gate only. **Reload is product charger-plug** on the hand / GUN path: index+middle pointing up at the ceiling is a rising-edge refill (`maybeReloadGesture`); empty mag dry-clicks via `missTick` and cannot silent-fire on shark-fin. Thin MAG chip after CONF in `drawModeChip` on the hand/GUN path (`MAG n` bone/mint; rust `DRY` at 0) — mag tell = reload honesty. DESKTOP / forceGun do not invent a pad mag story. Empty shark-fin stays `missTick`. Reload must not fire, must not rewrite shot UV, must not re-gate phase. Do not force reload when `S.desktop`. Shark-fin and charger-plug are mutually exclusive. Space `forceGun` stays the Q4 fail-to-lock escape — not product shoot. The hex plate is Look only. Gun kick and muzzle world run after `markHid` — a missing cuff must not throw on the click. Optional `?sableperf=1` records HID→hitscan p50/p99 vs the 8 ms bar (`window.SablePerf.stats()`).

## Proposed refactors (do not start all at once)

| # | Refactor | Why | Cost | When |
|---|----------|-----|------|------|
| R1 | Split `proto/game.js` into `aim.js`, `hands.js`, `house.js`, `boot.js` | Production ownership, test seams | ownership files + contract tests read the concat | **Done** (same verb; merge when CI green) |
| R2 | MediaPipe Hands as primary muzzle (landmark 8), skin/NCC fallback | Blob≠fingertip; face confusion | 1 day + vendor wasm | **Done** |
| R3 | Hand-visible **beats** trackpad HID for lift; sticky through pad reach | Trackpad click dropped GUN when the hand left frame | Half day + test rewrite | **Done** |
| R4 | Shared Range sim on the lobby room (plate seed + hits) | “Friends” is fake until this | seed + rewind ray resolve; not a global tick | **Done** (merge when CI green; zip after tip) |
| R5 | Blender GLB as optional load, procedural fallback | Art soT without breaking CI | 1 day | When a modeler is in Blender |
| R6 | Unify tick: render rAF, sim 128 Hz, HID outside both | Docs vs code | contract + local `stepSim` | **Done** |
| R7 | SablePort path skeleton (docs + host seams) | Honest later migrate, zero foreign IP now | `docs/port.md` + `proto/port.js` + DNA test | **Done** |

Recommend **merge to main when CI green**. **`v0.20.0` stood.** Build tags after this gallery HUD tip. Thin SableHUD chips only — same fire verb, AimSample untouched, R6 128 Hz / Hands Worker / `fire_ms` honesty stay. Shared house and shared Bay stay a lazy lobby snapshot + fire-tick rewind (not a fake global 128 Hz friend sim). SablePort seams are identity-only. Boot **BAY** stays local. Next after this: R5 when a modeler is in Blender.

## Milestones

- **M0 (now):** Salt House visible, cuff, plates, HID fire, rooms, original IP.
- **M1:** Arcade gallery loop (plates/clays escape). Waiting-room WARM UP. Fire peeks only (no aim recompute on click). Sticky lift shipped. **Done.**
- **M2:** Landmarks + lift verb that allows trackpad fire. **Done** (Hands + R3).
- **M3:** Two clients, same plates, same house. **Done** for the room (seed + fire-tick ray). Offline / WARM UP stay local. Zip held until tip + SableQA offline-shoot gate.
- **M4:** Bay as a second playlist from the lobby, still one art bible. **Done** (boot **BAY** + lobby **ENTER BAY**; original booth; first to 5). Offline / WARM UP stay local one-click. Zip held until tip + SableQA (Bay must not be the only gun). **`v0.12.0` stands.**
- **M5:** Salt House is a playable **gallery mode** (60 s score / round clock / GALLERY CLEAR). Offline one-click stays. Bay / WARM UP / ENTER RANGE stay. **Done.** **`v0.19.0` stood.**
- **M6:** Thin arcade **SableHUD** bar for the 60 s gallery (score / round time / end chip). No bloom over the reticle, no tutorial wall, lobby stays thin. **Done.** **`v0.20.0` stood.** Build tags after this gallery tip.
- **M7:** SablePort path skeleton — `docs/port.md` + `proto/port.js` seams. Runtime art fails loud on Valve / Epic DNA. Soft-locks held. **Done.**
- **M8:** Bay 1v1 on the R6 contract — local first-to-5 pose at 128 Hz, HID fire outside, `fire_ms` stamp, thin SableHUD chips. Offline / WARM UP stay one-click. Bay is never the only gun. **Done.**
- **M9:** Shared Bay 1v1 — lobby **ENTER BAY** room-owns score / pose / `fire_ms` rewind. Boot **BAY** stays local one-click. Offline / WARM UP / ENTER RANGE stay. HID never waits on the lobby POST. **Done.** Soft-lock + merge stay with Sable. Post-M9 honesty: Shared Bay net never taxes HID. `?sableperf=1` p99 < 8 ms still holds. `tools/test_sableperf.py` / `tools/test_shared_bay.py` fail loud if `reportSharedBayFire` lands inside the probe.

## Non-goals (v1)

Ranked, anti-cheat, Steam, on-rails campaign, voice, user-generated maps, marketplace cosmetics that change tracking.

## Open questions — blocking

See the end of this file. Do not invent answers in code until they are decided.

---

### Q1. SKU — decided
v1 ship floor is **Chromium on MacBook Pro–class** (lid camera). Product verb is hand point + shark-fin; DESKTOP HID pad is honesty fallback. A living-room TV + USB webcam + clicker is a later stretch on the same web client — not a second product, not a Godot/native SKU.

### Q2. Friends
Is “with friends” **same couch / same screen** (pass the click, or two hands on one cam), **two laptops / room code**, or both?

### Q3. House fantasy — decided
Salt House v1 is a **clay gallery**: things fly at you, you stand still. Score the 60 s clock. WASD is Bay only. A house walk is a later mode, original rooms, not a clone.

### Q4. Fail to lock — decided
Waiting Yard when the camera works but no hand: **Q4 fail-to-lock is SEEKING until lock or Space** (`forceGun`). Never OS cursor. Never auto-desktop. `Space` forceGun invokes `updateMode` before `afterLiftState`. `drawModeChip` does not prefer SEEKING when `S.forceGun` or `S.mode === "GUN"`. Thin SableHUD SEEKING chip so the state is not silent. Camera **deny** still arms DESKTOP on the live lobby (`armPracticeDesktop`) — camera deny is not fail-to-lock. Offline lock timeout → `goDesktopRange` stays Offline. KeyT desktop toggle may remain as debug when `camReady` — not the Q4 product path. KeyT must not disarm DESKTOP on cam-deny waiting Yard (`lobby` / `wait_practice`) — re-arm via `armPracticeDesktop`.

### Q5. Art soT
Are runtime procedural meshes enough until Blender stills exist, or must GLB from Blender load in the client before a public tag?

### Q6. Violence analog
Plates only (sporting clays), or original creatures that are **not** zombies/ducks? This changes art, VO, and stores.

### Q7. Trigger hardware
Trackpad only, or also **space / USB foot pedal / second mouse** as first-class HID?
