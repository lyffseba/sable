#!/usr/bin/env python3
"""Aim verb proofs. Strategies that died to a counterexample stay dead."""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def mode(desktop: bool, force: bool, hid_moving: bool, det: bool, coasting: bool) -> str:
    """Proto updateMode, extracted. HID on the mat beats a live NCC lock."""
    if desktop:
        return "DESKTOP"
    if force:
        return "GUN"
    if hid_moving:
        return "PAD"
    if det or coasting:
        return "GUN"
    return "SEEKING"


def test_mode_table() -> None:
    # Camera still sees the Superlight on the pad. That is not a gun.
    assert mode(False, False, True, True, False) == "PAD"
    assert mode(False, False, True, True, True) == "PAD"
    # Lift-off: HID silent, lock holds.
    assert mode(False, False, False, True, False) == "GUN"
    # 100 ms hole: coast, still GUN, UV must not snap.
    assert mode(False, False, False, False, True) == "GUN"
    # Lost.
    assert mode(False, False, False, False, False) == "SEEKING"
    # Space.
    assert mode(False, True, True, False, False) == "GUN"
    # T debug.
    assert mode(True, False, True, True, False) == "DESKTOP"


def test_ruled_out() -> None:
    """Desktop HID-idle as lift: cursor IS the gun, idle means you cannot aim."""
    # If we treated desktop hid_moving as PAD, debug T could not paint UV.
    assert mode(True, False, True, False, False) == "DESKTOP"


def _fn(src: str, name: str) -> str:
    m = re.search(rf"func {name}\b[\s\S]*?(?=\nfunc |\Z)", src)
    if not m:
        raise AssertionError(f"missing func {name}")
    return m.group(0)


def test_proto_source_order() -> None:
    src = (ROOT / "proto/game.js").read_text(encoding="utf-8")
    m = re.search(r"function updateMode\([^)]*\) \{[\s\S]*?\n\}", src)
    if not m:
        raise AssertionError("missing updateMode")
    body = m.group(0)
    hid = body.find("if (S.hidMoving)")
    gun = body.find("if (detGood() || coasting)")
    if hid < 0 or gun < 0:
        raise AssertionError("updateMode must test hidMoving and detGood")
    if hid > gun:
        raise AssertionError("hidMoving must beat detGood — pad HID is PAD")


def test_camera_writes_aim() -> None:
    src = (ROOT / "proto/game.js").read_text(encoding="utf-8")
    m = re.search(r"function updateAim\(\) \{[\s\S]*?\n\}", src)
    if not m:
        raise AssertionError("missing updateAim")
    body = m.group(0)
    if 'S.mode === "GUN"' in body:
        raise AssertionError("camera must drive the reticle even on PAD")
    if "camToScreen" not in body:
        raise AssertionError("updateAim maps camera to screen")
    move = re.search(r"pointermove[\s\S]{0,400}", src)
    if not move:
        raise AssertionError("missing pointermove")
    block = move.group(0)
    if "S.aim.x = e.clientX" in block and "if (S.desktop)" not in block:
        raise AssertionError("OS pointer must not write aim outside DESKTOP")


def test_range_gate() -> None:
    text = (ROOT / "godot/src/app/range_controller.gd").read_text(encoding="utf-8")
    leave = _fn(text, "_can_leave_pad")
    if "lifted" not in leave:
        raise AssertionError("Range PAD must gate on AimSample.lifted")
    fat = _fn(text, "_on_fat_hit")
    if "_can_leave_pad()" not in fat:
        raise AssertionError("fat hit must reuse the lift gate")
    if re.search(r"if _elapsed >= PAD_END:", fat):
        raise AssertionError("fat hit must not enter GUN on the clock alone")


def main() -> int:
    try:
        test_mode_table()
        test_ruled_out()
        test_proto_source_order()
        test_camera_writes_aim()
        test_range_gate()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("aim verb ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
