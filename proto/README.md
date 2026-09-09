# SABLE proto

Chrome range. Webcam tracks the **hand** (index / landmark 8). The mouse is HID only. The camera is never drawn.

## Zip (other computer)

Unzip `sable-proto-*.zip`, then in that folder:

```
python3 serve_proto.py
```

Open **http://127.0.0.1:8080**. PLAY. Allow camera. Tilt it **down at your hands**. Lift.

## From git

```
python3 tools/serve_proto.py
```

`file://` fails — camera needs localhost.

## Play

1. **OFFLINE** (60s gallery on the Yard) or **ONLINE** (HUD-on-Yard always-practice, camera armed without lock) → **WARM UP** (local 60s, skip calib/lock — the waiting Yard is already live) / **ENTER RANGE** (shared live Yard, skip calib/lock when already lifted). After JOIN, leftover CODE/JOIN is not the pad. Bay booth is parked.
2. Raise a hand at the lid cam. Point the index (aim). Product gun path (see `research/TRACKING.md`): shark-fin thumb fires (this cut). Index+middle up reload is out of scope. SEEKING until lock or Space (`forceGun`). Cam-deny / **T** is DESKTOP (OS cursor / pad HID). HID click must not replace the shoot gesture in gun mode.
3. Four corners — point the index.
4. Gallery: 60-second scored plates/clays. Escape = miss.

## Keys

| Key | What |
|-----|------|
| **T** | Hidden debug: desktop-aim |
| **Space** (hold) | Force GUN |
| **WASD** | Bay PAD move (locked while lifted) |
| **L** | Bay: cycle CANCHO style |

Mode chip: `PAD` / `GUN` / `DESKTOP` / `SEEKING`. Gallery SableHUD chips: hangar `WAIT` / `READY` / `LIVE` from `S.hangar` (room snapshot owns hangar on the wire), thin `ROOM` on `wait_practice` / `match_live`, then `SCORE` / `ROUND` / `60s GALLERY`. Lift plays a quiet mint-tell chirp (`Mint. Lift.`).
