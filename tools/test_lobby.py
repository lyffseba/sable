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
    bad = lobby.start(a["code"], b["player"])
    if bad.get("ok"):
        print("FAIL non-host started", file=sys.stderr)
        return 1
    st = lobby.start(a["code"], a["player"])
    if not st.get("ok") or st.get("phase") != "range":
        print(f"FAIL start {st}", file=sys.stderr)
        return 1
    late = lobby.join(a["code"], "LATE")
    if late.get("ok"):
        print("FAIL join after start", file=sys.stderr)
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
