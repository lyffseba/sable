#!/usr/bin/env python3
"""In-memory 5v5 waiting-arena rooms + shared Salt House sim. Stdlib only.

Shared house is closed-form pose at elapsed_ms + fire-tick rewind.
Snapshot is a view. fire_ms snaps to the named 128 Hz grid — not rAF present.
Not a 128 Hz friend loop. See docs/tick.md.
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


def snapshot(room: dict, now: float | None = None) -> dict:
    filled = sum(1 for s in room["slots"] if s)
    out = {
        "ok": True,
        "code": room["code"],
        "phase": room["phase"],
        "host": room["host"],
        "filled": filled,
        "slots": room["slots"],
    }
    if room["phase"] == "range" and room.get("sim"):
        t = time.time() if now is None else now
        out.update(_sim_view(room["sim"], t))
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
    """Stay in the room. Phase stays wait. Practice does not start the match."""
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
        if room["phase"] != "range" or not room.get("sim"):
            room["phase"] = "range"
            room["sim"] = _new_sim(secrets.randbits(32) if seed is None else seed, t)
        else:
            _sync_sim(room["sim"], t)
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
