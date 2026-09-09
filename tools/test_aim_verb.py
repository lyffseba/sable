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
    if "!S.seeking && (S.locked || S.desktop)" not in src:
        raise AssertionError("publishAim valid must stay !seeking && (locked || desktop)")
    if "S.lifted" not in _js_fn(src, "publishAim"):
        raise AssertionError("publishAim must publish S.lifted — do not invent a sixth field")
    if 'S.seeking = false' not in mode_body or "S.lifted = true" not in mode_body:
        raise AssertionError("updateMode DESKTOP must clear seeking and arm lifted")

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
    if "enableCamera" in fire or "armPracticeCam" in fire or "armPracticeDesktop" in fire or "getUserMedia" in fire:
        raise AssertionError("fire must not wait on camera arm")
    if re.search(r"postMessage|createImageBitmap|detectForVideo|hands_worker", fire):
        raise AssertionError("fire must not wait on the Hands worker")
    intersect = fire.find("hitscanRange(")
    mark_range = fire.find("SablePerf.markHid", intersect) if intersect >= 0 else -1
    if intersect < 0 or mark_range < 0:
        raise AssertionError("fire must mark HID→hitscan at the house sphere")
    probe = fire[intersect:mark_range]
    if "applyGunKick" in probe or "peekMuzzleWorld" in probe or "getWorldPosition" in probe:
        raise AssertionError("Look (gun kick / muzzle world) is not a fire gate")
    if "applyGunKick" not in fire or "peekMuzzleWorld" not in fire:
        raise AssertionError("gun kick / muzzle world must stay Look after the sphere")

    if 'canvasHUD.addEventListener("pointerdown"' in src:
        raise AssertionError("HID click must not live on muted #hud — window owns the peek")
    if "function onHidPointerDown" not in src or "hidChromeTarget" not in src:
        raise AssertionError("HID pointerdown must live on window and spare chrome")
    if 'window.addEventListener("pointerdown", onHidPointerDown)' not in src:
        raise AssertionError("HID click must bind window — Fire is HID")
    hid = _js_fn(src, "onHidPointerDown")
    if "if (S.desktop) publishAim(e.clientX, e.clientY)" not in hid:
        raise AssertionError("DESKTOP HID must publish click UV before fire() peek")
    if hid.find("publishAim") > hid.find("fire()"):
        raise AssertionError("DESKTOP publishAim must land before fire()")
    if "updateAim" in hid or "coastTrack" in hid:
        raise AssertionError("window HID must not recompute aim — fire() peeks")
    for m in re.finditer(r"publishAim\s*\(", hid):
        window = hid[max(0, m.start() - 80) : m.start()]
        if "S.desktop" not in window:
            raise AssertionError("HID must not publishAim unless DESKTOP owns the mailbox")
    if "publishAim" in _js_fn(src, "fire"):
        raise AssertionError("fire() must peek — DESKTOP publish lives on onHidPointerDown")
    chrome = _js_fn(src, "hidChromeTarget")
    if "join-mute" not in chrome or "lobby-join" not in chrome:
        raise AssertionError("leftover JOIN/CODE must not mute waiting-Yard HID")
    if "muteJoinPad()" not in _js_fn(src, "lobbyJoin"):
        raise AssertionError("JOIN must release leftover CODE/JOIN so the pad peeks")

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
    pinch = _js_fn(src, "maybePinchFire")
    if "fire()" not in pinch:
        raise AssertionError("pinch must peek through fire()")
    if "updateAim(" in pinch or "publishAim(" in pinch:
        raise AssertionError("pinch must not rewrite aim — peek last pointing UV")
    if 'phase === "range"' in pinch or 'phase === "bay"' in pinch:
        raise AssertionError("maybePinchFire must not re-gate the verb — fire() owns the phase lock")
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
    if frame.find("maybePinchFire") > frame.find("updateAim"):
        raise AssertionError("pinch must peek last pointing UV — updateAim after the trigger must not rewrite the shot")
    desk_else = re.search(r"else if \(S\.desktop\) \{([\s\S]*?)\n  \}", frame)
    if not desk_else or "updateMode" not in desk_else.group(1):
        raise AssertionError("frame must run updateMode on DESKTOP even if !camReady")
    if "maybePinchFire" in desk_else.group(1) or "updateAim" in desk_else.group(1):
        raise AssertionError("!camReady DESKTOP must not pinch or rewrite aim")
    if "runTrack" in desk_else.group(1) or "grabFrame" in desk_else.group(1):
        raise AssertionError("!camReady DESKTOP must not invent a hand track")
    if frame.find("if (camReady)") > frame.find("else if (S.desktop)"):
        raise AssertionError("camReady track/pinch path must stay first — do not reorder GUN")
    lost = _js_fn(src, "nccTrack")
    if "age > COAST_MS && S.euroX" in lost:
        raise AssertionError("do not kill euro/velocity at coast — only after QUALITY_LOST_MS")
    if "QUALITY_LOST_MS" not in lost:
        raise AssertionError("long hole resets filters, short hole coasts")
    mode_body = _js_fn(src, "updateMode")
    if "LIFT_ON_MS" not in mode_body and "S.liftMs" not in mode_body:
        raise AssertionError("lift needs hysteresis so HID noise does not flicker fire")


