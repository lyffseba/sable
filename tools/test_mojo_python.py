#!/usr/bin/env python3
"""Python ↔ Mojo 1.0 kernel contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from sable_mojo import centroid, hitscan, load, one_euro, ping  # noqa: E402


def main() -> int:
    if load() is None:
        print("mojo python bindings skipped (no pixi/mojo env)")
        return 0
    ident = ping()
    if ident != "sable-mojo-1.0":
        print(f"FAIL: ping={ident!r}", file=sys.stderr)
        return 1
    c = centroid(640, 480, 320, 240, 24)
    if not c.get("ok") or not c.get("found"):
        print(f"FAIL: centroid {c}", file=sys.stderr)
        return 1
    if abs(c["cx"] - 320.0) > 0.2 or abs(c["cy"] - 240.0) > 0.2:
        print(f"FAIL: centroid accuracy {c}", file=sys.stderr)
        return 1
    h = hitscan([0, 1.64, 10], [0, -0.038, -1], [0, 0.89, -10], 0.52)
    if not h.get("ok") or not h.get("hit"):
        print(f"FAIL: hitscan {h}", file=sys.stderr)
        return 1
    e = one_euro(100.0, 0.016, 100.0, -1.0)
    if not e.get("ok") or abs(e["value"] - 100.0) > 1e-6:
        print(f"FAIL: one_euro {e}", file=sys.stderr)
        return 1
    print("mojo python bindings ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
