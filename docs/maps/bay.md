# Bay — first 1v1

Original booth. Not a third-party map. Specs live in this repo.

Live client is `proto/` (`house.js` booth + combat, `boot.js` playlist). Godot paths below are the original layout spec and may be stale.

Scene: `godot/scenes/bay/Bay.tscn`. Controller: `godot/src/app/bay_controller.gd`. App state: `App.State.BAY`.

## Run

`python3 tools/serve_proto.py` → **http://127.0.0.1:8080**

- Boot **BAY**, or lobby **ENTER BAY** (local first-to-5; does not start the shared house)
- Offline **OFFLINE** and lobby **WARM UP** / **ENTER RANGE** stay the Salt House gallery paths

Godot **4.7.2** → import `godot/` (spec reference):

- **F5** → Boot → **Enter Bay**
- **F6** on `godot/scenes/bay/Bay.tscn`

**T** desktop aim. **Space** force gun (`AimSample.lifted`). **WASD** only while PAD. **L** cycles locker style (see `docs/operators/cancho.md`). Click fires the latest `AimSample`.

## Combat verb

Pad-strafe to cover. Lift. Take the fight. Drop.

Physical ADS is the gun. Fire is always HID against the latest `AimSample`. Do not wait for a camera frame. Do not touch `AimSample` or the tracker.

## Layout (meters, as shipped)

Booth floor `16 × 28`. Walls at `x = ±8`, `z = ±14`. Dark unshaded charcoal. No world glow. Low stall in the open middle. Left window and right angle are the only lift-peeks.

| Piece | Position | Notes |
|-------|----------|--------|
| Player spawn A | `(0, 0, 10)` | `SPAWN_A`. Collision / body sit at eye-capsule height `0.89`. |
| Foe spawn B | `(0, 0.89, -10)` | `SPAWN_B`. ~20 m down the booth. Capsule `1.78` tall, mesh radius `0.32`. |
| Center stall | `(0, 0.42, 0)` size `4.2 × 0.84 × 1.1` | Low. Pad-strafe behind it. |
| Left window volume | `x ∈ (−7.5, −4.8)`, `z ∈ (2.4, 5.6)` | `_in_left_window`. Cover chip `WINDOW`. |
| Right angle volume | `x ∈ (4.6, 7.5)`, `z ∈ (1.6, 5.8)` | `_in_right_angle`. Cover chip `ANGLE`. |

Open middle is death. After **0.12 s** (`EXPOSE_S`) standing in the kill volume you die and the foe scores.

Open-middle test (`_in_open_middle`): `z ≤ 0.65` and `z > −12.5` and `|x| < 7.6`, **except** the left window and right angle volumes. North of `z = 0.65` is pad side (spawn A). Cover chip `OPEN` while exposed.

## Score and rounds

First to **5** (`TO_WIN`). HUD: `CANCHO  you — them  ·  style`. Chip `FIRST TO 5`.

| Phase | HUD chip | Rule |
|-------|----------|------|
| PAD | `PAD` | `!AimSample.lifted`. WASD at `SPEED` 4.2. |
| GUN | `GUN` | Lifted. Walk locks (`wish = 0`). |
| FREEZE | `DROP` | Death or a hit that is not match point. World freezes. |
| MATCH | `DROP` | Someone reached 5. Boot button. VO `Se escribió.` |

Death freezes. After **0.45 s** (`FREEZE_PAD_S`) a drop (`!AimSample.lifted`) returns you to PAD and `_next_round()` respawns A/B. Stay lifted and you stay frozen. Match-over does not start another round.

## Move

WASD (`move_left` / `move_right` / `move_forward` / `move_back`) **only while PAD**. Lift locks walk. Superlight is the gun. Frozen and match-over also zero planar velocity.

## Fire

Same hitscan as Range: `AimSample.uv` → screen → camera ray vs the foe sphere (radius **0.46**). Peek `AimBus` / `HidFire.shot_from_bus`. Miss = dry tick (1850 Hz, 28 ms) + HUD tick. No VO. No trash talk.

Hit: you score, VO `Claro.`, freeze (or match-over). Open-middle death: them score, no VO, freeze (or match-over).

## Do not

- Do not touch `AimSample` or the tracker.
- Do not bloom, aim-assist, or RNG-smooth aim.
- Do not copy a third-party booth.
- Do not add a gun mesh or a second map file for this layout.
