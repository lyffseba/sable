#!/usr/bin/env python3
"""Aim verb proofs. Strategies that died to a counterexample stay dead."""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def mode(desktop: bool, force: bool, hid_moving: bool, det: bool, coasting: bool) -> str:
    """Chip only. Camera still writes the mailbox on PAD.
    Hand lock beats trackpad HID so a MacBook click can fire."""
    if desktop:
        return "DESKTOP"
    if force:
        return "GUN"
    if det or coasting:
        return "GUN"
    if hid_moving:
        return "PAD"
    return "SEEKING"


def lifted(desktop: bool, force: bool, hid_moving: bool, det: bool, coasting: bool) -> bool:
    if desktop or force:
        return True
    return det or coasting


def can_fire(desktop: bool, force: bool, hid_moving: bool, det: bool, coasting: bool) -> bool:
    return desktop or lifted(desktop, force, hid_moving, det, coasting)


def test_mode_table() -> None:
    assert mode(False, False, True, True, False) == "GUN"
    assert mode(False, False, False, True, False) == "GUN"
    assert mode(False, False, False, False, True) == "GUN"
    assert mode(False, False, True, False, False) == "PAD"
    assert mode(False, False, False, False, False) == "SEEKING"
    assert mode(False, True, True, False, False) == "GUN"
    assert mode(True, False, True, True, False) == "DESKTOP"


def test_lift_and_fire() -> None:
    # Hand up + trackpad click must still shoot (MacBook).
    assert lifted(False, False, True, True, False) is True
    assert can_fire(False, False, True, True, False) is True
    # Hand up, pad idle.
    assert lifted(False, False, False, True, False) is True
    assert can_fire(False, False, False, True, False) is True
    # Hand down, pad moving: no shoot.
    assert can_fire(False, False, True, False, False) is False
    # Space.
    assert can_fire(False, True, True, False, False) is True
    # T debug always shoots.
    assert can_fire(True, False, True, False, False) is True


def test_ruled_out() -> None:
    """Desktop HID-idle as lift: cursor IS the gun, idle means you cannot aim."""
    assert mode(True, False, True, False, False) == "DESKTOP"
    assert can_fire(True, False, True, False, False) is True


def _fn(src: str, name: str) -> str:
    m = re.search(rf"func {name}\b[\s\S]*?(?=\nfunc |\Z)", src)
    if not m:
        raise AssertionError(f"missing func {name}")
    return m.group(0)


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        raise AssertionError(f"missing function {name}")
    return m.group(0)


def test_proto_mailbox() -> None:
    src = (ROOT / "proto/game.js").read_text(encoding="utf-8")
    mode_body = _js_fn(src, "updateMode")
    hid = mode_body.find("if (S.hidMoving)")
    locked = mode_body.find("if (locked)")
    if hid < 0 or locked < 0 or locked > hid:
        raise AssertionError("chip: hand lock must beat trackpad HID")
    if "S.lifted" not in mode_body:
        raise AssertionError("updateMode must write lifted")

    aim = _js_fn(src, "updateAim")
    if "S.mode" in aim:
        raise AssertionError("camera must write aim with no mode gate")
    if "camToScreen" not in aim:
        raise AssertionError("updateAim maps camera to screen")
    if "function publishAim" not in src:
        raise AssertionError("one publisher for the mailbox")

    fire = _js_fn(src, "fire")
    if 'S.mode === "PAD"' in fire:
        raise AssertionError("fire gates on lifted, not the chip")
    if "!S.lifted" not in fire:
        raise AssertionError("fire peeks lifted")

    move = re.search(r"pointermove[\s\S]{0,280}", src)
    if not move or "if (S.desktop)" not in move.group(0):
        raise AssertionError("OS pointer writes aim only in DESKTOP")

    if src.count("drawCrosshair(S.aim.x, S.aim.y)") < 2:
        raise AssertionError("calib + range must draw the reticle")
    if 'if (S.mode === "GUN" || S.mode === "DESKTOP" || S.mode === "SEEKING")' in src:
        raise AssertionError("PAD must not hide the reticle")


def test_pointing_filter() -> None:
    src = (ROOT / "proto/game.js").read_text(encoding="utf-8")
    m = re.search(r"EURO_MINCUTOFF = ([0-9.]+)", src)
    if not m or float(m.group(1)) < 2.5:
        raise AssertionError("One Euro mincutoff must be pointing-fast, not 1Hz soup")
    if "function adaptTpl" not in src:
        raise AssertionError("strong lock must refresh the template")
    if "function findHand" not in src:
        raise AssertionError("hand is the gun: findHand must exist")
    lost = _js_fn(src, "nccTrack")
    if "age > COAST_MS && S.euroX" in lost:
        raise AssertionError("do not kill euro/velocity at coast — only after QUALITY_LOST_MS")
    if "QUALITY_LOST_MS" not in lost:
        raise AssertionError("long hole resets filters, short hole coasts")
    mode_body = _js_fn(src, "updateMode")
    if "LIFT_ON_MS" not in mode_body and "S.liftMs" not in mode_body:
        raise AssertionError("lift needs hysteresis so HID noise does not flicker fire")


def test_range_gate() -> None:
    src = (ROOT / "proto/game.js").read_text(encoding="utf-8")
    fire_body = _js_fn(src, "fire")
    if "lifted" not in fire_body:
        raise AssertionError("Range fire must gate on AimSample.lifted")
    if "!S.desktop && !S.lifted" not in fire_body:
        raise AssertionError("Range fire must gate on lifted unless desktop")


def main() -> int:
    try:
        test_mode_table()
        test_lift_and_fire()
        test_ruled_out()
        test_proto_mailbox()
        test_pointing_filter()
        test_range_gate()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("aim verb ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
