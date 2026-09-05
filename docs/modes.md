# Modes / playlist

Salt House is a **gallery mode**. Bay is a booth. WARM UP is practice. None of them is the only gun.

Internal house phase stays `range` (`play("range")`, `setPhase("range")`). The player-facing mode name is **GALLERY**. Do not rename the phase to trap lift/HID or kill Offline.

| Entry | Playlist | Rules | Soft-lock |
|-------|----------|-------|-----------|
| **OFFLINE** | local gallery (`play("range")`) | 60 s clock, score, ESC = miss, `GALLERY CLEAR` | one click, local |
| **WARM UP** | local gallery, seat stays | same house, practice — RETURN TO LOBBY | one click, no `/api/lobby/start` |
| **ENTER RANGE** | shared Salt House | same 60 s gallery, room owns plates | host starts the house |
| **BAY** | local first-to-5 | cover vs open middle, R6 128 Hz / HID outside / `fire_ms` stamp | one-click local; no room |
| **ENTER BAY** | shared first-to-5 | same booth, room owns score / pose / `fire_ms` rewind | host starts the booth; never `/api/lobby/start` |

## Gallery rules (Salt House)

- Round clock is `RANGE_MS` (60 s) on the 128 Hz sim (`galleryOver` / `galleryLeftMs`).
- Score + combo are the mode. Escape (`ESC`) is a miss. Sit plates dwell, then drop. Clays leave.
- End state is **GALLERY CLEAR** (score / hits / accuracy / combo / 60 s round).
- Offline HUD session is `GALLERY`. WARM UP stays `WARM UP`. Shared house stays `SHARED`.
- Arcade feedback is a thin **SableHUD** bar (`SABLE_HUD_H` 22px): `SCORE`, `ROUND` + time remaining, end chip (`60s GALLERY` / session / `GALLERY CLEAR`). Charcoal plate, bone / mint / rust ink. No bloom, no tutorial wall, no paint over the cuff or reticle. Do not thicken the lobby.
- Sparse **SableAudio**: dry-tick miss (escape / dry fire) and hit punch on shatter. Quiet mint-tell lift cue (`Mint. Lift.` — oscillator this cut) after GUN. Audio only — do not paint VO over the cuff. Feedback after resolve / lift state, never a fire gate. No bed, no ambience.
- Stand still. WASD is Bay only.

## Bay rules (1v1 booth)

- First to 5 (`BAY_TO_WIN`). Pose / expose / freeze live on the 128 Hz sim (`tickBay(SIM_DT)` from `stepSim`). Hitscan peeks the last committed pose.
- Fire is HID (`fire()` → `fireBay3D`). Stamps `Bay.fireMs = committedSimMs()`. Boot **BAY** has no `/api/lobby/*`. Lobby **ENTER BAY** fire-and-forgets `/api/lobby/bay` — never `/api/lobby/start` (that starts the house). Shared resolve is a lazy snapshot + fire-tick rewind. `reportSharedBayFire` / pose / lobby poll stay after `SablePerf.markHid` — HID→hitscan p99 < 8 ms still holds. No 128 Hz friend loop.
- Room-owned shared Bay: last committed pose mailbox + peeked UV + `fire_ms` on the 128 Hz grid. The room ray-tests that UV against the foe capsule at that tick. A miss stays a miss. Open-middle death is an expose intent the room verifies.
- Arcade feedback is the same thin **SableHUD** bar: `YOU` / `THEM` / `ROUND` + cover chip + `FIRST TO 5` / `MATCH`. Charcoal plate, bone / mint / rust ink. No bloom, no tutorial wall, no paint over the cuff.
- Boot **BAY** stays one-click local without a room. Lobby **ENTER BAY** drops into the booth immediately — if the lobby POST hangs, local BAY still fires. Offline **GALLERY**, **WARM UP**, and **ENTER RANGE** stay. Bay is never the only gun.

## Geometry

CS / Fortnite layout literacy is **architecture notes only** (`docs/port.md`, `research/`). Runtime Salt House / Yard / Bay is original SABLE geometry. Zero Valve / Epic asset DNA — no `de_*` halls, no Marketplace packs, no third-party map files.

## Port path

SablePort owns later-migrate notes. Verb stays AimBus / HID peek. Sim stays 128 Hz with fire outside. Look bible stays charcoal / bone / mint / rust. Playlist stays this file. Runtime host is SABLE — `proto/port.js` is identity only. Destinations named in `docs/port.md` are feeling / architecture, not content.

## Do not

- Do not make gallery the only gun. Bay, WARM UP, and ENTER RANGE stay.
- Do not wait on a camera frame, the Hands worker, or the 128 Hz step to fire.
- Do not bloom the reticle. Charcoal / bone / mint / rust only.
- Do not hide the gun with HUD copy. SableHUD stays a thin top bar over live aim.
- Do not thicken the lobby. Waiting-arena chrome stays WARM UP / ENTER RANGE / ENTER BAY.
- Do not touch `AimSample`. Fire peeks `AimBus` only.
