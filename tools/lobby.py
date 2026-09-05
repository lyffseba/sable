#!/usr/bin/env python3
"""In-memory 5v5 waiting-arena rooms + shared Salt House / Bay. Stdlib only.

Shared house is closed-form pose at elapsed_ms + fire-tick rewind.
Shared Bay is a pose mailbox + fire-tick rewind (score / pose / fire_ms).
Snapshot is a view. fire_ms snaps to the named 128 Hz grid — not rAF present.
Not a 128 Hz friend loop. See docs/tick.md.

Room owns hangar session class (wait→wait_practice, range→match_live).
Bay stays parked (hangar, never match_live). Practice never promotes.
Poll / snapshot is a view of that enum. Fire never waits on this field.
"""

from __future__ import annotations

import math
import secrets
import threading
import time
import uuid

_LOCK = threading.Lock()
_ROOMS: dict[str, dict] = {}
_ALPHA = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
SLOTS = 10

RANGE_MS = 60_000
SIM_HZ = 128
SIM_DT_MS = 1000.0 / SIM_HZ
SIT_DWELL_S = 4.2
SIT_DROP_VY = -3.2
PLATE_MAX_LIFE_S = 7.5
GRAVITY = 4.6
REWIND_MAX_MS = 350.0
CAM_EYE = (0.0, 1.64, 2.05)
CAM_AT = (0.0, 0.55, -12.0)
CAM_UP = (0.0, 1.0, 0.0)
FOV_Y_DEG = 62.0
DEFAULT_ASPECT = 1280.0 / 720.0
YARD_PEEKS = (
    (-3.4, -0.7, -3.9),
    (3.4, -0.7, -3.9),
    (-0.5, 0.35, -6.6),
    (2.4, 0.55, -8.1),
    (-2.6, 0.05, -10.5),
    (0.8, -0.15, -12.0),
    (3.1, 0.15, -13.5),
    (-3.0, 0.25, -14.1),
)
BAY_TO_WIN = 5
BAY_FOE_RADIUS = 0.46
BAY_EYE_Y = 1.64
BAY_FOE_Y = 0.89
BAY_LOOK_DZ = 16.0
BAY_FREEZE_MS = 450.0
BAY_POSE_RING = 24
BAY_SPAWN_A = (0.0, 10.0)
BAY_SPAWN_B = (0.0, -10.0)
HANGAR_PHASES = ("hangar", "wait_practice", "match_live")


def hangar_for_phase(phase: str) -> str:
    """Map today's wait|range onto the hangar session class. Bay stays parked."""
    if phase == "wait":
        hangar = "wait_practice"
    elif phase == "range":
        hangar = "match_live"
    elif phase == "bay":
        hangar = "hangar"
    else:
        raise ValueError("SABLE HANGAR: unknown room phase " + str(phase))
    if hangar not in HANGAR_PHASES:
        raise ValueError("SABLE HANGAR: unknown hangar phase " + hangar)
    return hangar


def _assign_room_hangar(room: dict, hangar: str) -> None:
    if hangar not in HANGAR_PHASES:
        raise ValueError("SABLE HANGAR: unknown hangar phase " + str(hangar))
    room["hangar"] = hangar


def _hangar_view(room: dict) -> str:
    """Poll / snapshot view of the room-owned hangar enum. Fail loud on drift."""
    hangar = room.get("hangar")
    if hangar is None or hangar == "":
        raise ValueError("SABLE HANGAR: room snapshot missing hangar")
    if hangar not in HANGAR_PHASES:
        raise ValueError("SABLE HANGAR: unknown hangar phase " + str(hangar))
    phase = room.get("phase")
    if phase == "wait" and hangar != "wait_practice":
        raise ValueError("SABLE HANGAR: wait room must stay wait_practice")
    if phase == "range" and hangar != "match_live":
        raise ValueError("SABLE HANGAR: range room must be match_live")
    if phase == "bay" and hangar == "match_live":
        raise ValueError("SABLE HANGAR: parked bay must not be match_live")
    return hangar


def _code() -> str:
    n = int(time.time_ns() % (32**4))
    chars = []
    for _ in range(4):
        chars.append(_ALPHA[n % 32])
        n //= 32
    return "".join(reversed(chars))


class _Rng:
    """mulberry32 — same stream for a room seed. Not used for aim."""

    __slots__ = ("s",)

    def __init__(self, seed: int) -> None:
        self.s = (int(seed) & 0xFFFFFFFF) or 1

    def random(self) -> float:
        self.s = (self.s + 0x6D2B79F5) & 0xFFFFFFFF
        t = self.s
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0


