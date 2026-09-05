#!/usr/bin/env python3
"""Aim verb proofs. Strategies that died to a counterexample stay dead."""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402


def _js_const(src: str, name: str) -> float:
    m = re.search(rf"const {name} = (-?[0-9.]+)", src)
    if not m:
        raise AssertionError(f"missing const {name}")
    return float(m.group(1))


def mode(
    desktop: bool,
    force: bool,
    hid_moving: bool,
    det: bool,
    coasting: bool,
    recent: bool = False,
    lifted: bool = False,
) -> str:
    """Chip only. Camera still writes the mailbox on PAD.
    Hand / recent sample owns GUN. Trackpad HID does not demote lift."""
    if desktop:
        return "DESKTOP"
    if force:
        return "GUN"
    if lifted or det or coasting or recent:
        return "GUN"
    if hid_moving:
        return "PAD"
    return "SEEKING"


def lifted(
    desktop: bool,
    force: bool,
    hid_moving: bool,
    det: bool,
    coasting: bool,
    recent: bool = False,
) -> bool:
    if desktop or force:
        return True
    return det or coasting or recent


def can_fire(
    desktop: bool,
    force: bool,
    hid_moving: bool,
    det: bool,
    coasting: bool,
    recent: bool = False,
    bus_lifted: bool = False,
) -> bool:
    # fire() peeks AimBus.lifted and recent sample — not only S.lifted.
    return desktop or force or lifted(
        desktop, force, hid_moving, det, coasting, recent
    ) or bus_lifted


def step_lift(
    lift_ms: float,
    dt: float,
    *,
    det: bool,
    coasting: bool,
    recent: bool,
    hid_moving: bool,
    force: bool = False,
    desktop: bool = False,
    lift_on_ms: float = 50.0,
    sticky_ms: float = 550.0,
    hid_hold_ms: float = 180.0,
    since_ms: float = 0.0,
) -> tuple[float, bool]:
    """Discrete updateMode lift bank. HID click freezes decay, never charges down."""
    if desktop or force:
        return lift_on_ms, True
    hand_owns = det or recent
    want = force or hand_owns
    hold_click = lift_ms >= lift_on_ms and hid_moving and since_ms <= sticky_ms + hid_hold_ms
    if want:
        lift_ms = min(160.0, lift_ms + dt)
    elif not hold_click:
        lift_ms = max(0.0, lift_ms - dt)
    return lift_ms, force or lift_ms >= lift_on_ms


def test_mode_table() -> None:
    assert mode(False, False, True, True, False) == "GUN"
    assert mode(False, False, False, True, False) == "GUN"
    assert mode(False, False, False, False, True) == "GUN"
    assert mode(False, False, True, False, False, recent=True) == "GUN"
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