def test_desktop_arm_writes_updatemode_truth() -> None:
    """Cam-deny / KeyT / goDesktopRange must match DESKTOP updateMode immediately."""
    src = proto_js()
    desk = _js_fn(src, "armPracticeDesktop")
    if "if (camReady) return" not in desk:
        raise AssertionError("armPracticeDesktop must refuse a live camera")
    if "updateMode(" not in desk:
        raise AssertionError("armPracticeDesktop must write updateMode truth before the next frame")
    if desk.find("if (camReady) return") > desk.find("updateMode("):
        raise AssertionError("armPracticeDesktop must not steal camReady before writing truth")
    if "aimBus" in desk or "fire(" in desk or "publishAim" in desk:
        raise AssertionError("desktop arm must not publish or fire — HID peeks")
    go = _js_fn(src, "goDesktopRange")
    if "updateMode(" not in go:
        raise AssertionError("goDesktopRange must write updateMode truth before enterGame")
    if go.find("updateMode") > go.find("enterGame"):
        raise AssertionError("goDesktopRange must arm DESKTOP truth before enterGame")
    keys = src[src.find('addEventListener("keydown"') : src.find('addEventListener("keyup"')]
    t_block = re.search(
        r'if \(e\.code === "KeyT"\) \{([\s\S]*?)\n  if \(e\.code === "KeyW"\)',
        keys,
    )
    if not t_block:
        raise AssertionError("KeyT handler missing")
    t_body = t_block.group(1)
    if "updateMode(" not in t_body:
        raise AssertionError("KeyT DESKTOP must write updateMode truth immediately")
    if 'phase === "lock"' not in t_body or "goDesktopRange()" not in t_body:
        raise AssertionError("Offline lock-phase KeyT must stay goDesktopRange")
    if "armPracticeDesktop()" not in t_body:
        raise AssertionError("KeyT must re-arm DESKTOP on cam-deny waiting Yard")
    if "camReady" not in t_body:
        raise AssertionError("KeyT re-arm must refuse to steal a live camera")
    if 'phase === "lobby"' not in t_body or "wait_practice" not in t_body:
        raise AssertionError("KeyT re-arm is waiting Yard only — lobby / wait_practice")
    if "S.desktop = !S.desktop" not in t_body:
        raise AssertionError("KeyT must still toggle DESKTOP when camReady")
    if t_body.find("armPracticeDesktop()") > t_body.find("S.desktop = !S.desktop"):
        raise AssertionError("KeyT must re-arm / no-op before toggle-off on cam-deny")
    if t_body.find("goDesktopRange()") > t_body.find("S.desktop = !S.desktop"):
        raise AssertionError("waiting-Yard KeyT must not dump through goDesktopRange")
    hid = _js_fn(src, "onHidPointerDown")
    if "if (S.desktop) publishAim(e.clientX, e.clientY)" not in hid:
        raise AssertionError("#76: DESKTOP HID must still publish click UV before fire()")


