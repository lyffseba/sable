#!/usr/bin/env python3
"""Fist is presence, not pointing lock.

Fail loud if a curled index refreshes lastDetAt, chases the nail, opens
fallbackSkin, keeps mode GUN after the pointing sticky window, or breaks
#94 empty-landmark hygiene / shark-fin re-extend.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402
from test_aim_verb import mode as chip_mode  # noqa: E402
from test_shark_fin import (  # noqa: E402
    apply_mp_landmarks,
    gun_fist,
    gun_shark,
    index_extended,
    maybe_fin_edge,
    nail_muzzle,
    shark_fin,
)

LIFT_STICKY_MS = 550.0
COAST_MS = 100.0
LIFT_ON_MS = 50.0
NCC_GOOD = 0.58


def _fail(msg: str) -> None:
    raise AssertionError(f"FIST PRESENCE FAIL: {msg}")


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


def update_mode(state: dict, now: float, dtm: float = 16.0) -> str:
    """Mirror proto/aim.js updateMode with the live-fist belt."""
    if state.get("desktop"):
        state["mode"] = "DESKTOP"
        state["seeking"] = False
        state["lifted"] = True
        return "DESKTOP"
    since = now - state["lastDetAt"] if state.get("lastDetAt") else 1e9
    coasting = bool(state.get("smooth")) and since <= COAST_MS
    recent = bool(state.get("smooth")) and since <= LIFT_STICKY_MS
    det = state.get("det")
    det_good = bool(det and det.get("conf", 0) >= NCC_GOOD)
    lm = state.get("handLm")
    fist_live = bool(lm and not index_extended(lm))
    hand_owns = (det_good or recent) and not fist_live
    lift_ms = float(state.get("liftMs") or 0)
    if state.get("forceGun") or hand_owns:
        lift_ms = min(160.0, lift_ms + dtm)
    else:
        lift_ms = max(0.0, lift_ms - dtm)
    state["liftMs"] = lift_ms
    lifted = bool(state.get("forceGun")) or lift_ms >= LIFT_ON_MS
    state["lifted"] = lifted
    if state.get("forceGun"):
        state["mode"] = "GUN"
        state["seeking"] = not (det_good or coasting)
        return "GUN"
    if lifted or hand_owns:
        state["mode"] = "GUN"
        state["seeking"] = not (det_good or coasting) and not lifted
        return "GUN"
    if state.get("hidMoving"):
        state["mode"] = "PAD"
        state["seeking"] = True
        return "PAD"
    state["mode"] = "SEEKING"
    state["seeking"] = True
    return "SEEKING"


def test_fist_clocks_and_euro() -> None:
    gun = gun_shark()
    fist = gun_fist()
    gun_uv = nail_muzzle(gun)
    fist_uv = nail_muzzle(fist)
    if math_close(gun_uv, fist_uv):
        _fail("fist fixture must curl away from the pointing nail")
    state = {
        "handLm": None,
        "finHeld": True,
        "reloadHeld": True,
        "lastDetAt": 0,
        "lastHandAt": 0,
        "det": None,
        "smooth": None,
        "liftMs": 0.0,
        "desktop": False,
        "forceGun": False,
        "hidMoving": False,
    }
    if not apply_mp_landmarks([gun], state, now=1000):
        _fail("pointing apply must return true")
    if state["lastDetAt"] != 1000 or state["lastHandAt"] != 1000:
        _fail("pointing must stamp lastDetAt and lastHandAt")
    if state["smooth"]["x"] != gun_uv[0] or state["smooth"]["y"] != gun_uv[1]:
        _fail("pointing must lock One Euro / S.smooth on the nail")
    state["liftMs"] = 160.0
    if not apply_mp_landmarks([fist], state, now=1080):
        _fail("fist must return true — Hands still saw a hand")
    if state["lastDetAt"] != 1000:
        _fail("fist landmarks: lastDetAt must stay at the last pointing sample")
    if state["lastHandAt"] != 1080:
        _fail("fist must refresh presence lastHandAt")
    if state["smooth"]["x"] != gun_uv[0] or state["smooth"]["y"] != gun_uv[1]:
        _fail("One Euro / S.smooth must not advance toward the curled tip")
    if abs(state["smooth"]["x"] - fist_uv[0]) < 1e-6 and abs(state["smooth"]["y"] - fist_uv[1]) < 1e-6:
        _fail("S.smooth chased the curled nail")
    if state["finHeld"] or state["reloadHeld"]:
        _fail("fist must drop finHeld / reloadHeld")
    if state["handLm"] is not fist:
        _fail("fist must keep handLm so re-extend / shark-fin edge can return")


def math_close(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return abs(a[0] - b[0]) < 8 and abs(a[1] - b[1]) < 8


def test_sticky_expires_off_gun() -> None:
    gun = gun_shark()
    fist = gun_fist()
    state = {
        "handLm": None,
        "finHeld": False,
        "reloadHeld": False,
        "lastDetAt": 0,
        "lastHandAt": 0,
        "det": None,
        "smooth": None,
        "liftMs": 0.0,
        "desktop": False,
        "forceGun": False,
        "hidMoving": False,
        "mode": "SEEKING",
    }
    apply_mp_landmarks([gun], state, now=0)
    state["liftMs"] = 160.0
    mode = update_mode(state, 0)
    if mode != "GUN":
        _fail("pointing must own GUN")
    t = 0.0
    while t <= LIFT_STICKY_MS + 80:
        t += 16.0
        apply_mp_landmarks([fist], state, now=t)
        mode = update_mode(state, t)
        if state.get("desktop") or mode == "DESKTOP":
            _fail("fist must not SEEKING→auto-desktop / invent DESKTOP")
    if mode == "GUN":
        _fail("after sticky window with fist held, updateMode must leave GUN")
    if mode == "DESKTOP" or state.get("desktop"):
        _fail("leaving GUN on a held fist must not auto-desktop")
    # Presence is still live — not a hand-leave that should invent pad DESKTOP.
    if state["lastHandAt"] < LIFT_STICKY_MS:
        _fail("fist held through sticky must keep refreshing lastHandAt")
    if chip_mode(False, False, False, False, False, recent=False, lifted=False) == "GUN":
        _fail("chip table: no det / coast / recent / lift is not GUN")


def test_reextend_and_empty_hygiene() -> None:
    gun = gun_shark()
    fist = gun_fist()
    state = {
        "handLm": gun,
        "finHeld": True,
        "reloadHeld": True,
        "lastDetAt": 1000,
        "lastHandAt": 1000,
        "det": {"x": 12.0, "y": 34.0, "conf": 0.92},
        "smooth": {"x": 12.0, "y": 34.0},
    }
    if apply_mp_landmarks([], state, now=1100) or apply_mp_landmarks(None, state, now=1100):
        _fail("#94: empty landmarks must return false")
    if state["handLm"] is not None or state["finHeld"] or state["reloadHeld"]:
        _fail("#94: empty must clear handLm and both held flags")
    if state["lastDetAt"] != 1000 or not state["det"]:
        _fail("#94: empty must not zero lastDetAt / S.det")
    unusable = {0: (0.50, 0.82), 4: (0.33, 0.34)}
    state["handLm"] = gun
    state["finHeld"] = True
    state["reloadHeld"] = True
    if apply_mp_landmarks([unusable], state, now=1200):
        _fail("#94: unusable hand must return false")
    if state["handLm"] is not None or state["finHeld"] or state["reloadHeld"]:
        _fail("#94: unusable must clear handLm and both held flags")
    if state["lastDetAt"] != 1000 or not state["det"]:
        _fail("#94: unusable must not zero lastDetAt / S.det")

    apply_mp_landmarks([fist], state, now=1300)
    if state["lastDetAt"] != 1000:
        _fail("fist after empty hygiene must still not refresh lastDetAt")
    if not apply_mp_landmarks([gun], state, now=1400):
        _fail("re-extend must restore pointing lock")
    if state["lastDetAt"] != 1400:
        _fail("re-extend must stamp lastDetAt")
    held, fired = maybe_fin_edge(state["finHeld"], shark_fin(gun))
    if not fired or not held:
        _fail("re-extend shark-fin rising edge must still work")


def test_client_split() -> None:
    src = proto_js()
    apply = _fn(src, "applyMpLandmarks")
    if "S.lastHandAt" not in apply:
        _fail("applyMpLandmarks must refresh presence lastHandAt")
    if "if (!indexExtended" not in apply:
        _fail("applyMpLandmarks must gate pointing lock on indexExtended")
    if apply.find("applyEuroPoint") < apply.find("if (!indexExtended"):
        _fail("fist must return before applyEuroPoint")
    if apply.find("S.lastDetAt") < apply.find("if (!indexExtended"):
        _fail("fist must return before writing lastDetAt")
    if "fallbackSkin" in apply:
        _fail("applyMpLandmarks must not open fallbackSkin / invent skin GUN")
    if apply.count("S.handLm = null") < 2:
        _fail("#94: empty / unusable paths must null handLm")
    if apply.count("S.finHeld = false") < 3 or apply.count("S.reloadHeld = false") < 3:
        _fail("empty / unusable / fist must drop both held flags")
    if "S.lastDetAt = 0" in apply or "S.det = null" in apply:
        _fail("applyMpLandmarks must not zero lastDetAt / S.det")
    if apply.find("return false") > apply.find("S.lastDetAt"):
        _fail("#94: early-fail must return before writing lastDetAt")

    present = _fn(src, "handsPresent")
    if "S.lastHandAt" not in present:
        _fail("handsPresent must read the presence clock")
    if "S.lastDetAt" in present:
        _fail("handsPresent must not follow pointing lastDetAt")

    kick = _fn(src, "kickAndFresh")
    if "handsPresent" not in kick and "lastHandAt" not in kick:
        _fail("kickAndFresh must follow presence, not only pointing lastDetAt")
    if "lastDetAt" in kick:
        _fail("kickAndFresh must not treat lastDetAt as Worker freshness")

    run = _fn(src, "runTrack")
    if run.count("handsPresent") < 2:
        _fail("runTrack mpFresh / rvfc must follow the presence clock")
    grab = _fn(src, "grabFrame")
    if "handsPresent" not in grab and "lastHandAt" not in grab:
        _fail("grabFrame mpFresh must follow presence, not only lastDetAt")

    mode_body = _fn(src, "updateMode")
    if "indexExtended" not in mode_body or "S.handLm" not in mode_body:
        _fail("updateMode belt: live fist must not handOwns")
    if "LIFT_STICKY_MS" not in mode_body or "COAST_MS" not in mode_body:
        _fail("do not replace sticky/coast constants — only stop fist refreshing lastDetAt")
    if "goDesktopRange" in mode_body or "S.desktop = true" in mode_body:
        _fail("updateMode must not auto-desktop when a fist leaves GUN")

    skin = _fn(src, "fallbackSkin")
    if "S.handLm = null" not in skin:
        _fail("fallbackSkin clear path must stay — Hands-reported fist must not reach it")

    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", src)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample must stay five fields")
    if "function publishAim" not in src:
        _fail("publishAim must stay")
    gate = _fn(src, "productGunHidFire")
    if "return false" not in gate or "fire(" in gate:
        _fail("productGunHidFire must stay false and not peek")
    if "function maybePinchFire" in src or "maybePinchFire(" in src:
        _fail("pinch must not peek fire()")
    keys = src[src.find('addEventListener("keydown"') : src.find('addEventListener("keyup"')]
    space = re.search(r'if \(e\.code === "Space"\) \{([^}]+)\}', keys)
    if not space or "S.forceGun = true" not in space.group(1):
        _fail("Space must stay the Q4 forceGun escape")
    if "fire(" in space.group(1):
        _fail("Space is not a shot")

    fin = _fn(src, "sharkFin")
    if "indexExtended" not in fin or "thumbParallel" not in fin:
        _fail("shark-fin geometry must stay — fist is not a threshold change")
    plug = _fn(src, "chargerPlug")
    if "fingerCeiling" not in plug:
        _fail("charger-plug geometry must stay")
    if "MAG_CAP" not in src or "function spendGestureRound" not in src:
        _fail("MAG chip / spend path must stay untouched")
    if "drawModeChip" in _fn(src, "applyMpLandmarks"):
        _fail("applyMpLandmarks must not paint MAG")


def test_ci_wired() -> None:
    ci = (ROOT / "tools/ci.sh").read_text(encoding="utf-8")
    if "test_fist_presence.py" not in ci:
        _fail("ci.sh must run the fist-presence contract")
    if "test_shark_fin.py" not in ci:
        _fail("ci.sh must still run the shark-fin contract")


def main() -> int:
    try:
        test_fist_clocks_and_euro()
        test_sticky_expires_off_gun()
        test_reextend_and_empty_hygiene()
        test_client_split()
        test_ci_wired()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("fist presence contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
