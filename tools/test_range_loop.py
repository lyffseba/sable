#!/usr/bin/env python3
"""Range PAD cannot skip lift. Clock-only GUN is a contract break."""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "godot/src/app/range_controller.gd"


def _fn(src: str, name: str) -> str:
    m = re.search(rf"func {name}\b[\s\S]*?(?=\nfunc |\Z)", src)
    if not m:
        raise AssertionError(f"missing func {name}")
    return m.group(0)


def main() -> int:
    try:
        text = SRC.read_text(encoding="utf-8")
        leave = _fn(text, "_can_leave_pad")
        if "PAD_END" not in leave:
            raise AssertionError("PAD must last until PAD_END")
        if "AimBus.peek().lifted" not in leave and "AimBus.peek().lifted" not in text:
            raise AssertionError("PAD must read AimSample.lifted")
        if "lifted" not in leave:
            raise AssertionError("_can_leave_pad must gate on lifted")
        if re.search(r"return true\n\treturn true", leave):
            raise AssertionError("unreachable leave-pad")
        fat = _fn(text, "_on_fat_hit")
        if "_can_leave_pad()" not in fat:
            raise AssertionError("fat hit must reuse the lift gate, not elapsed-only")
        if re.search(r"if _elapsed >= PAD_END:", fat):
            raise AssertionError("fat hit must not enter GUN on the clock alone")
        fire = _fn(text, "_fire")
        if "Phase.DROP" not in fire:
            raise AssertionError("DROP must ignore fire")
    except (OSError, AssertionError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("range pad-lift gate ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
