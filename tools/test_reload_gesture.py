#!/usr/bin/env python3
"""Index+middle ceiling is product reload on the hand / GUN path.

Fail loud if the rising edge no longer refills, if shark-fin false-reloads,
if reload false-fires shark-fin, if empty mag silent-fires, if AimSample
grows a sixth field, if DESKTOP is forced onto reload, if the gesture
rewrites shot UV / re-gates the waiting Yard, or if pinch still peeks fire().
"""

from __future__ import annotations

import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402

MAG_CAP = 6


def _fail(msg: str) -> None:
    raise AssertionError(f"RELOAD FAIL: {msg}")


def _fn(src: str, name: str) -> str:
    m = re.search(rf"(?:async )?function {name}\s*\(", src)
    if not m:
        _fail(f"missing function {name}")
    start = src.find("{", m.end() - 1)
    if start < 0:
        _fail(f"function {name} has no body")
    depth = 0
    i = start
    while i < len(src):
        ch = src[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[m.start() : i + 1]
        i += 1
    _fail(f"function {name} is unclosed")
    raise AssertionError("unreachable")


def palm_scale(lm: dict[int, tuple[float, float]]) -> float:
    wrist, palm = lm.get(0), lm.get(9)
    if not wrist or not palm:
        return 0.2
    return max(0.08, math.hypot(wrist[0] - palm[0], wrist[1] - palm[1]))


def index_extended(lm: dict[int, tuple[float, float]]) -> bool:
    w, pip, tip = lm.get(0), lm.get(6), lm.get(8)
    if not w or not pip or not tip:
        return False
    d_tip = math.hypot(tip[0] - w[0], tip[1] - w[1])
    d_pip = math.hypot(pip[0] - w[0], pip[1] - w[1])
    return d_tip > d_pip * 1.06


def thumb_extended(lm: dict[int, tuple[float, float]]) -> bool:
    w, ip, tip = lm.get(0), lm.get(3), lm.get(4)
    if not w or not ip or not tip:
        return False
    d_tip = math.hypot(tip[0] - w[0], tip[1] - w[1])
    d_ip = math.hypot(ip[0] - w[0], ip[1] - w[1])
    return d_tip > d_ip * 1.04


def dist_point_to_seg(
    px: float, py: float, ax: float, ay: float, bx: float, by: float
) -> float:
    abx, aby = bx - ax, by - ay
    apx, apy = px - ax, py - ay
    ab2 = abx * abx + aby * aby
    t = 0.0 if ab2 < 1e-8 else max(0.0, min(1.0, (apx * abx + apy * aby) / ab2))
    return math.hypot(apx - abx * t, apy - aby * t)


def pinch_strength(lm: dict[int, tuple[float, float]]) -> float:
    thumb, index, wrist, palm = lm.get(4), lm.get(8), lm.get(0), lm.get(9)
    if not thumb or not index:
        return 0.0
    scale = (
        math.hypot(wrist[0] - palm[0], wrist[1] - palm[1]) if wrist and palm else 0.2
    )
    d = math.hypot(thumb[0] - index[0], thumb[1] - index[1]) / max(0.08, scale)
    return max(0.0, min(1.0, 1.0 - (d - 0.28) / 0.4))


def thumb_parallel(lm: dict[int, tuple[float, float]]) -> bool:
    tip, idx_mcp, idx_tip = lm.get(4), lm.get(5), lm.get(8)
    if not tip or not idx_mcp or not idx_tip:
        return True
    off = dist_point_to_seg(
        tip[0], tip[1], idx_mcp[0], idx_mcp[1], idx_tip[0], idx_tip[1]
    ) / palm_scale(lm)
    return off < 0.55


def finger_ceiling(
    lm: dict[int, tuple[float, float]], mcp_i: int, pip_i: int, tip_i: int
) -> bool:
    w, pip, tip, mcp = lm.get(0), lm.get(pip_i), lm.get(tip_i), lm.get(mcp_i)
    if not w or not pip or not tip or not mcp:
        return False
    d_tip = math.hypot(tip[0] - w[0], tip[1] - w[1])
    d_pip = math.hypot(pip[0] - w[0], pip[1] - w[1])
    if d_tip <= d_pip * 1.06:
        return False
    if tip[1] >= mcp[1] - 0.02:
        return False
    dx = tip[0] - mcp[0]
    dy = mcp[1] - tip[1]
    if dy <= abs(dx) * 0.85:
        return False
    return True


def charger_plug(lm: dict[int, tuple[float, float]] | None) -> bool:
    if not lm:
        return False
    return finger_ceiling(lm, 5, 6, 8) and finger_ceiling(lm, 9, 10, 12)


def shark_fin(lm: dict[int, tuple[float, float]] | None) -> bool:
    if not lm or not index_extended(lm) or not thumb_extended(lm):
        return False
    tip, mcp = lm.get(4), lm.get(2)
    if not tip or not mcp:
        return False
    if thumb_parallel(lm):
        return False
    if tip[1] >= mcp[1] - 0.02:
        return False
    if pinch_strength(lm) > 0.48:
        return False
    if charger_plug(lm):
        return False
    return True


def reload_gesture(lm: dict[int, tuple[float, float]] | None) -> bool:
    if not charger_plug(lm):
        return False
    if shark_fin(lm):
        return False
    return True


def gun_shark() -> dict[int, tuple[float, float]]:
    """Finger-gun, thumb up like a shark fin. Index points at the glass."""
    return {
        0: (0.50, 0.82),
        2: (0.36, 0.64),
        3: (0.34, 0.50),
        4: (0.33, 0.34),
        5: (0.58, 0.62),
        6: (0.68, 0.56),
        8: (0.80, 0.50),
        9: (0.54, 0.66),
        12: (0.62, 0.58),
    }


def gun_parallel() -> dict[int, tuple[float, float]]:
    """Same gun, thumb lies along the index — safe, no fire."""
    return {
        0: (0.50, 0.82),
        2: (0.52, 0.70),
        3: (0.62, 0.62),
        4: (0.72, 0.54),
        5: (0.58, 0.62),
        6: (0.68, 0.56),
        8: (0.80, 0.50),
        9: (0.54, 0.66),
        12: (0.62, 0.58),
    }


def charger_reload() -> dict[int, tuple[float, float]]:
    """Index + middle up at the ceiling — charger-plug / insert-mag."""
    return {
        0: (0.50, 0.85),
        2: (0.36, 0.78),
        3: (0.32, 0.80),
        4: (0.28, 0.82),
        5: (0.42, 0.70),
        6: (0.41, 0.52),
        8: (0.40, 0.28),
        9: (0.52, 0.68),
        10: (0.53, 0.50),
        12: (0.54, 0.26),
    }


def one_finger_up() -> dict[int, tuple[float, float]]:
    """Index ceiling, middle curled — not a two-finger reload."""
    pose = charger_reload()
    pose[10] = (0.54, 0.70)
    pose[12] = (0.55, 0.74)
    return pose


def maybe_reload_edge(held: bool, pose: bool, mag: int) -> tuple[bool, int, bool]:
    """Rising edge only. Held continuous is not auto-refill."""
    reloaded = False
    if pose and not held:
        held = True
        mag = MAG_CAP
        reloaded = True
    elif not pose:
        held = False
    return held, mag, reloaded


def spend_gesture_round(mag: int, fin_held: bool) -> tuple[int, bool]:
    """Hand-path mag only. HID / DESKTOP / pinch do not invent a mag story."""
    if not fin_held:
        return mag, True
    if mag <= 0:
        return mag, False
    return mag - 1, True


def test_geometry_table() -> None:
    plug = charger_reload()
    fin = gun_shark()
    safe = gun_parallel()
    one = one_finger_up()
    if not finger_ceiling(plug, 5, 6, 8) or not finger_ceiling(plug, 9, 10, 12):
        _fail("charger-plug fixture must point index+middle at the ceiling")
    if not charger_plug(plug) or not reload_gesture(plug):
        _fail("index+middle ceiling must be product reload")
    if shark_fin(plug):
        _fail("charger-plug must not false-fire shark-fin")
    if reload_gesture(fin) or charger_plug(fin):
        _fail("shark-fin must not false-reload")
    if not shark_fin(fin):
        _fail("shark-fin fixture must stay product fire")
    if reload_gesture(safe) or shark_fin(safe):
        _fail("thumb-parallel finger-gun is not reload and not fire")
    if reload_gesture(one) or charger_plug(one):
        _fail("one finger up is not the charger-plug")
    if reload_gesture(None) or charger_plug(None):
        _fail("missing landmarks must not invent a reload")


def test_rising_edge_refills() -> None:
    held, mag, reloaded = maybe_reload_edge(False, True, 2)
    if not reloaded or not held or mag != MAG_CAP:
        _fail("reload rising edge must refill once")
    held, mag, reloaded = maybe_reload_edge(held, True, mag)
    if reloaded:
        _fail("held charger-plug must not auto-refill")
    held, mag, reloaded = maybe_reload_edge(held, False, mag)
    if reloaded or held:
        _fail("drop must reset the reload edge")
    held, mag, reloaded = maybe_reload_edge(held, True, 1)
    if not reloaded or mag != MAG_CAP:
        _fail("a second rising edge after drop must refill again")


def test_empty_mag_cannot_silent_fire() -> None:
    mag, shot = spend_gesture_round(0, True)
    if shot or mag != 0:
        _fail("empty mag cannot silent-fire on shark-fin")
    mag, shot = spend_gesture_round(0, False)
    if not shot:
        _fail("pinch / HID / DESKTOP must not invent a mag brick")
    held, mag, reloaded = maybe_reload_edge(False, True, 0)
    if not reloaded or mag != MAG_CAP:
        _fail("rising-edge reload must refill an empty mag")
    mag, shot = spend_gesture_round(mag, True)
    if not shot or mag != MAG_CAP - 1:
        _fail("after reload, shark-fin must spend a round")
    for _ in range(MAG_CAP - 1):
        mag, shot = spend_gesture_round(mag, True)
        if not shot:
            _fail("loaded mag must still fire")
    mag, shot = spend_gesture_round(mag, True)
    if shot or mag != 0:
        _fail("sixth spent round must dry-click — not a seventh silent hit")


def test_client_peek_and_order() -> None:
    src = proto_js()
    if "function reloadGesture" not in src or "function maybeReloadGesture" not in src:
        _fail("hand path must detect charger-plug from MediaPipe landmarks")
    if "function chargerPlug" not in src or "function fingerCeiling" not in src:
        _fail("reload must name the ceiling-finger helpers")
    pose = _fn(src, "reloadGesture")
    if "chargerPlug" not in pose:
        _fail("reloadGesture must require index+middle ceiling")
    if "sharkFin" not in pose:
        _fail("reloadGesture must refuse shark-fin — poses stay exclusive")
    if "AimSample" in pose or "publishAim" in pose or "updateAim" in pose:
        _fail("reloadGesture must not touch the mailbox — five fields stay")
    if "fire()" in pose:
        _fail("reload pose test must not fire")
    fin_fn = _fn(src, "sharkFin")
    if "chargerPlug" not in fin_fn:
        _fail("sharkFin must refuse charger-plug — do not false-fire reload")
    trig = _fn(src, "maybeReloadGesture")
    if "refillMag" not in trig and "S.mag" not in trig:
        _fail("rising-edge reload must refill the mag")
    if "fire()" in trig:
        _fail("reload must not peek fire() — that would shoot")
    if "updateAim(" in trig or "publishAim(" in trig:
        _fail("reload rewrites aim — gesture must not touch shot UV")
    if 'phase === "range"' in trig or 'phase === "bay"' in trig:
        _fail("maybeReloadGesture re-gates the verb — waiting Yard would mute")
    if "S.desktop" not in trig:
        _fail("reload must no-op when DESKTOP owns the pad fallback")
    if "S.reloadHeld" not in trig:
        _fail("reload must rising-edge, not held auto-refill")
    if "function maybePinchFire" in src or "maybePinchFire(" in src:
        _fail("pinch must not peek -- maybePinchFire is retired")
    if "pinchHeld" in src:
        _fail("S.pinchHeld died with the pinch verb")
    frame = _fn(src, "frame")
    if frame.find("updateMode") > frame.find("maybeSharkFinFire"):
        _fail("shark-fin ran before updateMode -- lift would be stale")
    if "maybePinchFire" in frame:
        _fail("frame must not run pinch -- pinch is not a trigger")
    if frame.find("maybeSharkFinFire") > frame.find("maybeReloadGesture"):
        _fail("shark-fin must run before reload -- product shoot first")
    if frame.find("maybeReloadGesture") > frame.find("updateAim"):
        _fail("reload published gesture UV before the peek")
    if frame.find("maybeSharkFinFire") > frame.find("updateAim"):
        _fail("shark-fin published gesture UV before the peek")
    desk_else = re.search(r"else if \(S\.desktop\) \{([\s\S]*?)\n  \}", frame)
    if not desk_else or "updateMode" not in desk_else.group(1):
        _fail("frame must run updateMode on DESKTOP even if !camReady")
    desk = desk_else.group(1)
    if "maybeReloadGesture" in desk or "maybeSharkFinFire" in desk or "maybePinchFire" in desk:
        _fail("!camReady DESKTOP must not reload — HID is the pad fallback")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", src)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample must stay five fields — do not invent a sixth")
    if "reloadHeld: false" not in src:
        _fail("reload hold lives on S, not on AimSample")
    if "mag:" not in src and "mag =" not in src:
        _fail("tiny mag honesty lives on S, not on AimSample")
    fire = _fn(src, "fire")
    if "spendGestureRound" not in fire:
        _fail("fire() must spend a hand-path round or dry-click")
    if "missTick" not in fire:
        _fail("empty mag must reuse dry-tick miss audio")
    spend = _fn(src, "spendGestureRound")
    if "S.finHeld" not in spend:
        _fail("mag spend is the shark-fin path -- not HID / DESKTOP")
    if "S.pinchHeld" in spend or "pinchHeld" in spend:
        _fail("pinch must not spend mag -- pinch is not a trigger")
    if "S.desktop" in spend:
        _fail("spendGestureRound must not invent a DESKTOP mag story")
    chip = _fn(src, "drawModeChip")
    if "MAG " not in chip or '"DRY"' not in chip:
        _fail("MAG chip missing on hand/GUN path")
    mag_gate = re.search(r"if\s*\(\s*!S\.desktop\s*\)\s*\{([\s\S]+)", chip)
    if not mag_gate or "MAG " not in mag_gate.group(1) or '"DRY"' not in mag_gate.group(1):
        _fail("MAG chip shows under DESKTOP — HID does not own mag")
    if "fillRect(mx, 16," not in chip and "fillRect(mx,16," not in chip:
        _fail("MAG chip left the 22px MODE row")
    hangar = _fn(src, "hangarHudChip")
    if "MAG " in hangar or '"DRY"' in hangar:
        _fail("hangar bar invented MAG — do not thicken lobby")


