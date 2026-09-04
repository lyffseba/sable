#!/usr/bin/env python3
"""Load SABLE Mojo 1.0 kernels from Python (mojo.importer)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOJO_DIR = ROOT / "native" / "mojo"

_mod = None
_error = ""


def load():
    """Return the sable_kern module or None if Mojo is unavailable."""
    global _mod, _error
    if _mod is not None:
        return _mod
    if not (MOJO_DIR / "sable_kern.mojo").is_file():
        _error = "missing native/mojo/sable_kern.mojo"
        return None
    if str(MOJO_DIR) not in sys.path:
        sys.path.insert(0, str(MOJO_DIR))
    try:
        import mojo.importer  # noqa: F401
        import sable_kern

        _mod = sable_kern
        return _mod
    except Exception as exc:
        _error = str(exc)
        return None


def ping() -> str | None:
    kern = load()
    if kern is None:
        return None
    return str(kern.ping())


def centroid(width: int, height: int, blob_x: int, blob_y: int, radius: int) -> dict:
    kern = load()
    if kern is None:
        return {"ok": False, "error": _error or "mojo unavailable"}
    cx, cy, mass, found = list(kern.centroid([width, height, blob_x, blob_y, radius]))
    return {
        "ok": True,
        "cx": float(cx),
        "cy": float(cy),
        "mass": float(mass),
        "found": bool(found),
    }


def hitscan(origin: list[float], direction: list[float], sphere: list[float], radius: float) -> dict:
    kern = load()
    if kern is None:
        return {"ok": False, "error": _error or "mojo unavailable"}
    args = list(origin) + list(direction) + list(sphere) + [radius]
    hit, dist = list(kern.hitscan(args))
    return {"ok": True, "hit": bool(hit), "distance": float(dist)}


def one_euro(value: float, t_s: float, prev: float, prev_t: float) -> dict:
    kern = load()
    if kern is None:
        return {"ok": False, "error": _error or "mojo unavailable"}
    out = float(kern.one_euro_step([value, t_s, prev, prev_t]))
    return {"ok": True, "value": out}


def main() -> int:
    ident = ping()
    if not ident:
        print("mojo unavailable:", _error, file=sys.stderr)
        return 1
    print("ping", ident)
    print("centroid", centroid(640, 480, 320, 240, 24))
    print(
        "hitscan",
        hitscan([0, 1.64, 10], [0, -0.038, -1], [0, 0.89, -10], 0.52),
    )
    print("one_euro", one_euro(100.0, 0.016, 100.0, -1.0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
