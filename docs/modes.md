# Modes / playlist

**The Yard** (original paintball range, `docs/yard.md`) is the **sole active map**. Salt House gallery runs on the Yard. Bay booth is **parked** — code and scenes stay; player chrome does not offer it.

Internal house phase stays `range` (`play("range")`, `setPhase("range")`). The player-facing mode name is **GALLERY**. Do not rename the phase to trap lift/HID or kill Offline.

Durable hangar session is `S.hangar`: `hangar` (boot / Offline gallery) | `wait_practice` (HUD-on-Yard waiting + WARM UP) | `match_live` (shared ENTER RANGE). It is a thin HUD seam so waiting-practice and shared gallery are not overloaded on `lobby` / `range` alone. Screen/sim phase stays `boot` / `lobby` / `lock` / `calibrate` / `range` / `results`. Server room `phase` stays `wait` | `range` | `bay`.

**SableNet hangar lock:** the room owns that session class (`wait`→`wait_practice`, `range`→`match_live`; Bay stays parked). Practice never promotes the room — only ENTER RANGE writes `match_live`. Poll / snapshot is a view of the enum. Offline Range and WARM UP stay client-local parks (no wire gate). Lift/HID never waits on a hangar write. Fail loud if fire gates on hangar or Offline / WARM UP talk to the room for hangar.

| Entry | Playlist | Rules | Soft-lock |
|-------|----------|-------|-----------|
| **OFFLINE** | local gallery (`play("range")`) | 60 s clock, score, ESC = miss, `GALLERY CLEAR` | one click, local |
| **WARM UP** | local gallery, seat stays | same house, practice — RETURN TO LOBBY | one click, no `/api/lobby/start` |
| **ENTER RANGE** | shared Salt House / Yard | same 60 s gallery, room owns plates + sit / flyer pose + SCORE | host shares the live Yard; phase-preserve — skip calib/lock when already lifted |

Sit / flyer pose is closed-form from life (`sitPoseY` / `sit_pose_y`: bob then drop; `flyerPose` / `flyer_pose`: `y0 + vy0*t - 0.5*g*t^2`). Hitscan is the same sphere (`hitscanRange` / `_hitscan`). Offline / WARM UP / wait_practice local plates and match_live rewind share that house. Do not Euler-integrate flyers. Do not mesh-test the spun hex — a HID peek that hits the plate must hit the rewind sphere. The room owns seed + hits + SCORE (combo / worth) only after ENTER RANGE. `applySharedSim` snaps the book. Practice never opens the shared sim. A local peek must not keep phantom points — two friends must not both credit the same plate.

Bay (local first-to-5 / shared booth) is parked. `startBay` / `lobbyStartBay` / `house.js` booth may remain; boot `btn-bay` and lobby **ENTER BAY** stay off player chrome.

## Gallery rules (Salt House)

- Round clock is `RANGE_MS` (60 s) on the 128 Hz sim (`galleryOver` / `galleryLeftMs`).
- Score + combo are the mode. Escape (`ESC`) is a miss. Sit plates dwell, then drop. Clays leave.
- End state is **GALLERY CLEAR** (score / hits / accuracy / combo / 60 s round).
- Offline HUD session is `GALLERY`. WARM UP stays `WARM UP`. Shared house stays `SHARED`.
- Arcade feedback is a thin **SableHUD** bar (`SABLE_HUD_H` 22px): hangar chip from `S.hangar` (`WAIT` / `READY` / `LIVE`), a thin `ROOM` chip from `S.room` when `wait_practice` or `match_live`, then `SCORE`, `ROUND` + time remaining, end chip (`60s GALLERY` / session / `GALLERY CLEAR`). Charcoal plate, bone / mint / rust ink. No bloom, no tutorial wall, no paint over the cuff or reticle. Do not thicken the lobby. Waiting arena stays HUD-on-Yard (`startWaitingYard`) — local plates, thin `WAIT` + `ROOM` chips, no gallery SCORE / ROUND, no 60 s lock, no net on the click. Overlay `ROOM` stays; the HUD chip is additive so friends see the code without thicker chrome.
- Sparse **SableAudio**: dry-tick miss (escape / dry fire) and hit punch on shatter. Quiet mint-tell lift cue (`Mint. Lift.` — oscillator this cut) after GUN. Audio only — do not paint VO over the cuff. Feedback after resolve / lift state, never a fire gate. No bed, no ambience.
- Stand still. WASD is Bay only (parked booth).

