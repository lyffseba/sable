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
    bus_h = ROOT / "native/cv_input/include/sable/aim_bus.hpp"
    proto_js = ROOT / "proto/aim.js"
    mojo_s = ROOT / "native/mojo/aim_sample.mojo"
    mojo_b = ROOT / "native/mojo/aim_bus.mojo"
    missing = []
    for path in (native, bus_h, proto_js, mojo_s, mojo_b):
        if not path.is_file():
            missing.append(f"missing file: {path}")
    if missing:
        print("\n".join(missing), file=sys.stderr)
        return 1

    bad = must_contain(native, ("uv_x", "uv_y", "valid", "lifted", "confidence", "t_hw"))
    bad += [f"mojo:{n}" for n in must_contain(mojo_s, ("uv_x", "uv_y", "valid", "lifted", "confidence", "t_hw"))]
    bad += [f"proto:{n}" for n in must_contain(proto_js, FIELDS)]
    bad += [f"bus.h:{n}" for n in must_contain(bus_h, ("fire", "peek"))]
    bad += [f"bus.mojo:{n}" for n in must_contain(mojo_b, ("fire", "peek"))]
    bad += [f"bus.js:{n}" for n in must_contain(proto_js, ("class AimBus", "peek(", "fire("))]
    if bad:
        print("AimSample contract missing:", ", ".join(bad), file=sys.stderr)
        return 1
    print("AimSample protocol ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
