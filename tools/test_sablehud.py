#!/usr/bin/env python3
"""SableHUD lock: thin arcade chips over live aim.

Fail loud if gallery SCORE / ROUND / end leave the 22px chip bar, bloom
covers the reticle, Offline one-click dies, Salt House becomes the only
gun, or the lobby grows a thicker HUD.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402


def _fail(msg: str) -> None:
    raise AssertionError(f"SABLEHUD FAIL: {msg}")


def _fail_only_gun(msg: str) -> None:
    raise AssertionError(f"SABLEHUD FAIL: Salt House/gallery became the only gun — {msg}")


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"(?:async )?function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        _fail(f"missing function {name}")
    return m.group(0)


def _js_const(src: str, name: str) -> float:
    m = re.search(rf"const {name} = (-?[0-9.]+)", src)
    if not m:
        _fail(f"missing const {name}")
    return float(m.group(1))


def test_thin_arcade_chips() -> None:
    js = proto_js()
    if _js_const(js, "SABLE_HUD_H") != 22:
        _fail("SableHUD bar must stay thin (22px chips)")
    chip = _js_fn(js, "drawSableChip")
    if "SABLE_HUD_H" not in chip:
        _fail("drawSableChip must use the thin SableHUD height")
    if "700 11px" not in chip:
        _fail("chips must stay arcade-readable (700 11px)")
    if "rgba(10,12,16" not in chip and "rgba(10, 12, 16" not in chip:
        _fail("chips must stay charcoal plates")
    if "shadowBlur" in chip or "glow" in chip.lower() or "filter" in chip:
        _fail("SableHUD chips bloomed")
    hud = _js_fn(js, "drawHUD")
    if "drawSableChip" not in hud:
        _fail("gallery feedback left the SableHUD chip bar")
    if "galleryLeftMs" not in hud or "gallerySessionLabel" not in hud:
        _fail("HUD must read the live gallery clock / session")
    if '"SCORE "' not in hud:
        _fail("HUD lost the SCORE chip")
    if '"ROUND "' not in hud and '"ROUND"' not in hud:
        _fail("HUD lost the ROUND chip")
    if '"60s GALLERY"' not in hud:
        _fail("HUD lost the 60s GALLERY chip")
    if '"GALLERY CLEAR"' not in hud:
        _fail("HUD lost the end chip")
    if "Locker.colors.bone" not in hud or "Locker.colors.mint" not in hud or "Locker.colors.rust" not in hud:
        _fail("chips must stay bone / mint / rust")
    if "HUD_PAD" not in hud:
        _fail("SableHUD must stay a top bar over live aim")
    if "Impact" in hud:
        _fail("SableHUD thickened — no Impact billboard")
    if "RAISE YOUR HAND" in hud or "ESC = miss" in hud:
        _fail("tutorial wall over live aim")
    if "H * 0.78" in hud or "H*0.78" in hud or "H * 0.5" in hud:
        _fail("HUD hides the gun or the reticle")
    if "shadowBlur" in hud or "glow" in hud.lower():
        _fail("gallery HUD bloomed over the reticle")


def test_over_live_aim() -> None:
    js = proto_js()
    d2 = _js_fn(js, "draw2D")
    ranged = d2[d2.find('phase === "range"') :]
    if not ranged:
        _fail("draw2D lost the gallery range path")
    xh = ranged.find("drawCrosshair")
    hud = ranged.find("drawHUD")
    if xh < 0 or hud < 0 or xh > hud:
        _fail("SableHUD must paint over live aim — crosshair then chips")
    fire = _js_fn(js, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if re.search(r"await\s+", fire):
        _fail("fire() awaits — HUD/look trapped HID")
    hud_fn = _js_fn(js, "drawHUD")
    if "setPhase" in hud_fn or "fire(" in hud_fn or "aimBus" in hud_fn:
        _fail("HUD trapped lift/HID")
    cross = _js_fn(js, "drawCrosshair")
    if "shadowBlur" in cross or "glow" in cross.lower():
        _fail("reticle bloom is forbidden")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")


def test_offline_never_only_gun() -> None:
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    js = proto_js()
    if 'id="btn-play"' not in html or ">OFFLINE<" not in html:
        _fail("boot lost one-click OFFLINE")
    offline = re.search(
        r'\$\("btn-play"\)\.addEventListener\("click", \(\) => \{[\s\S]*?play\("range"\)',
        js,
    )
    if not offline:
        _fail("OFFLINE must still call play(range) in one click")
    if "S.online = false" not in offline.group(0):
        _fail("OFFLINE must stay local")
    if "S.warmup = false" not in offline.group(0):
        _fail("OFFLINE must clear WARM UP")
    if 'play("bay")' in offline.group(0):
        _fail_only_gun("OFFLINE was rerouted into Bay")
    if 'id="btn-bay"' in html or re.search(r">\s*BAY\s*<", html):
        _fail("boot still offers BAY — Yard is the sole active map")
    if 'id="btn-lobby-warmup"' not in html or "WARM UP" not in html:
        _fail_only_gun("lobby lost WARM UP")
    if 'id="btn-lobby-range"' not in html or "ENTER RANGE" not in html:
        _fail_only_gun("lobby lost ENTER RANGE")
    if 'id="btn-lobby-bay"' in html or "ENTER BAY" in html:
        _fail("lobby still offers ENTER BAY — Bay is parked")
    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/start" in warm:
        _fail_only_gun("WARM UP started the shared house")
    if re.search(r"await\s+", warm):
        _fail("WARM UP awaits net — practice is soft-locked")
    start_room = _js_fn(js, "lobbyStartRange")
    if 'play("range")' not in start_room or "/api/lobby/start" not in start_room:
        _fail_only_gun("ENTER RANGE no longer shares the Salt House")
    start_bay = _js_fn(js, "lobbyStartBay")
    if 'play("bay")' not in start_bay and 'setPhase("bay")' not in start_bay:
        _fail("parked lobbyStartBay lost the booth drop")
    if "/api/lobby/start" in start_bay:
        _fail("parked lobbyStartBay started the shared gallery")


def test_lobby_stays_thin() -> None:
    css = (ROOT / "proto/style.css").read_text(encoding="utf-8")
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    js = proto_js()
    hud = _js_fn(js, "drawHUD")
    if 'phase !== "range"' not in hud:
        _fail("SableHUD must not paint the lobby")
    lobby = re.search(r"\.lobby-inner \{([^}]+)\}", css)
    if not lobby:
        _fail("lobby-inner rule missing")
    box = lobby.group(1)
    if "padding: 24px 16px 40px" not in box:
        _fail("lobby was thickened — padding left the thin waiting-arena")
    if "gap: 12px" not in box:
        _fail("lobby was thickened — action gap grew")
    inner = re.search(r'<div class="lobby-inner">([\s\S]*?)</div>\s*</div>\s*<div id="screen-range"', html)
    if not inner:
        _fail("lobby-inner markup missing")
    body = inner.group(1)
    if "SCORE" in body or "ROUND" in body or "SableHUD" in body:
        _fail("lobby grew gallery HUD chips")
    if "WARM UP" not in body or "ENTER RANGE" not in body:
        _fail_only_gun("lobby chrome lost a Yard path")
    if "ENTER BAY" in body or 'id="btn-lobby-bay"' in body:
        _fail("lobby chrome still offers ENTER BAY — Bay is parked")


def test_docs_lock() -> None:
    modes = (ROOT / "docs/modes.md").read_text(encoding="utf-8")
    bible = (ROOT / "docs/PRODUCTION.md").read_text(encoding="utf-8")
    if "SableHUD" not in modes:
        _fail("docs/modes.md must name the thin SableHUD bar")
    if "Do not thicken the lobby" not in modes and "thicken the lobby" not in modes:
        _fail("docs/modes.md must refuse a thicker lobby")
    if "test_sablehud.py" not in bible:
        _fail("PRODUCTION.md must fail loud through test_sablehud.py")
    if "v0.20.0" not in bible:
        _fail("PRODUCTION.md must stand v0.20.0 until Build tags this gallery HUD tip")


def main() -> int:
    try:
        test_thin_arcade_chips()
        test_over_live_aim()
        test_offline_never_only_gun()
        test_lobby_stays_thin()
        test_docs_lock()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("sablehud lock ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
