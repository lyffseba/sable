#!/usr/bin/env python3
"""Waiting-arena lobby: create, join, start, leave."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lobby  # noqa: E402


def main() -> int:
    a = lobby.create("HOST")
    if not a.get("ok") or a.get("slot") != 0 or len(a["code"]) != 4:
        print(f"FAIL create {a}", file=sys.stderr)
        return 1
    b = lobby.join(a["code"], "P2")
    if not b.get("ok") or b.get("slot") != 1 or b["filled"] != 2:
        print(f"FAIL join {b}", file=sys.stderr)
        return 1
    g = lobby.get(a["code"])
    if g["slots"][0]["name"] != "HOST" or g["slots"][1]["name"] != "P2":
        print(f"FAIL get {g}", file=sys.stderr)
        return 1
    warm = lobby.warmup(a["code"], b["player"])
    if not warm.get("ok") or warm.get("phase") != "wait":
        print(f"FAIL warmup phase {warm}", file=sys.stderr)
        return 1
    slots = lobby.get(a["code"])["slots"]
    if not slots[1] or not slots[1].get("warmup"):
        print("FAIL warmup flag missing", file=sys.stderr)
        return 1
    if slots[1]["id"] != b["player"]:
        print("FAIL warmup dropped membership", file=sys.stderr)
        return 1
    if lobby.warmup(a["code"], "nobody").get("ok"):
        print("FAIL warmup outsider", file=sys.stderr)
        return 1
    back = lobby.resume(a["code"], b["player"])
    if not back.get("ok") or back["slots"][1].get("warmup"):
        print(f"FAIL resume {back}", file=sys.stderr)
        return 1
    lobby.warmup(a["code"], a["player"])
    still = lobby.get(a["code"])
    if still.get("phase") != "wait" or still.get("filled") != 2:
        print(f"FAIL warmup must keep wait + seats {still}", file=sys.stderr)
        return 1
    bad = lobby.start(a["code"], b["player"])
    if bad.get("ok"):
        print("FAIL non-host started", file=sys.stderr)
        return 1
    st = lobby.start(a["code"], a["player"])
    if not st.get("ok") or st.get("phase") != "range":
        print(f"FAIL start {st}", file=sys.stderr)
        return 1
    if st.get("seed") is None or not st.get("plates") or st["plates"][0]["id"] != "p0":
        print(f"FAIL start missing shared sim {st}", file=sys.stderr)
        return 1
    late = lobby.join(a["code"], "LATE")
    if late.get("ok"):
        print("FAIL join after start", file=sys.stderr)
        return 1
    late_warm = lobby.warmup(a["code"], a["player"])
    if late_warm.get("ok"):
        print("FAIL warmup after start", file=sys.stderr)
        return 1
    lobby.leave(a["code"], b["player"])
    lobby.leave(a["code"], a["player"])
    gone = lobby.get(a["code"])
    if gone.get("ok"):
        print("FAIL room still live", file=sys.stderr)
        return 1
    print("lobby ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