def test_pad_click_while_lift_coasts() -> None:
    """Regression: point, hand leaves the lid cam, click the pad. Plates must die."""
    src = proto_js()
    lift_on = _js_const(src, "LIFT_ON_MS")
    sticky = _js_const(src, "LIFT_STICKY_MS")
    hid_hold = _js_const(src, "LIFT_HID_HOLD_MS")
    coast = _js_const(src, "COAST_MS")
    if sticky < 400:
        raise AssertionError("LIFT_STICKY_MS must cover a MacBook pad reach (>= 400 ms)")
    if coast > 150:
        raise AssertionError("UV coast must stay short — do not invent pose")

    # Boolean table: coast UV expired, recent sample + HID click.
    assert lifted(False, False, True, False, False, recent=True) is True
    assert can_fire(False, False, True, False, False, recent=True) is True
    assert mode(False, False, True, False, False, recent=True, lifted=True) == "GUN"
    # Mailbox still armed even if S.lifted flickered this frame.
    assert can_fire(False, False, True, False, False, recent=False, bus_lifted=True) is True
    # Sticky expired, no bus lift, pad moving: rest, do not shoot.
    assert can_fire(False, False, True, False, False, recent=False, bus_lifted=False) is False

    # Time series: lifted, then 120 ms hole (past UV coast), HID click at 400 ms.
    lift_ms = 160.0
    armed = True
    t = 0.0
    dt = 16.0
    while t < 400.0:
        t += dt
        recent = t <= sticky
        coasting = t <= coast
        hid = t >= 280.0
        lift_ms, armed = step_lift(
            lift_ms,
            dt,
            det=False,
            coasting=coasting,
            recent=recent,
            hid_moving=hid,
            lift_on_ms=lift_on,
            sticky_ms=sticky,
            hid_hold_ms=hid_hold,
            since_ms=t,
        )
        if t <= sticky + hid_hold:
            if not armed:
                raise AssertionError(f"lift died at {t:.0f} ms during pad reach")
    if not can_fire(False, False, True, False, False, recent=t <= sticky):
        raise AssertionError("pad click while lift coasts must fire")

    # Long rest on the pad after the window: drop.
    while t < sticky + hid_hold + lift_on + 80:
        t += dt
        lift_ms, armed = step_lift(
            lift_ms,
            dt,
            det=False,
            coasting=False,
            recent=False,
            hid_moving=False,
            lift_on_ms=lift_on,
            sticky_ms=sticky,
            hid_hold_ms=hid_hold,
            since_ms=t,
        )
    if armed:
        raise AssertionError("lift must drop after sticky + hid-hold, not stick forever")


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
    src = proto_js()
    mode_body = _js_fn(src, "updateMode")
    hid = mode_body.find("if (S.hidMoving)")
    owns = mode_body.find("handOwns")
    if "LIFT_STICKY_MS" not in mode_body:
        raise AssertionError("updateMode must sticky-lift on a recent sample")
    if "holdClick" not in mode_body:
        raise AssertionError("HID click must hold lift, not demote it")
    if owns < 0 or hid < 0 or owns > hid:
        raise AssertionError("chip: hand / recent sample must beat trackpad HID")
    if "S.lifted" not in mode_body:
        raise AssertionError("updateMode must write lifted")
    if "want = S.forceGun || (!S.hidMoving" in mode_body:
        raise AssertionError("HID idle must not be required to charge lift")

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
    if "aimBus.fire" not in fire:
        raise AssertionError("fire must peek the AimBus mailbox")
    if "shot.lifted" not in fire:
        raise AssertionError("fire peeks AimSample.lifted from the bus")
    if "shot.uv" not in fire:
        raise AssertionError("fire peeks AimSample.uv from the bus")
    if "hitscanRange" not in fire:
        raise AssertionError("fire must ray-test the house sphere")
    if "intersectObjects" in fire:
        raise AssertionError("fire must not mesh-test the spun hex")
    if "LIFT_STICKY_MS" not in fire:
        raise AssertionError("fire must honor sticky / recent lift, not only S.lifted")
    if "coastTrack" in fire or "updateAim" in fire:
        raise AssertionError("fire must not coastTrack / updateAim — last committed sample only")
    if re.search(r"await\s+|requestVideoFrameCallback", fire):
        raise AssertionError("fire must not wait on a camera frame")
    if re.search(r"postMessage|createImageBitmap|detectForVideo|hands_worker", fire):
        raise AssertionError("fire must not wait on the Hands worker")

    move = re.search(r"pointermove[\s\S]{0,280}", src)
    if not move or "if (S.desktop)" not in move.group(0):
        raise AssertionError("OS pointer writes aim only in DESKTOP")

    if src.count("drawCrosshair(S.aim.x, S.aim.y)") < 2:
        raise AssertionError("calib + range must draw the reticle")
    if 'if (S.mode === "GUN" || S.mode === "DESKTOP" || S.mode === "SEEKING")' in src:
        raise AssertionError("PAD must not hide the reticle")


def test_pointing_filter() -> None:
    src = proto_js()
    m = re.search(r"EURO_MINCUTOFF = ([0-9.]+)", src)
    if not m or float(m.group(1)) < 2.5:
        raise AssertionError("One Euro mincutoff must be pointing-fast, not 1Hz soup")
    if "function adaptTpl" not in src:
        raise AssertionError("strong lock must refresh the template")
    if "function findHand" not in src:
        raise AssertionError("hand is the gun: findHand must exist")
    if "function mpTrack" not in src or "function initHands" not in src:
        raise AssertionError("MediaPipe Hands (landmark 8) must be the primary tracker")
    if "function maybePinchFire" not in src:
        raise AssertionError("pinch thumb-index must be able to fire")
    if "function fallbackSkin" not in src:
        raise AssertionError("if Hands dies, skin/NCC fallback must run")
    if "handsPromise" not in src:
        raise AssertionError("initHands must wait for the model, not return early")
    if "function indexExtended" not in src:
        raise AssertionError("muzzle requires an extended index, not a fist")
    if "new Worker" not in src or "hands_worker.js" not in src:
        raise AssertionError("HandLandmarker detect must run in a Worker")
    apply_lm = _js_fn(src, "applyMpLandmarks")
    if "applyEuroPoint" not in apply_lm:
        raise AssertionError("One Euro must run on UV after worker landmarks, before mailbox")
    mp = _js_fn(src, "mpTrack")
    if "kickAndFresh" not in mp and "kickWorkerDetect" not in mp:
        raise AssertionError("mpTrack must kick the worker, not detect on rAF")
    if "detectForVideo" in mp:
        raise AssertionError("mpTrack happy path must not call detectForVideo on main")
    for name in ("frame", "runTrack", "armVideoTrack"):
        body = _js_fn(src, name)
        if "detectForVideo" in body or "mpTrackMain" in body:
            raise AssertionError(f"{name} must not run HandLandmarker.detect on main")
    frame = _js_fn(src, "frame")
    if frame.find("updateMode") > frame.find("maybePinchFire"):
        raise AssertionError("pinch must run after updateMode so lifted is current")
    lost = _js_fn(src, "nccTrack")
    if "age > COAST_MS && S.euroX" in lost:
        raise AssertionError("do not kill euro/velocity at coast — only after QUALITY_LOST_MS")
    if "QUALITY_LOST_MS" not in lost:
        raise AssertionError("long hole resets filters, short hole coasts")
    mode_body = _js_fn(src, "updateMode")
    if "LIFT_ON_MS" not in mode_body and "S.liftMs" not in mode_body:
        raise AssertionError("lift needs hysteresis so HID noise does not flicker fire")


