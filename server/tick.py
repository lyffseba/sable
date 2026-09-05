#!/usr/bin/env python3
"""128 Hz dedicated tick. Mojo hitscan is authoritative for the sim peek.

Named sim rate for the discrete stepper. Render stays rAF. HID fire peeks
AimBus and does not wait on this clock. Shared house is rewind, not this loop.
See docs/tick.md.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from sable_mojo import hitscan, ping  # noqa: E402

HZ = 128
DT = 1.0 / HZ


def main() -> int:
    ident = ping()
    print(f"SABLE headless tick  {HZ} Hz  mojo={ident or 'off'}", flush=True)
    origin = [0.0, 1.64, 10.0]
    direction = [0.0, -0.038, -1.0]
    sphere = [0.0, 0.89, -10.0]
    hits = 0
    t0 = time.perf_counter()
    for i in range(HZ):
        step_start = time.perf_counter()
        if ident:
            res = hitscan(origin, direction, sphere, 0.52)
            if res.get("hit"):
                hits += 1
        remain = DT - (time.perf_counter() - step_start)
        if remain > 0:
            time.sleep(remain)
    elapsed = time.perf_counter() - t0
    print(
        f"SABLE headless tick ok  frames={HZ}  hits={hits}  wall={elapsed:.3f}s",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
