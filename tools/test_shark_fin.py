#!/usr/bin/env python3
"""Shark-fin thumb-up is product shoot on the hand / GUN path.

Fail loud if the rising edge no longer peeks fire(), if thumb-parallel
fires, if AimSample grows a sixth field, if DESKTOP is forced onto
shark-fin, if Space forceGun becomes product shoot, or if the gesture
rewrites shot UV / re-gates the waiting Yard.
"""

from __future__ import annotations

import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402


def _fail(msg: str) -> None:
    raise AssertionError(f"SHARK-FIN FAIL: {msg}")


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


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        _fail(f"missing function {name}")
    return m.group(0)


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


def gun_pinch() -> dict[int, tuple[float, float]]:
    """Thumb near index tip — interim pinch, not product shark-fin."""
    return {
        0: (0.50, 0.82),
        2: (0.60, 0.64),
        3: (0.70, 0.56),
        4: (0.78, 0.51),
        5: (0.58, 0.62),
        6: (0.68, 0.56),
        8: (0.80, 0.50),
        9: (0.54, 0.66),
        12: (0.62, 0.58),
    }


def maybe_fin_edge(held: bool, fin: bool) -> tuple[bool, bool]:
    """Rising edge only. Held continuous is not auto-fire."""
    fired = False
    if fin and not held:
        held = True
        fired = True
    elif not fin:
        held = False
    return held, fired


def test_geometry_table() -> None:
    fin = gun_shark()
    safe = gun_parallel()
    pinch = gun_pinch()
    if not index_extended(fin) or not thumb_extended(fin):
        _fail("shark-fin fixture must be an extended finger-gun")
    if not shark_fin(fin):
        _fail("thumb-up shark-fin must be product fire")
    if shark_fin(safe):
        _fail("thumb parallel to other fingers must be safe — no fire")
    if not thumb_parallel(safe):
        _fail("parallel fixture must lie along the barrel")
    if shark_fin(pinch):
        _fail("pinch must not also be shark-fin — that double-fires")
    if pinch_strength(pinch) <= 0.48:
        _fail("pinch fixture must be a real pinch so the reject is honest")
    if shark_fin(None):
        _fail("missing landmarks must not invent a shark-fin")
    fist = dict(fin)
    fist[6] = (0.56, 0.68)
    fist[8] = (0.52, 0.78)
    if index_extended(fist) or shark_fin(fist):
        _fail("a fist is not GUN — index must stay extended")


def test_rising_edge_not_auto() -> None:
    held, fired = maybe_fin_edge(False, True)
    if not fired or not held:
        _fail("shark-fin rising edge must fire once")
    held, fired = maybe_fin_edge(held, True)
    if fired:
        _fail("held shark-fin must not auto-fire")
    held, fired = maybe_fin_edge(held, False)
    if fired or held:
        _fail("parallel / drop must reset the edge")
    held, fired = maybe_fin_edge(held, True)
    if not fired:
        _fail("a second rising edge after safe must fire again")


def test_client_peek_and_order() -> None:
    src = proto_js()
    if "function sharkFin" not in src or "function maybeSharkFinFire" not in src:
        _fail("hand path must detect shark-fin from MediaPipe landmarks")
    fin_fn = _fn(src, "sharkFin")
    if "thumbParallel" not in fin_fn:
        _fail("sharkFin must refuse a parallel thumb")
    if "indexExtended" not in fin_fn:
        _fail("sharkFin must require an extended index — fist is not GUN")
    if "pinchStrength" not in fin_fn:
        _fail("sharkFin must refuse a pinch pose — do not double-fire")
    if "AimSample" in fin_fn or "publishAim" in fin_fn or "updateAim" in fin_fn:
        _fail("sharkFin must not touch the mailbox — five fields stay")
    trig = _fn(src, "maybeSharkFinFire")
    if "fire()" not in trig:
        _fail("shark-fin must peek through fire()")
    if "updateAim(" in trig or "publishAim(" in trig:
        _fail("shark-fin rewrites aim — trigger must peek last pointing UV")
    if 'phase === "range"' in trig or 'phase === "bay"' in trig:
        _fail("maybeSharkFinFire re-gates the verb — waiting Yard would mute")
    if "S.desktop" not in trig:
        _fail("shark-fin must no-op when DESKTOP owns the pad fallback")
    if "S.finHeld" not in trig:
        _fail("shark-fin must rising-edge, not held auto-fire")
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
    if "maybeSharkFinFire" in desk_else.group(1) or "maybePinchFire" in desk_else.group(1):
        _fail("!camReady DESKTOP must not shark-fin -- HID is the pad fallback")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", src)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample must stay five fields — do not invent a sixth")
    if "finHeld: false" not in src:
        _fail("shark-fin hold lives on S, not on AimSample")