def test_desktop_shows_os_cursor() -> None:
    """DESKTOP aim is the OS cursor. Hide only when the hand owns the pad."""
    src = proto_js()
    sync = _js_fn(src, "syncCursor")
    if "!S.desktop" not in sync:
        raise AssertionError("syncCursor must show the OS cursor when S.desktop")
    if 'phase === "lock"' not in sync or "nocursor" not in sync:
        raise AssertionError("lock-never-cursor: non-DESKTOP live phases still hide")
    for phase in ("range", "bay", "lobby", "calibrate", "lock"):
        if f'phase === "{phase}"' not in sync:
            raise AssertionError(f"syncCursor must still name {phase} for lock-never-cursor")
    if "S.desktop = true" in sync or "armPracticeDesktop" in sync or "goDesktopRange" in sync:
        raise AssertionError("syncCursor must not arm DESKTOP — Q4 never auto-desktop")
    if "aimBus" in sync or "fire(" in sync or "publishAim" in sync:
        raise AssertionError("syncCursor must not publish or fire — HID peeks")
    if "AimSample" in sync:
        raise AssertionError("syncCursor must not touch AimSample")
    hid = _js_fn(src, "onHidPointerDown")
    if "if (S.desktop) publishAim(e.clientX, e.clientY)" not in hid:
        raise AssertionError("#76: DESKTOP HID must still publish click UV before fire()")
    desk = _js_fn(src, "armPracticeDesktop")
    if "updateMode(" not in desk:
        raise AssertionError("#77: armPracticeDesktop must still write updateMode truth")
    keys = src[src.find('addEventListener("keydown"') : src.find('addEventListener("keyup"')]
    t_block = re.search(
        r'if \(e\.code === "KeyT"\) \{([\s\S]*?)\n  if \(e\.code === "KeyW"\)',
        keys,
    )
    if not t_block or "armPracticeDesktop()" not in t_block.group(1):
        raise AssertionError("#78: KeyT must still re-arm DESKTOP on cam-deny waiting Yard")


def test_desktop_skips_mint_crosshair() -> None:
    """DESKTOP aim is the OS cursor. Do not stack the mint reticle."""
    src = proto_js()
    d2 = _js_fn(src, "draw2D")
    for m in re.finditer(r"drawCrosshair\s*\(", d2):
        window = d2[max(0, m.start() - 80) : m.start()]
        if "S.desktop" not in window:
            raise AssertionError("draw2D must skip drawCrosshair when S.desktop")
    if d2.count("drawCrosshair") < 2:
        raise AssertionError("non-DESKTOP live phases must still paint the mint reticle")
    for phase in ("range", "bay", "lobby", "calibrate", "lock"):
        if f'phase === "{phase}"' not in d2:
            raise AssertionError(f"draw2D must still name {phase} for the mint tell")
    if "S.desktop = true" in d2 or "armPracticeDesktop" in d2 or "goDesktopRange" in d2:
        raise AssertionError("draw2D must not arm DESKTOP — Q4 never auto-desktop")
    if "aimBus" in d2 or "fire(" in d2 or "publishAim" in d2:
        raise AssertionError("draw2D must not publish or fire — HID peeks")
    if "AimSample" in d2:
        raise AssertionError("draw2D must not touch AimSample")
    sync = _js_fn(src, "syncCursor")
    if "!S.desktop" not in sync:
        raise AssertionError("#79: syncCursor must still show the OS cursor when S.desktop")
    hid = _js_fn(src, "onHidPointerDown")
    if "if (S.desktop) publishAim(e.clientX, e.clientY)" not in hid:
        raise AssertionError("#76: DESKTOP HID must still publish click UV before fire()")
    desk = _js_fn(src, "armPracticeDesktop")
    if "updateMode(" not in desk:
        raise AssertionError("#77: armPracticeDesktop must still write updateMode truth")
    keys = src[src.find('addEventListener("keydown"') : src.find('addEventListener("keyup"')]
    t_block = re.search(
        r'if \(e\.code === "KeyT"\) \{([\s\S]*?)\n  if \(e\.code === "KeyW"\)',
        keys,
    )
    if not t_block or "armPracticeDesktop()" not in t_block.group(1):
        raise AssertionError("#78: KeyT must still re-arm DESKTOP on cam-deny waiting Yard")


