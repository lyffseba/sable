# SABLE proto

Chrome range. Webcam tracks the physical mouse. The camera is never drawn.

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

1. **OFFLINE** (60s gallery on the Yard) or **ONLINE** (HUD-on-Yard always-practice) → **WARM UP** / **ENTER RANGE** (shared live Yard, skip calib/lock when already lifted). Bay booth is parked.
2. Hold the mouse up to the webcam until it locks. Stay on SEEKING until a template exists — no OS-mouse fallback.
3. Four corners — aim the mouse-gun, click each, then one center shot.
4. Gallery: 60-second scored plates/clays. Escape = miss.

## Keys

| Key | What |
|-----|------|
| **T** | Hidden debug: desktop-aim |
| **Space** (hold) | Force GUN |
| **WASD** | Bay PAD move (locked while lifted) |
| **L** | Bay: cycle CANCHO style |

Mode chip: `PAD` / `GUN` / `DESKTOP` / `SEEKING`. Gallery SableHUD chips: hangar `WAIT` / `READY` / `LIVE` from `S.hangar` (room snapshot owns hangar on the wire), thin `ROOM` on `wait_practice` / `match_live`, then `SCORE` / `ROUND` / `60s GALLERY`. Lift plays a quiet mint-tell chirp (`Mint. Lift.`).
