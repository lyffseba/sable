#!/usr/bin/env python3
"""In-memory 5v5 waiting-arena rooms. Stdlib only."""

from __future__ import annotations

import threading
import time
import uuid

_LOCK = threading.Lock()
_ROOMS: dict[str, dict] = {}
_ALPHA = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
SLOTS = 10


def _code() -> str:
    n = int(time.time_ns() % (32**4))
    chars = []
    for _ in range(4):
        chars.append(_ALPHA[n % 32])
        n //= 32
    return "".join(reversed(chars))


def snapshot(room: dict) -> dict:
    filled = sum(1 for s in room["slots"] if s)
    return {
        "ok": True,
        "code": room["code"],
        "phase": room["phase"],
        "host": room["host"],
        "filled": filled,
        "slots": room["slots"],
    }


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


def start(code: str, player: str) -> dict:
    code = (code or "").strip().upper()
    with _LOCK:
        room = _ROOMS.get(code)
        if not room:
            return {"ok": False, "error": "no room"}
        if room["host"] != player:
            return {"ok": False, "error": "not host"}
        room["phase"] = "range"
        return snapshot(room)


def get(code: str) -> dict:
    code = (code or "").strip().upper()
    with _LOCK:
        room = _ROOMS.get(code)
        if not room:
            return {"ok": False, "error": "no room"}
        return snapshot(room)
