#!/usr/bin/env python3
"""In-memory 5v5 waiting-arena rooms + shared Salt House sim. Stdlib only."""

from __future__ import annotations

import secrets
import threading
import time
import uuid

_LOCK = threading.Lock()
_ROOMS: dict[str, dict] = {}
_ALPHA = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
SLOTS = 10

RANGE_MS = 60_000
SIT_DWELL_S = 4.2
SIT_DROP_VY = -3.2
PLATE_MAX_LIFE_S = 7.5
GRAVITY = 4.6
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


def _add_plate(sim: dict, kind: str, x: float, y: float, z: float, **extra) -> dict:
    pid = f"p{sim['seq']}"
    sim["seq"] += 1
    plate = {
        "id": pid,
        "kind": kind,
        "x": float(x),
        "y": float(y),
        "z": float(z),
        "vx": float(extra.get("vx", 0.0)),
        "vy": float(extra.get("vy", 0.0)),
        "vz": float(extra.get("vz", 0.0)),
        "baseY": float(extra.get("baseY", y)),
        "worth": int(extra.get("worth", 100)),
        "born_ms": float(extra.get("born_ms", 0.0)),
        "life": float(extra.get("life", 0.0)),
    }
    sim["plates"][pid] = plate
    return plate


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


def _escaped(p: dict) -> bool:
    if p["life"] >= PLATE_MAX_LIFE_S:
        return True
    if p["kind"] in ("clay", "rise"):
        return p["y"] < -1.7 or p["x"] < -10 or p["x"] > 10 or p["z"] < -18 or p["z"] > 3
    return p["y"] < -1.7


def _advance_sim(sim: dict, now: float) -> None:
    last = float(sim["last"])
    dt = max(0.0, now - last)
    sim["last"] = now
    elapsed_ms = max(0.0, (now - float(sim["t0"])) * 1000.0)
    if dt > 0:
        gone: list[str] = []
        for pid, p in sim["plates"].items():
            p["life"] += dt
            if p["kind"] in ("clay", "rise"):
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["z"] += p["vz"] * dt
                p["vy"] -= GRAVITY * dt
            elif p["life"] >= SIT_DWELL_S:
                p["y"] += SIT_DROP_VY * dt
            if _escaped(p):
                gone.append(pid)
        for pid in gone:
            sim["plates"].pop(pid, None)
            sim["escaped"].append(pid)
    if elapsed_ms >= RANGE_MS:
        return
    want = _desired(elapsed_ms)
    hard = elapsed_ms > 35000
    while len(sim["plates"]) < want and (elapsed_ms >= 2000 or len(sim["plates"]) == 0):
        _spawn_random(sim, elapsed_ms, hard)


def _new_sim(seed: int, now: float) -> dict:
    sim = {
        "seed": int(seed) & 0xFFFFFFFF,
        "t0": now,
        "last": now,
        "seq": 0,
        "rng": _Rng(seed),
        "plates": {},
        "dead": [],
        "escaped": [],
    }
    _add_plate(sim, "sit", 0.2, 0.35, -6.6, worth=100, born_ms=0.0, baseY=0.35)
    return sim


def _sim_view(sim: dict, now: float) -> dict:
    plates = []
    for p in sim["plates"].values():
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
    plates.sort(key=lambda row: row["id"])
    return {
        "seed": sim["seed"],
        "elapsed_ms": int(max(0.0, (now - float(sim["t0"])) * 1000.0)),
        "plates": plates,
        "dead": list(sim["dead"]),
    }


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
            _advance_sim(room["sim"], t)
        return snapshot(room, t)


def get(code: str, now: float | None = None) -> dict:
    code = (code or "").strip().upper()
    t = time.time() if now is None else now
    with _LOCK:
        room = _ROOMS.get(code)
        if not room:
            return {"ok": False, "error": "no room"}
        if room["phase"] == "range" and room.get("sim"):
            _advance_sim(room["sim"], t)
        return snapshot(room, t)


def hit(code: str, player: str, plate: str, now: float | None = None) -> dict:
    """Apply a client HID hit. Validates seat + live plate. Never reads cam confidence."""
    code = (code or "").strip().upper()
    pid = (plate or "").strip()
    t = time.time() if now is None else now
    with _LOCK:
        room = _ROOMS.get(code)
        if not room:
            return {"ok": False, "error": "no room"}
        if room["phase"] != "range" or not room.get("sim"):
            return {"ok": False, "error": "not in range"}
        if not _seat(room, player):
            return {"ok": False, "error": "not in room"}
        sim = room["sim"]
        _advance_sim(sim, t)
        live = sim["plates"].pop(pid, None)
        if not live:
            known_dead = any(d.get("id") == pid for d in sim["dead"])
            return {"ok": False, "error": "already dead" if known_dead else "no plate"}
        sim["dead"].append({"id": pid, "by": player, "kind": live["kind"]})
        snap = snapshot(room, t)
    snap["hit"] = pid
    snap["by"] = player
    return snap
