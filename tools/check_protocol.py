#!/usr/bin/env python3
"""Verify the AimSample contract exists on both sides of the engine."""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIELDS = ("uv", "valid", "lifted", "confidence", "t_hw")


def must_contain(path: pathlib.Path, needles: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [n for n in needles if n not in text]


def main() -> int:
    native = ROOT / "native/cv_input/include/sable/aim_sample.hpp"
    gdscript = ROOT / "godot/src/input/aim_sample.gd"
    bus_h = ROOT / "native/cv_input/include/sable/aim_bus.hpp"
    bus_gd = ROOT / "godot/src/input/aim_bus.gd"
    missing = []
    for path in (native, gdscript, bus_h, bus_gd):
        if not path.is_file():
            missing.append(f"missing file: {path}")
    if missing:
        print("\n".join(missing), file=sys.stderr)
        return 1

    bad = must_contain(native, ("uv_x", "uv_y", "valid", "lifted", "confidence", "t_hw"))
    bad += [f"gdscript:{n}" for n in must_contain(gdscript, FIELDS)]
    fire_needles = ("fire", "peek")
    bad += [f"bus.h:{n}" for n in must_contain(bus_h, fire_needles)]
    bad += [f"bus.gd:{n}" for n in must_contain(bus_gd, fire_needles)]
    if bad:
        print("AimSample contract missing:", ", ".join(bad), file=sys.stderr)
        return 1
    print("AimSample protocol ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
