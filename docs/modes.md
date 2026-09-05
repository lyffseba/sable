# Modes / playlist

Salt House is a **gallery mode**. Bay is a booth. WARM UP is practice. None of them is the only gun.

Internal house phase stays `range` (`play("range")`, `setPhase("range")`). The player-facing mode name is **GALLERY**. Do not rename the phase to trap lift/HID or kill Offline.

| Entry | Playlist | Rules | Soft-lock |
|-------|----------|-------|-----------|
| **OFFLINE** | local gallery (`play("range")`) | 60 s clock, score, ESC = miss, `GALLERY CLEAR` | one click, local |
| **WARM UP** | local gallery, seat stays | same house, practice — RETURN TO LOBBY | one click, no `/api/lobby/start` |
| **ENTER RANGE** | shared Salt House | same 60 s gallery, room owns plates | host starts the house |
| **BAY** / **ENTER BAY** | local first-to-5 | cover vs open middle | never replaces gallery |

## Gallery rules (Salt House)

- Round clock is `RANGE_MS` (60 s) on the 128 Hz sim (`galleryOver` / `galleryLeftMs`).
- Score + combo are the mode. Escape (`ESC`) is a miss. Sit plates dwell, then drop. Clays leave.
- End state is **GALLERY CLEAR** (score / hits / accuracy / combo / 60 s round).
- Offline HUD session is `GALLERY`. WARM UP stays `WARM UP`. Shared house stays `SHARED`.
- Arcade feedback is a thin **SableHUD** bar (`SABLE_HUD_H` 22px): `SCORE`, `ROUND` + time remaining, end chip (`60s GALLERY` / session / `GALLERY CLEAR`). Charcoal plate, bone / mint / rust ink. No bloom, no tutorial wall, no paint over the cuff or reticle. Do not thicken the lobby.
- Stand still. WASD is Bay only.

## Geometry

CS / Fortnite layout literacy is **architecture notes only** (`research/`). Runtime Salt House / Yard / Bay is original SABLE geometry. Zero Valve / Epic asset DNA — no `de_*` halls, no Marketplace packs, no third-party map files.

## Do not

- Do not make gallery the only gun. Bay, WARM UP, and ENTER RANGE stay.
- Do not wait on a camera frame, the Hands worker, or the 128 Hz step to fire.
- Do not bloom the reticle. Charcoal / bone / mint / rust only.
- Do not hide the gun with HUD copy. SableHUD stays a thin top bar.
- Do not touch `AimSample`. Fire peeks `AimBus` only.