def test_desktop_publishes_confidence_one() -> None:
    """DESKTOP AimSample.confidence is 1. Leftover tracker quality must not lie."""
    src = proto_js()
    pub = _js_fn(src, "publishAim")
    if "S.desktop ? 1" not in pub:
        raise AssertionError("publishAim must write confidence 1 when S.desktop")
    if "S.quality / 100" not in pub:
        raise AssertionError("non-DESKTOP publishAim must still use S.quality")
    if "clamp(S.quality / 100, 0, 1)" in pub and "S.desktop ? 1" not in pub:
        raise AssertionError("publishAim must not always write leftover tracker quality")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", src)
    if not sample:
        raise AssertionError("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        raise AssertionError("AimSample must stay five fields — do not invent a sixth")
    if "new AimSample" not in pub or "aimBus.publish" not in pub:
        raise AssertionError("publishAim must still publish one five-field AimSample")
    if "S.desktop = true" in pub or "armPracticeDesktop" in pub or "goDesktopRange" in pub:
        raise AssertionError("publishAim must not arm DESKTOP — Q4 never auto-desktop")
    chip = src[src.find("function drawModeChip") : src.find("function drawModeChip") + 1400]
    if "S.desktop ? 100" not in chip:
        raise AssertionError("drawModeChip must paint CONF 100 when S.desktop")
    if "S.quality" not in chip:
        raise AssertionError("non-DESKTOP cuff must still paint S.quality")
    if "S.desktop = true" in chip or "armPracticeDesktop" in chip:
        raise AssertionError("drawModeChip must not arm DESKTOP — Q4 never auto-desktop")
    d2 = _js_fn(src, "draw2D")
    for m in re.finditer(r"drawCrosshair\s*\(", d2):
        window = d2[max(0, m.start() - 80) : m.start()]
        if "S.desktop" not in window:
            raise AssertionError("#80: draw2D must still skip drawCrosshair when S.desktop")
    sync = _js_fn(src, "syncCursor")
    if "!S.desktop" not in sync:
        raise AssertionError("#79: syncCursor must still show the OS cursor when S.desktop")
    hid = _js_fn(src, "onHidPointerDown")
    if "if (S.desktop) publishAim(e.clientX, e.clientY)" not in hid:
        raise AssertionError("#76: DESKTOP HID must still publish click UV before fire()")
    desk = _js_fn(src, "armPracticeDesktop")
    if "updateMode(" not in desk:
        raise AssertionError("#77: armPracticeDesktop must still write updateMode truth")
    keys = src[src.find('addEventListener("keydown"') : src.find('addEventListener("keyup"')]
    t_block = re.search(
        r'if \(e\.code === "KeyT"\) \{([\s\S]*?)\n  if \(e\.code === "KeyW"\)',
        keys,
    )
    if not t_block or "armPracticeDesktop()" not in t_block.group(1):
        raise AssertionError("#78: KeyT must still re-arm DESKTOP on cam-deny waiting Yard")


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
    if "commitSharedPlateLife" not in body:
        raise AssertionError("updateRange must rewind match_live life — not o.life += dt")
    if "o.life += dt" not in body:
        raise AssertionError("Offline / WARM UP must still integrate life locally")
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
        test_desktop_arm_writes_updatemode_truth()
        test_desktop_shows_os_cursor()
        test_desktop_skips_mint_crosshair()
        test_desktop_publishes_confidence_one()
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