def test_hid_desktop_fallback_stays() -> None:
    src = proto_js()
    hid = _fn(src, "onHidPointerDown")
    if "if (S.desktop || S.forceGun) publishAim(e.clientX, e.clientY)" not in hid:
        _fail("DESKTOP HID must still publish click UV before fire() peek")
    if "fire()" not in hid:
        _fail("DESKTOP / pad fallback must still peek through fire()")
    if "maybeReloadGesture" in hid or "refillMag" in hid:
        _fail("HID click must not invent reload — camera owns the gesture")
    keys = src[src.find('addEventListener("keydown"') : src.find('addEventListener("keyup"')]
    space = re.search(r'if \(e\.code === "Space"\) \{([^}]+)\}', keys)
    if not space or "S.forceGun = true" not in space.group(1):
        _fail("Space must stay the Q4 forceGun escape")
    if "maybeReloadGesture" in space.group(1) or "refillMag" in space.group(1):
        _fail("Space forceGun must not invent reload")
    fire = _fn(src, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if "coastTrack" in fire or "updateAim" in fire:
        _fail("fire() recomputes aim")


def test_docs_lock() -> None:
    prod = (ROOT / "docs/PRODUCTION.md").read_text(encoding="utf-8")
    pipe = (ROOT / "docs/aim_pipeline.md").read_text(encoding="utf-8")
    track = (ROOT / "research/TRACKING.md").read_text(encoding="utf-8")
    if "maybeReloadGesture" not in prod:
        _fail("PRODUCTION.md must name maybeReloadGesture as this cut")
    if "charger-plug" not in prod.lower() and "index+middle" not in prod.lower():
        _fail("PRODUCTION.md must lock index+middle ceiling as product reload")
    if "maybeReloadGesture" not in pipe:
        _fail("aim_pipeline.md must name maybeReloadGesture as this cut")
    if "maybeReloadGesture" not in track:
        _fail("TRACKING.md must name maybeReloadGesture as this cut")
    if "out of scope" in track.lower() and "reload" in track.lower():
        _fail("TRACKING.md must not still claim reload is out of scope")
    if "Juan LOCK" not in track or "PRODUCT.md" not in track:
        _fail("TRACKING.md must keep the #85 Juan lock and PRODUCT.md pointer")
    if "AimSample" not in track or "t_hw" not in track:
        _fail("TRACKING.md must keep the five-field AimSample pointer")
    if "mag tell = reload honesty" not in prod.lower() and "Mag tell = reload honesty" not in prod:
        _fail("PRODUCTION.md must lock mag tell = reload honesty")
    if "do not invent a pad mag story" not in prod.lower():
        _fail("PRODUCTION.md must refuse a DESKTOP / forceGun pad mag story")
    if "empty shark-fin stays" not in prod.lower():
        _fail("PRODUCTION.md must keep empty shark-fin on missTick")
    if "mag tell = reload honesty" not in pipe.lower() and "Mag tell = reload honesty" not in pipe:
        _fail("aim_pipeline.md must lock mag tell = reload honesty")
    if "do not invent a pad mag story" not in pipe.lower():
        _fail("aim_pipeline.md must refuse a DESKTOP / forceGun pad mag story")
    if "empty shark-fin stays missTick" not in pipe.lower() and "Empty shark-fin stays missTick" not in pipe:
        _fail("aim_pipeline.md must keep empty shark-fin on missTick")
    if "mag tell = reload honesty" not in track.lower() and "Mag tell = reload honesty" not in track:
        _fail("TRACKING.md must lock mag tell = reload honesty")
    if "do not invent a pad mag story" not in track.lower():
        _fail("TRACKING.md must refuse a DESKTOP / forceGun pad mag story")
    if "empty shark-fin stays missTick" not in track.lower() and "Empty shark-fin stays missTick" not in track:
        _fail("TRACKING.md must keep empty shark-fin on missTick")
    product = (ROOT / "research/PRODUCT.md").read_text(encoding="utf-8")
    if "Index + middle up toward ceiling" not in product:
        _fail("PRODUCT.md must keep the Juan RELOAD lock")
    if "Thumb up like a shark fin" not in product:
        _fail("PRODUCT.md must keep the Juan SHOOT = shark-fin lock")
    ci = (ROOT / "tools/ci.sh").read_text(encoding="utf-8")
    if "test_reload_gesture.py" not in ci:
        _fail("ci.sh must run the reload gesture contract")
    if "test_shark_fin.py" not in ci:
        _fail("ci.sh must still run the shark-fin contract")


def main() -> int:
    try:
        test_geometry_table()
        test_rising_edge_refills()
        test_empty_mag_cannot_silent_fire()
        test_client_peek_and_order()
        test_hid_desktop_fallback_stays()
        test_docs_lock()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("reload gesture contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