## Bay rules (parked 1v1 booth)

Parked. Not playable from boot or the waiting arena. Specs stay so the booth can return later.

- First to 5 (`BAY_TO_WIN`). Pose / expose / freeze live on the 128 Hz sim (`tickBay(SIM_DT)` from `stepSim`). Hitscan peeks the last committed pose.
- Fire is HID (`fire()` → `fireBay3D`). Stamps `Bay.fireMs = committedSimMs()`. Soft-parked `lobbyStartBay` fire-and-forgets `/api/lobby/bay` — never `/api/lobby/start` (that starts the house). Shared resolve is a lazy snapshot + fire-tick rewind. `reportSharedBayFire` / pose / lobby poll stay after `SablePerf.markHid` — HID→hitscan p99 < 8 ms still holds. No 128 Hz friend loop.
- Room-owned shared Bay (parked): last committed pose mailbox + peeked UV + `fire_ms` on the 128 Hz grid. The room ray-tests that UV against the foe capsule at that tick. A miss stays a miss. Open-middle death is an expose intent the room verifies.
- Arcade feedback is the same thin **SableHUD** bar: `YOU` / `THEM` / `ROUND` + cover chip + `FIRST TO 5` / `MATCH`. Charcoal plate, bone / mint / rust ink. No bloom, no tutorial wall, no paint over the cuff.

## Geometry

CS / Fortnite layout literacy is **architecture notes only** (`docs/port.md`, `research/`). Fortnite-class on the Look bar is **silhouette literacy only** (charcoal / bone / mint / rust). Runtime Salt House / Yard / Bay is original SABLE geometry. Zero Valve / Epic / UEFN asset DNA — no `de_*` halls, no Marketplace packs, no third-party map files.

## Port path

SablePort owns later-migrate notes. Verb stays AimBus / HID peek. Sim stays 128 Hz with fire outside. Look bible stays charcoal / bone / mint / rust. Playlist stays this file. Runtime host is SABLE — `proto/port.js` is identity only. Destinations named in `docs/port.md` are feeling / architecture, not content.

## Do not

- Do not offer Bay from boot or lobby. The Yard is the sole active map.
- Do not wait on a camera frame, the Hands worker, or the 128 Hz step to fire.
- Do not bloom the reticle. Charcoal / bone / mint / rust only. Yard bunkers stay charcoal / rust (few, low) so bone plates read.
- Do not hide the gun with HUD copy. SableHUD stays a thin top bar over live aim.
- Do not thicken the lobby. Waiting-arena chrome stays WARM UP / ENTER RANGE (+ LEAVE). The waiting arena is HUD-on-Yard always-practice — live plates, thin `WAIT` + `ROOM` chips from `S.hangar` / `S.room` — not a match-start screen. Do not paint hangar chips from screen phase; read `S.hangar` only. Do not hide the gun with a ROOM chip.
- Do not force calib/lock on ENTER RANGE when the Yard is already live. Promote is SableNet phase-preserve (`enterRangePreserve`) — lift/HID never waits on the lobby POST.
- Do not collapse `wait_practice` and `match_live` back onto `lobby` / `range` alone. `S.hangar` is the durable session enum (`assignHangar` / `syncHangar`).
- Do not let a client invent hangar for a shared room. The room snapshot owns hangar.
- Do not promote hangar from WARM UP / practice. Only ENTER RANGE writes `match_live`.
- Do not touch `AimSample`. Fire peeks `AimBus` only.