def _desired(elapsed_ms: float) -> int:
    if elapsed_ms < 1800:
        return 1
    if elapsed_ms < 14000:
        return 2
    if elapsed_ms < 32000:
        return 3
    return 4


def _vec_sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vec_add(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _vec_mul(a: tuple[float, float, float], s: float) -> tuple[float, float, float]:
    return (a[0] * s, a[1] * s, a[2] * s)


def _vec_dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _vec_cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _vec_norm(a: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(_vec_dot(a, a)) or 1.0
    return _vec_mul(a, 1.0 / length)


def _cam_basis() -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    z_axis = _vec_norm(_vec_sub(CAM_EYE, CAM_AT))
    x_axis = _vec_norm(_vec_cross(CAM_UP, z_axis))
    y_axis = _vec_cross(z_axis, x_axis)
    return x_axis, y_axis, z_axis


def ray_from_uv(uv_x: float, uv_y: float, aspect: float = DEFAULT_ASPECT) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """World ray from last-committed UV. Same 62° yard camera as the client. Does not invent pose."""
    ndc_x = float(uv_x) * 2.0 - 1.0
    ndc_y = 1.0 - float(uv_y) * 2.0
    tan_h = math.tan(math.radians(FOV_Y_DEG) * 0.5)
    asp = float(aspect) if aspect and aspect > 0.2 else DEFAULT_ASPECT
    cam_x, cam_y, cam_z = _cam_basis()
    local = (ndc_x * tan_h * asp, ndc_y * tan_h, -1.0)
    world = _vec_add(_vec_add(_vec_mul(cam_x, local[0]), _vec_mul(cam_y, local[1])), _vec_mul(cam_z, local[2]))
    return CAM_EYE, _vec_norm(world)


def uv_for_world(x: float, y: float, z: float, aspect: float = DEFAULT_ASPECT) -> tuple[float, float]:
    """Project a yard point to UV. Test helper — not a new aim sample."""
    cam_x, cam_y, cam_z = _cam_basis()
    w = _vec_sub((x, y, z), CAM_EYE)
    view_z = _vec_dot(w, cam_z)
    if view_z >= -1e-6:
        return (0.5, 0.5)
    tan_h = math.tan(math.radians(FOV_Y_DEG) * 0.5)
    asp = float(aspect) if aspect and aspect > 0.2 else DEFAULT_ASPECT
    ndc_x = _vec_dot(w, cam_x) / (-view_z * tan_h * asp)
    ndc_y = _vec_dot(w, cam_y) / (-view_z * tan_h)
    return ((ndc_x + 1.0) * 0.5, (1.0 - ndc_y) * 0.5)


def bay_in_left_window(x: float, z: float) -> bool:
    return -7.5 < x < -4.8 and 2.4 < z < 5.6


def bay_in_right_angle(x: float, z: float) -> bool:
    return 4.6 < x < 7.5 and 1.6 < z < 5.8


def bay_in_open_middle(x: float, z: float) -> bool:
    if bay_in_left_window(x, z) or bay_in_right_angle(x, z):
        return False
    return z <= 0.65 and z > -12.5 and abs(x) < 7.6


def _bay_cam(x: float, z: float, seat: str) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    eye = (float(x), BAY_EYE_Y, float(z))
    look_z = float(z) + BAY_LOOK_DZ if seat == "B" else float(z) - BAY_LOOK_DZ
    return eye, (float(x), BAY_FOE_Y, look_z)


def _cam_basis_at(
    eye: tuple[float, float, float],
    at: tuple[float, float, float],
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    z_axis = _vec_norm(_vec_sub(eye, at))
    x_axis = _vec_norm(_vec_cross(CAM_UP, z_axis))
    y_axis = _vec_cross(z_axis, x_axis)
    return x_axis, y_axis, z_axis


def bay_ray_from_uv(
    uv_x: float,
    uv_y: float,
    x: float,
    z: float,
    seat: str,
    aspect: float = DEFAULT_ASPECT,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Booth ray from last-committed UV + pose. Same 62° camera as the client. Does not invent pose."""
    eye, at = _bay_cam(x, z, seat)
    ndc_x = float(uv_x) * 2.0 - 1.0
    ndc_y = 1.0 - float(uv_y) * 2.0
    tan_h = math.tan(math.radians(FOV_Y_DEG) * 0.5)
    asp = float(aspect) if aspect and aspect > 0.2 else DEFAULT_ASPECT
    cam_x, cam_y, cam_z = _cam_basis_at(eye, at)
    local = (ndc_x * tan_h * asp, ndc_y * tan_h, -1.0)
    world = _vec_add(_vec_add(_vec_mul(cam_x, local[0]), _vec_mul(cam_y, local[1])), _vec_mul(cam_z, local[2]))
    return eye, _vec_norm(world)


def bay_uv_for_world(
    wx: float,
    wy: float,
    wz: float,
    x: float,
    z: float,
    seat: str,
    aspect: float = DEFAULT_ASPECT,
) -> tuple[float, float]:
    """Project a booth point to the shooter's UV. Test helper — not a new aim sample."""
    eye, at = _bay_cam(x, z, seat)
    cam_x, cam_y, cam_z = _cam_basis_at(eye, at)
    w = _vec_sub((wx, wy, wz), eye)
    view_z = _vec_dot(w, cam_z)
    if view_z >= -1e-6:
        return (0.5, 0.5)
    tan_h = math.tan(math.radians(FOV_Y_DEG) * 0.5)
    asp = float(aspect) if aspect and aspect > 0.2 else DEFAULT_ASPECT
    ndc_x = _vec_dot(w, cam_x) / (-view_z * tan_h * asp)
    ndc_y = _vec_dot(w, cam_y) / (-view_z * tan_h)
    return ((ndc_x + 1.0) * 0.5, (1.0 - ndc_y) * 0.5)


def _ray_sphere(
    origin: tuple[float, float, float],
    direction: tuple[float, float, float],
    center: tuple[float, float, float],
    radius: float,
) -> float | None:
    oc = _vec_sub(origin, center)
    b = 2.0 * _vec_dot(oc, direction)
    c = _vec_dot(oc, oc) - radius * radius
    disc = b * b - 4.0 * c
    if disc < 0.0:
        return None
    t = (-b - math.sqrt(disc)) * 0.5
    if t <= 0.0:
        return None
    return t


def _plate_radius(kind: str) -> float:
    return 0.50 if kind in ("clay", "rise") else 0.62


def _add_plate(sim: dict, kind: str, x: float, y: float, z: float, **extra) -> dict:
    pid = f"p{sim['seq']}"
    sim["seq"] += 1
    rec = {
        "id": pid,
        "kind": kind,
        "x0": float(x),
        "y0": float(y),
        "z0": float(z),
        "vx0": float(extra.get("vx", 0.0)),
        "vy0": float(extra.get("vy", 0.0)),
        "vz0": float(extra.get("vz", 0.0)),
        "baseY": float(extra.get("baseY", y)),
        "worth": int(extra.get("worth", 100)),
        "born_ms": float(extra.get("born_ms", 0.0)),
    }
    sim["spawned"].append(rec)
    return rec


def _spawn_random(sim: dict, elapsed_ms: float, hard: bool) -> dict:
    rng: _Rng = sim["rng"]
    roll = rng.random()
    kind = "sit"
    if roll > 0.42:
        kind = "clay"
    elif roll > 0.22:
        kind = "rise"
    worth = 250 if kind == "clay" else (180 if kind == "rise" else 100)
    peek = YARD_PEEKS[int(rng.random() * len(YARD_PEEKS)) % len(YARD_PEEKS)]
    if kind == "clay":
        left = rng.random() < 0.5
        return _add_plate(
            sim,
            kind,
            -8.5 if left else 8.5,
            0.7 + rng.random() * 0.7,
            -5 - rng.random() * 8,
            vx=(1 if left else -1) * (4.2 + rng.random() * (5.0 if hard else 2.2)),
            vy=1.4 + rng.random(),
            vz=-0.8 - rng.random(),
            worth=worth,
            born_ms=elapsed_ms,
        )
    if kind == "rise":
        return _add_plate(
            sim,
            kind,
            peek[0],
            -1.45,
            peek[2],
            vy=3.4 + rng.random() * 1.4,
            worth=worth,
            born_ms=elapsed_ms,
            baseY=-1.45,
        )
    return _add_plate(
        sim,
        kind,
        peek[0],
        peek[1],
        peek[2],
        worth=worth,
        born_ms=elapsed_ms,
        baseY=peek[1],
    )


def _pose_at(rec: dict, elapsed_ms: float) -> dict:
    life = max(0.0, (float(elapsed_ms) - float(rec["born_ms"])) / 1000.0)
    if rec["kind"] in ("clay", "rise"):
        x = rec["x0"] + rec["vx0"] * life
        y = rec["y0"] + rec["vy0"] * life - 0.5 * GRAVITY * life * life
        z = rec["z0"] + rec["vz0"] * life
        vy = rec["vy0"] - GRAVITY * life
        vx, vz = rec["vx0"], rec["vz0"]
    elif life >= SIT_DWELL_S:
        x, z = rec["x0"], rec["z0"]
        y = rec["baseY"] + SIT_DROP_VY * (life - SIT_DWELL_S)
        vx = vy = vz = 0.0
    else:
        x, y, z = rec["x0"], rec["baseY"], rec["z0"]
        vx = vy = vz = 0.0
    return {
        "id": rec["id"],
        "kind": rec["kind"],
        "x": x,
        "y": y,
        "z": z,
        "vx": vx,
        "vy": vy,
        "vz": vz,
        "baseY": rec["baseY"],
        "worth": rec["worth"],
        "born_ms": rec["born_ms"],
        "life": life,
    }


def _escaped_at(rec: dict, elapsed_ms: float) -> bool:
    pose = _pose_at(rec, elapsed_ms)
    if pose["life"] >= PLATE_MAX_LIFE_S:
        return True
    if rec["kind"] in ("clay", "rise"):
        return pose["y"] < -1.7 or pose["x"] < -10 or pose["x"] > 10 or pose["z"] < -18 or pose["z"] > 3
    return pose["y"] < -1.7


def _dead_ids_at(sim: dict, elapsed_ms: float) -> set[str]:
    return {d["id"] for d in sim["dead"] if float(d.get("at_ms", 0.0)) <= float(elapsed_ms)}


def _live_at(sim: dict, elapsed_ms: float) -> list[dict]:
    dead = _dead_ids_at(sim, elapsed_ms)
    live = []
    for rec in sim["spawned"]:
        if float(rec["born_ms"]) > float(elapsed_ms):
            continue
        if rec["id"] in dead:
            continue
        if _escaped_at(rec, elapsed_ms):
            continue
        live.append(_pose_at(rec, elapsed_ms))
    live.sort(key=lambda row: row["id"])
    return live


def _advance_spawns(sim: dict, elapsed_ms: float) -> None:
    if elapsed_ms >= RANGE_MS:
        return
    want = _desired(elapsed_ms)
    hard = elapsed_ms > 35000
    while True:
        live = _live_at(sim, elapsed_ms)
        if not (len(live) < want and (elapsed_ms >= 2000 or len(live) == 0)):
            return
        _spawn_random(sim, elapsed_ms, hard)


def quantize_fire_ms(fire_ms: float) -> float:
    """Snap fire time onto the last committed 128 Hz tick. Never use present."""
    tick = math.floor(float(fire_ms) / SIM_DT_MS + 1e-12)
    if tick < 0:
        tick = 0
    return tick * SIM_DT_MS


def _sync_sim(sim: dict, now: float) -> float:
    sim["last"] = now
    elapsed_ms = max(0.0, (now - float(sim["t0"])) * 1000.0)
    _advance_spawns(sim, elapsed_ms)
    return elapsed_ms


def _new_sim(seed: int, now: float) -> dict:
    sim = {
        "seed": int(seed) & 0xFFFFFFFF,
        "t0": now,
        "last": now,
        "seq": 0,
        "rng": _Rng(seed),
        "spawned": [],
        "dead": [],
    }
    _add_plate(sim, "sit", 0.2, 0.35, -6.6, worth=100, born_ms=0.0, baseY=0.35)
    return sim


def _sim_view(sim: dict, now: float) -> dict:
    elapsed_ms = max(0.0, (now - float(sim["t0"])) * 1000.0)
    plates = []
    for p in _live_at(sim, elapsed_ms):
        plates.append(
            {
                "id": p["id"],
                "kind": p["kind"],
                "x": p["x"],
                "y": p["y"],
                "z": p["z"],
                "vx": p["vx"],
                "vy": p["vy"],
                "vz": p["vz"],
                "baseY": p["baseY"],
                "worth": p["worth"],
                "born_ms": p["born_ms"],
                "life": p["life"],
            }
        )
    return {
        "seed": sim["seed"],
        "elapsed_ms": int(elapsed_ms),
        "plates": plates,
        "dead": list(sim["dead"]),
    }


def _parse_uv(raw: object) -> tuple[float, float] | None:
    if isinstance(raw, (list, tuple)) and len(raw) >= 2:
        return float(raw[0]), float(raw[1])
    if isinstance(raw, dict) and "x" in raw and "y" in raw:
        return float(raw["x"]), float(raw["y"])
    return None


def _hitscan(live: list[dict], uv: tuple[float, float], aspect: float) -> dict | None:
    origin, direction = ray_from_uv(uv[0], uv[1], aspect)
    best: tuple[float, dict] | None = None
    for plate in live:
        t = _ray_sphere(origin, direction, (plate["x"], plate["y"], plate["z"]), _plate_radius(plate["kind"]))
        if t is None:
            continue
        if best is None or t < best[0]:
            best = (t, plate)
    return best[1] if best else None


def _seat(room: dict, player: str) -> dict | None:
    for s in room["slots"]:
        if s and s["id"] == player:
            return s
    return None


def _bay_filled(room: dict) -> list[dict]:
    return [s for s in room["slots"] if s]


def _bay_seats(room: dict) -> dict[str, str]:
    filled = _bay_filled(room)
    seats: dict[str, str] = {}
    if filled:
        seats[filled[0]["id"]] = "A"
    if len(filled) > 1:
        seats[filled[1]["id"]] = "B"
    return seats


def _bay_spawn(seat: str) -> tuple[float, float]:
    return BAY_SPAWN_B if seat == "B" else BAY_SPAWN_A


def _new_bay(now: float, room: dict) -> dict:
    seats = _bay_seats(room)
    poses: dict[str, list[dict]] = {}
    scores: dict[str, int] = {}
    for pid, seat in seats.items():
        x, z = _bay_spawn(seat)
        poses[pid] = [{"x": x, "z": z, "sim_ms": 0.0}]
        scores[pid] = 0
    return {
        "t0": now,
        "seats": seats,
        "scores": scores,
        "poses": poses,
        "round": 1,
        "over": False,
        "freeze_until_ms": -1.0,
        "to_win": BAY_TO_WIN,
    }


def _bay_elapsed_ms(bay: dict, now: float) -> float:
    return max(0.0, (now - float(bay["t0"])) * 1000.0)


def _bay_pose_at(samples: list[dict], fire_ms: float, seat: str) -> dict:
    chosen: dict | None = None
    for rec in samples:
        if float(rec.get("sim_ms", 0.0)) <= float(fire_ms):
            chosen = rec
        else:
            break
    if chosen is None:
        if samples:
            chosen = samples[0]
        else:
            x, z = _bay_spawn(seat)
            return {"x": x, "z": z, "sim_ms": 0.0}
    return chosen


def _bay_record_pose(bay: dict, player: str, x: float, z: float, sim_ms: float) -> None:
    ring = bay["poses"].setdefault(player, [])
    rec = {"x": float(x), "z": float(z), "sim_ms": float(sim_ms)}
    if ring and float(ring[-1].get("sim_ms", -1.0)) == rec["sim_ms"]:
        ring[-1] = rec
    else:
        ring.append(rec)
    if len(ring) > BAY_POSE_RING:
        del ring[: len(ring) - BAY_POSE_RING]


def _reset_bay_round(bay: dict) -> None:
    for pid, seat in bay["seats"].items():
        x, z = _bay_spawn(seat)
        bay["poses"][pid] = [{"x": x, "z": z, "sim_ms": 0.0}]


def _bay_score(bay: dict, scorer: str, elapsed_ms: float) -> None:
    if bay["over"]:
        return
    if elapsed_ms < float(bay.get("freeze_until_ms", -1.0)):
        return
    bay["scores"][scorer] = int(bay["scores"].get(scorer, 0)) + 1
    bay["freeze_until_ms"] = elapsed_ms + BAY_FREEZE_MS
    if bay["scores"][scorer] >= int(bay.get("to_win", BAY_TO_WIN)):
        bay["over"] = True
        return
    bay["round"] = int(bay.get("round", 1)) + 1
    _reset_bay_round(bay)


def _bay_view(bay: dict, now: float) -> dict:
    elapsed_ms = _bay_elapsed_ms(bay, now)
    poses = {}
    for pid, seat in bay["seats"].items():
        last = _bay_pose_at(bay["poses"].get(pid) or [], elapsed_ms, seat)
        poses[pid] = {"x": last["x"], "z": last["z"], "sim_ms": last["sim_ms"], "seat": seat}
    return {
        "elapsed_ms": int(elapsed_ms),
        "seats": dict(bay["seats"]),
        "scores": dict(bay["scores"]),
        "poses": poses,
        "round": int(bay.get("round", 1)),
        "over": bool(bay.get("over")),
        "to_win": int(bay.get("to_win", BAY_TO_WIN)),
        "frozen": (not bay.get("over")) and elapsed_ms < float(bay.get("freeze_until_ms", -1.0)),
    }


def snapshot(room: dict, now: float | None = None) -> dict:
    filled = sum(1 for s in room["slots"] if s)
    out = {
        "ok": True,
        "code": room["code"],
        "phase": room["phase"],
        "hangar": _hangar_view(room),
        "host": room["host"],
        "filled": filled,
        "slots": room["slots"],
    }
    t = time.time() if now is None else now
    if room["phase"] == "range" and room.get("sim"):
        out.update(_sim_view(room["sim"], t))
    if room["phase"] == "bay" and room.get("bay"):
        out.update(_bay_view(room["bay"], t))
    return out


def create(name: str = "HOST") -> dict:
    with _LOCK:
        code = _code()
        while code in _ROOMS:
            code = _code()
        pid = uuid.uuid4().hex[:8]
        slots: list[dict | None] = [None] * SLOTS
        slots[0] = {"id": pid, "name": (name or "HOST")[:12], "team": "alpha", "warmup": False}
        room = {
            "code": code,
            "phase": "wait",
            "hangar": hangar_for_phase("wait"),
            "host": pid,
            "slots": slots,
            "t": time.time(),
        }
        _ROOMS[code] = room
        snap = snapshot(room)
    snap["player"] = pid
    snap["slot"] = 0
    return snap


def join(code: str, name: str = "PLAYER") -> dict:
    code = (code or "").strip().upper()
    with _LOCK:
        room = _ROOMS.get(code)
        if not room:
            return {"ok": False, "error": "no room"}
        if room["phase"] != "wait":
            return {"ok": False, "error": "match started"}
        pid = uuid.uuid4().hex[:8]
        slot = -1
        for i, s in enumerate(room["slots"]):
            if s is None:
                slot = i
                break
        if slot < 0:
            return {"ok": False, "error": "full"}
        team = "alpha" if slot < 5 else "bravo"
        room["slots"][slot] = {
            "id": pid,
            "name": (name or "PLAYER")[:12],
            "team": team,
            "warmup": False,
        }
        snap = snapshot(room)
    snap["player"] = pid
    snap["slot"] = slot
    return snap


def leave(code: str, player: str) -> dict:
    code = (code or "").strip().upper()
    with _LOCK:
        room = _ROOMS.get(code)
        if not room:
            return {"ok": True}
        for i, s in enumerate(room["slots"]):
            if s and s["id"] == player:
                room["slots"][i] = None
        if room["host"] == player:
            nxt = next((s["id"] for s in room["slots"] if s), None)
            if nxt:
                room["host"] = nxt
            else:
                _ROOMS.pop(code, None)
                return {"ok": True, "gone": True}
        return snapshot(room)


def _mark_warmup(code: str, player: str, on: bool) -> dict:
    """Stay in the room. Phase stays wait. Practice never promotes hangar."""
    code = (code or "").strip().upper()
    with _LOCK:
        room = _ROOMS.get(code)
        if not room:
            return {"ok": False, "error": "no room"}
        if room["phase"] != "wait":
            return {"ok": False, "error": "match started"}
        found = False
        for s in room["slots"]:
            if s and s["id"] == player:
                s["warmup"] = bool(on)
                found = True
                break
        if not found:
            return {"ok": False, "error": "not in room"}
        snap = snapshot(room)
    snap["player"] = player
    return snap


def warmup(code: str, player: str) -> dict:
    return _mark_warmup(code, player, True)


def resume(code: str, player: str) -> dict:
    return _mark_warmup(code, player, False)


def start(
    code: str,
    player: str,
    now: float | None = None,
    seed: int | None = None,
) -> dict:
    code = (code or "").strip().upper()
    t = time.time() if now is None else now
    with _LOCK:
        room = _ROOMS.get(code)
        if not room:
            return {"ok": False, "error": "no room"}
        if room["host"] != player:
            return {"ok": False, "error": "not host"}
        if room["phase"] == "bay":
            return {"ok": False, "error": "bay match"}
        if room["phase"] != "range" or not room.get("sim"):
            room["phase"] = "range"
            room["sim"] = _new_sim(secrets.randbits(32) if seed is None else seed, t)
        else:
            _sync_sim(room["sim"], t)
        # SableNet: only ENTER RANGE promotes hangar to match_live.
        _assign_room_hangar(room, hangar_for_phase("range"))
        return snapshot(room, t)


def start_bay(code: str, player: str, now: float | None = None) -> dict:
    """Host starts the shared booth. Not the Salt House. Idempotent while already bay."""
    code = (code or "").strip().upper()
    t = time.time() if now is None else now
    with _LOCK:
        room = _ROOMS.get(code)
        if not room:
            return {"ok": False, "error": "no room"}
        if room["host"] != player:
            return {"ok": False, "error": "not host"}
        if room["phase"] == "range":
            return {"ok": False, "error": "match started"}
        if room["phase"] != "bay" or not room.get("bay"):
            room["phase"] = "bay"
            room["bay"] = _new_bay(t, room)
        # Parked booth. Never promote hangar to match_live.
        _assign_room_hangar(room, hangar_for_phase("bay"))
        return snapshot(room, t)


def pose(
    code: str,
    player: str,
    x: object = None,
    z: object = None,
    fire_ms: object = None,
    now: float | None = None,
) -> dict:
    """Last committed booth pose. Mailbox write — not a 128 Hz friend tick."""
    code = (code or "").strip().upper()
    t = time.time() if now is None else now
    try:
        px = float(x)
        pz = float(z)
    except (TypeError, ValueError):
        return {"ok": False, "error": "bad pose"}
    try:
        sim_ms = float(fire_ms) if fire_ms is not None else None
    except (TypeError, ValueError):
        sim_ms = None
    with _LOCK:
        room = _ROOMS.get(code)
        if not room:
            return {"ok": False, "error": "no room"}
        if room["phase"] != "bay" or not room.get("bay"):
            return {"ok": False, "error": "not in bay"}
        if not _seat(room, player):
            return {"ok": False, "error": "not in room"}
        bay = room["bay"]
        if player not in bay["seats"]:
            return snapshot(room, t)
        elapsed = _bay_elapsed_ms(bay, t)
        if sim_ms is None:
            sim_ms = elapsed
        else:
            sim_ms = quantize_fire_ms(sim_ms)
            view_ms = quantize_fire_ms(elapsed)
            if sim_ms > view_ms:
                sim_ms = view_ms
        _bay_record_pose(bay, player, px, pz, sim_ms)
        return snapshot(room, t)


def get(code: str, now: float | None = None) -> dict:
    code = (code or "").strip().upper()
    t = time.time() if now is None else now
    with _LOCK:
        room = _ROOMS.get(code)
        if not room:
            return {"ok": False, "error": "no room"}
        if room["phase"] == "range" and room.get("sim"):
            _sync_sim(room["sim"], t)
        return snapshot(room, t)


def _parse_pose(raw: object) -> tuple[float, float] | None:
    if isinstance(raw, dict) and "x" in raw and "z" in raw:
        try:
            return float(raw["x"]), float(raw["z"])
        except (TypeError, ValueError):
            return None
    if isinstance(raw, (list, tuple)) and len(raw) >= 2:
        try:
            return float(raw[0]), float(raw[1])
        except (TypeError, ValueError):
            return None
    return None


def _bay_opponent(bay: dict, player: str) -> str | None:
    for pid in bay["seats"]:
        if pid != player:
            return pid
    return None


def _bay_hit(
    room: dict,
    player: str,
    parsed: tuple[float, float] | None,
    fire_tick: float | None,
    stamp: int,
    aspect_f: float,
    pose_raw: object,
    expose: object,
    now: float,
) -> dict:
    if not _seat(room, player):
        return {"ok": False, "error": "not in room"}
    bay = room["bay"]
    if player not in bay["seats"]:
        snap = snapshot(room, now)
        snap["miss"] = True
        return snap
    elapsed_now = _bay_elapsed_ms(bay, now)
    view_ms = quantize_fire_ms(elapsed_now)
    if fire_tick is None:
        fire_tick = view_ms
    else:
        fire_tick = quantize_fire_ms(fire_tick)
        if fire_tick > view_ms:
            fire_tick = view_ms
    snap = snapshot(room, now)
    if elapsed_now - fire_tick > REWIND_MAX_MS:
        snap["miss"] = True
        snap["stale"] = True
        return snap
    if bay["over"] or elapsed_now < float(bay.get("freeze_until_ms", -1.0)):
        snap["miss"] = True
        return snap
    own_pose = _parse_pose(pose_raw)
    if own_pose is not None:
        _bay_record_pose(bay, player, own_pose[0], own_pose[1], fire_tick)
    seat = bay["seats"][player]
    shooter = _bay_pose_at(bay["poses"].get(player) or [], fire_tick, seat)
    if expose:
        if not bay_in_open_middle(shooter["x"], shooter["z"]):
            snap = snapshot(room, now)
            snap["miss"] = True
            return snap
        foe = _bay_opponent(bay, player)
        if not foe:
            snap = snapshot(room, now)
            snap["miss"] = True
            return snap
        _bay_score(bay, foe, elapsed_now)
        snap = snapshot(room, now)
        snap["expose"] = True
        snap["by"] = player
        return snap
    if parsed is None:
        snap["miss"] = True
        return snap
    foe = _bay_opponent(bay, player)
    if not foe:
        snap["miss"] = True
        return snap
    foe_seat = bay["seats"][foe]
    target = _bay_pose_at(bay["poses"].get(foe) or [], fire_tick, foe_seat)
    origin, direction = bay_ray_from_uv(parsed[0], parsed[1], shooter["x"], shooter["z"], seat, aspect_f)
    t_hit = _ray_sphere(origin, direction, (target["x"], BAY_FOE_Y, target["z"]), BAY_FOE_RADIUS)
    if t_hit is None:
        snap = snapshot(room, now)
        snap["miss"] = True
        return snap
    _bay_score(bay, player, elapsed_now)
    snap = snapshot(room, now)
    snap["hit"] = foe
    snap["by"] = player
    snap["t_hw"] = stamp
    return snap


def hit(
    code: str,
    player: str,
    uv: object = None,
    fire_ms: object = None,
    t_hw: object = None,
    aspect: object = None,
    lifted: object = None,
    now: float | None = None,
    plate: object = None,
    pose: object = None,
    expose: object = None,
) -> dict:
    """Resolve a HID fire intent. Rewind to fire_ms, ray-test the peeked UV. Ignore plate id and tracker quality."""
    del plate  # never authority
    del lifted  # FSM stays on the owning client; not a server gate
    code = (code or "").strip().upper()
    t = time.time() if now is None else now
    parsed = _parse_uv(uv)
    try:
        aspect_f = float(aspect) if aspect is not None else DEFAULT_ASPECT
    except (TypeError, ValueError):
        aspect_f = DEFAULT_ASPECT
    try:
        fire_tick = float(fire_ms) if fire_ms is not None else None
    except (TypeError, ValueError):
        fire_tick = None
    try:
        stamp = int(t_hw) if t_hw is not None else 0
    except (TypeError, ValueError):
        stamp = 0
    with _LOCK:
        room = _ROOMS.get(code)
        if not room:
            return {"ok": False, "error": "no room"}
        if room["phase"] == "bay" and room.get("bay"):
            return _bay_hit(
                room,
                player,
                parsed,
                fire_tick,
                stamp,
                aspect_f,
                pose,
                expose,
                t,
            )
        if room["phase"] != "range" or not room.get("sim"):
            return {"ok": False, "error": "not in range"}
        if not _seat(room, player):
            return {"ok": False, "error": "not in room"}
        sim = room["sim"]
        elapsed_now = _sync_sim(sim, t)
        snap = snapshot(room, t)
        if parsed is None:
            snap["miss"] = True
            return snap
        view_ms = quantize_fire_ms(elapsed_now)
        if fire_tick is None:
            fire_tick = view_ms
        else:
            fire_tick = quantize_fire_ms(fire_tick)
            if fire_tick > view_ms:
                fire_tick = view_ms
        if elapsed_now - fire_tick > REWIND_MAX_MS:
            snap["miss"] = True
            snap["stale"] = True
            return snap
        live = _live_at(sim, fire_tick)
        struck = _hitscan(live, parsed, aspect_f)
        if not struck:
            snap["miss"] = True
            return snap
        if any(d["id"] == struck["id"] for d in sim["dead"]):
            snap["miss"] = True
            snap["error"] = "already dead"
            return snap
        sim["dead"].append(
            {
                "id": struck["id"],
                "by": player,
                "kind": struck["kind"],
                "at_ms": fire_tick,
                "t_hw": stamp,
            }
        )
        snap = snapshot(room, t)
    snap["hit"] = struck["id"]
    snap["by"] = player
    return snap