def test_range_gate() -> None:
    src = proto_js()
    fire_body = _js_fn(src, "fire")
    if "lifted" not in fire_body:
        raise AssertionError("Range fire must gate on AimSample.lifted")
    if "shot.lifted" not in fire_body:
        raise AssertionError("Range fire must peek mailbox lift, not only S.lifted")
    if "!S.desktop && !S.lifted" not in fire_body:
        raise AssertionError("Range fire must still consult S.lifted unless desktop")


def test_gallery_escape() -> None:
    """Sit plates and clays must be able to miss. Infinite free hits are dishonest."""
    src = proto_js()
    dwell = _js_const(src, "SIT_DWELL_S")
    drop = _js_const(src, "SIT_DROP_VY")
    max_life = _js_const(src, "PLATE_MAX_LIFE_S")
    if _js_const(src, "SIT_BOB_RATE") != 1.6:
        raise AssertionError("SIT_BOB_RATE drifted from the shared house")
    if _js_const(src, "SIT_BOB_AMP") != 0.07:
        raise AssertionError("SIT_BOB_AMP drifted from the shared house")
    if _js_const(src, "GRAVITY") != 4.6:
        raise AssertionError("GRAVITY drifted from the shared house")
    if dwell <= 0 or dwell > 8:
        raise AssertionError("sit plates need a short dwell, then escape")
    if drop >= 0:
        raise AssertionError("sit escape must drop, not rise")
    if max_life <= dwell:
        raise AssertionError("PLATE_MAX_LIFE_S must outlast sit dwell")
    sit = _js_fn(src, "sitPoseY")
    for needle in ("SIT_DWELL_S", "SIT_DROP_VY", "SIT_BOB_RATE", "SIT_BOB_AMP"):
        if needle not in sit:
            raise AssertionError(f"sitPoseY must own sit escape / bob ({needle})")
    body = _js_fn(src, "updateRange")
    if "sitPoseY" not in body:
        raise AssertionError("updateRange must use closed-form sitPoseY — not an unsynced phase")
    if "flyerPose" not in body:
        raise AssertionError("updateRange must use closed-form flyerPose — not Euler")
    if "o.vy -=" in body or "o.mesh.position.y +=" in body:
        raise AssertionError("updateRange Euler-integrated flyers — friends would split")
    if "o.phase" in body:
        raise AssertionError("updateRange must not accumulate a local sit phase")
    fly = _js_fn(src, "flyerPose")
    if "GRAVITY" not in fly or "0.5" not in fly:
        raise AssertionError("flyerPose must own closed-form gravity")
    for needle in ("PLATE_MAX_LIFE_S", '"ESC"'):
        if needle not in body:
            raise AssertionError(f"updateRange must escape plates ({needle})")
    y = 0.35
    life = 0.0
    dt = 1.0 / 60.0
    escaped = False
    while life < 10.0:
        life += dt
        if life >= dwell:
            y += drop * dt
            if y < -1.7 or life >= max_life:
                escaped = True
                break
    if not escaped:
        raise AssertionError("sit plate must be able to escape")
    if life > 8.5:
        raise AssertionError("sit escape window is too long for an honest gallery")


def test_native_sticky_constants() -> None:
    src = (ROOT / "native/cv_input/include/sable/constants.hpp").read_text(encoding="utf-8")
    if "kLiftStickyMs" not in src:
        raise AssertionError("native lift must sticky through a pad reach")
    if "kLiftHidHoldMs" not in src:
        raise AssertionError("native lift must hold through the HID click gesture")
    pipe = (ROOT / "native/cv_input/src/pipeline.cpp").read_text(encoding="utf-8")
    if "hid_idle_ && cam_lift" in pipe:
        raise AssertionError("native apply_lift must not require HID idle to own lift")
    tests = (ROOT / "native/cv_input/tests/test_aim.cpp").read_text(encoding="utf-8")
    if "test_pad_click_while_lift_coasts" not in tests:
        raise AssertionError("C++ suite must regress pad click while lift coasts")


def main() -> int:
    try:
        test_mode_table()
        test_lift_and_fire()
        test_pad_click_while_lift_coasts()
        test_ruled_out()
        test_proto_mailbox()
        test_pointing_filter()
        test_range_gate()
        test_gallery_escape()
        test_native_sticky_constants()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("aim verb ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