def test_space_forcegun_is_not_shoot() -> None:
    src = proto_js()
    keys = src[src.find('addEventListener("keydown"') : src.find('addEventListener("keyup"')]
    space = re.search(r'if \(e\.code === "Space"\) \{([^}]+)\}', keys)
    if not space:
        _fail("Space forceGun handler missing")
    body = space.group(1)
    if "S.forceGun = true" not in body:
        _fail("Space must stay the Q4 forceGun escape")
    if "updateMode" not in body:
        _fail("#84: Space forceGun must still call updateMode")
    if "fire(" in body or "maybeSharkFinFire" in body:
        _fail("Space forceGun is fail-to-lock escape — not product shoot")


def test_hid_desktop_fallback_stays() -> None:
    src = proto_js()
    hid = _fn(src, "onHidPointerDown")
    if "if (S.desktop || S.forceGun) publishAim(e.clientX, e.clientY)" not in hid:
        _fail("DESKTOP HID must still publish click UV before fire() peek")
    if "fire()" not in hid:
        _fail("DESKTOP / pad fallback must still peek through fire()")
    if "maybeSharkFinFire" in hid:
        _fail("HID click must not invent shark-fin — camera owns the gesture")
    fire = _fn(src, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if "coastTrack" in fire or "updateAim" in fire:
        _fail("fire() recomputes aim")


def test_docs_lock() -> None:
    prod = (ROOT / "docs/PRODUCTION.md").read_text(encoding="utf-8")
    pipe = (ROOT / "docs/aim_pipeline.md").read_text(encoding="utf-8")
    track = (ROOT / "research/TRACKING.md").read_text(encoding="utf-8")
    if "shark-fin" not in prod.lower() and "shark fin" not in prod.lower():
        _fail("PRODUCTION.md must lock shark-fin as product shoot")
    if "maybeSharkFinFire" not in prod:
        _fail("PRODUCTION.md must name maybeSharkFinFire")
    if "shark-fin" not in pipe.lower() and "shark fin" not in pipe.lower():
        _fail("aim_pipeline.md must lock shark-fin as product shoot")
    if "maybeSharkFinFire" not in pipe:
        _fail("aim_pipeline.md must name maybeSharkFinFire")
    if "shark-fin" not in track.lower() and "shark fin" not in track.lower():
        _fail("TRACKING.md must point at shark-fin as product shoot")
    if "Juan LOCK" not in track or "PRODUCT.md" not in track:
        _fail("TRACKING.md must keep the #85 Juan lock and PRODUCT.md pointer")
    if "Not implemented in this docs cut" in track:
        _fail("TRACKING.md must not still claim shark-fin is unimplemented")
    if "maybeSharkFinFire" not in track:
        _fail("TRACKING.md must name maybeSharkFinFire as this cut")
    if "AimSample" not in track or "t_hw" not in track:
        _fail("TRACKING.md must keep the five-field AimSample pointer")
    product = (ROOT / "research/PRODUCT.md").read_text(encoding="utf-8")
    if "Thumb up like a shark fin" not in product:
        _fail("PRODUCT.md must keep the Juan SHOOT = shark-fin lock")
    js = proto_js()
    if "function maybeReloadGesture" not in js or "function reloadGesture" not in js:
        _fail("reload is this cut — maybeReloadGesture must exist next to shark-fin")
    fin_fn = _fn(js, "sharkFin")
    if "chargerPlug" not in fin_fn:
        _fail("sharkFin must refuse charger-plug — do not false-fire reload")
    ci = (ROOT / "tools/ci.sh").read_text(encoding="utf-8")
    if "test_shark_fin.py" not in ci:
        _fail("ci.sh must run the shark-fin contract")
    if "test_reload_gesture.py" not in ci:
        _fail("ci.sh must run the reload gesture contract")


def main() -> int:
    try:
        test_geometry_table()
        test_rising_edge_not_auto()
        test_client_peek_and_order()
        test_space_forcegun_is_not_shoot()
        test_hid_desktop_fallback_stays()
        test_docs_lock()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("shark-fin contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
