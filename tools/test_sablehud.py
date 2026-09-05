#!/usr/bin/env python3
"""SableHUD lock: thin arcade chips over live aim.

Fail loud if gallery SCORE / ROUND / end leave the 22px chip bar, hangar
WAIT / READY / LIVE leave S.hangar, the thin ROOM chip leaves wait_practice,
bloom covers the reticle, Offline one-click dies, Salt House becomes the
only gun, chips thicken the lobby, or HUD copy / a ROOM chip hides the gun.
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
    if "hangarHudChip" not in hud:
        _fail("SableHUD lost hangar chips from S.hangar")
    if "roomHudChip" not in hud:
        _fail("SableHUD lost the thin ROOM chip on wait_practice")
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
    if "roomHudChip" in _js_fn(js, "fire") or "S.room" in _js_fn(js, "fire"):
        _fail("fire() gated on room chip — Fire = AimBus HID peek")
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
    if ("enterRangePreserve()" not in start_room and 'play("range")' not in start_room) or "/api/lobby/start" not in start_room:
        _fail_only_gun("ENTER RANGE no longer shares the Salt House")
    if re.search(r"await\s+", start_room):
        _fail("ENTER RANGE awaits net — lift/HID is behind the lobby POST")
    start_bay = _js_fn(js, "lobbyStartBay")
    if 'play("bay")' not in start_bay and 'setPhase("bay")' not in start_bay:
        _fail("parked lobbyStartBay lost the booth drop")
    if "/api/lobby/start" in start_bay:
        _fail("parked lobbyStartBay started the shared gallery")


def test_hangar_chips_from_s_hangar() -> None:
    js = proto_js()
    chip = _js_fn(js, "hangarHudChip")
    if "S.hangar" not in chip:
        _fail("hangar chips must read S.hangar only")
    if '"WAIT"' not in chip or '"READY"' not in chip or '"LIVE"' not in chip:
        _fail("hangar chips must stay WAIT / READY / LIVE")
    if "wait_practice" not in chip or "match_live" not in chip:
        _fail("hangar chips must map wait_practice / match_live")
    if re.search(r"\bphase\b", chip) or "setPhase" in chip or "assignPhase" in chip:
        _fail("hangar chips renamed a screen phase — read S.hangar only")
    if "aimBus" in chip or "fire(" in chip or "AimSample" in chip:
        _fail("hangar chips gated fire / touched AimSample")
    if re.search(r"await\s+", chip) or "fetch(" in chip:
        _fail("hangar chips await — HUD trapped HID")
    if "shadowBlur" in chip or "glow" in chip.lower() or "filter" in chip:
        _fail("hangar chips bloomed")
    if "H * 0.78" in chip or "H*0.78" in chip or "H * 0.5" in chip:
        _fail("hangar chips hide the gun or the reticle")
    hud = _js_fn(js, "drawHUD")
    if "hangarHudChip" not in hud:
        _fail("SableHUD lost hangar chips")
    if "drawSableChip" not in hud:
        _fail("hangar chips left the thin SableHUD bar")
    mode_at = hud.find("drawModeChip")
    hangar_at = hud.find("hangarHudChip")
    if mode_at < 0 or hangar_at < 0 or mode_at > hangar_at:
        _fail("hangar chips wiped PAD/GUN — mode chip must stay live")
    if 'phase === "range"' not in hud or '"SCORE "' not in hud:
        _fail("gallery SCORE must stay gated on range — hangar chips must not thicken lobby")
    if '"ROUND "' not in hud and '"ROUND"' not in hud:
        _fail("RANGE clock left the bar — hangar chips must not unpin gallery ROUND")
    if '"60s GALLERY"' not in hud:
        _fail("RANGE gallery chip left the bar")
    if "H * 0.78" in hud or "H*0.78" in hud or "H * 0.5" in hud:
        _fail("hangar chips hide the gun or the reticle")
    if "RAISE YOUR HAND" in hud or "ESC = miss" in hud or "Impact" in hud:
        _fail("hangar chips grew a tutorial wall")
    if "setPhase" in hud or "fire(" in hud or "aimBus" in hud:
        _fail("HUD trapped lift/HID")
    if "roomHudChip" not in hud:
        _fail("ROOM chip must stay additive with WAIT / READY / LIVE")
    hangar_at = hud.find("hangarHudChip")
    room_at = hud.find("roomHudChip")
    if hangar_at < 0 or room_at < 0 or hangar_at > room_at:
        _fail("ROOM chip must sit with hangar chips — do not hide the gun")
    d2 = _js_fn(js, "draw2D")
    lobby = d2[d2.find('phase === "lobby"') :]
    if not lobby:
        _fail("draw2D lost the waiting-arena path")
    xh = lobby.find("drawCrosshair")
    chips = lobby.find("drawHUD")
    if xh < 0 or chips < 0 or xh > chips:
        _fail("waiting-arena hangar chips must paint over live aim — crosshair then chips")
    preserve = _js_fn(js, "enterRangePreserve")
    if 'assignHangar("match_live")' not in preserve:
        _fail("promote WAIT→LIVE must write match_live")
    if "clearRect" in preserve or "drawHUD" in preserve or "drawModeChip" in preserve:
        _fail("promote WAIT→LIVE wiped the HUD")
    if re.search(r"await\s+", preserve) or "fetch(" in preserve:
        _fail("promote awaits — WAIT→LIVE trapped HID")
    fire = _js_fn(js, "fire")
    if "hangarHudChip" in fire or "S.hangar" in fire:
        _fail("fire() gated on hangar — Fire = AimBus HID peek")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")


def test_lobby_stays_thin() -> None:
    css = (ROOT / "proto/style.css").read_text(encoding="utf-8")
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    js = proto_js()
    hud = _js_fn(js, "drawHUD")
    if 'phase !== "range"' not in hud:
        _fail("SableHUD must not thicken the lobby with gallery chips")
    if "hangarHudChip" not in hud:
        _fail("waiting arena lost hangar chips")
    if "roomHudChip" not in hud:
        _fail("waiting arena lost the thin ROOM chip")
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
    if "WAIT" not in modes or "READY" not in modes or "LIVE" not in modes:
        _fail("docs/modes.md must name hangar WAIT / READY / LIVE chips")
    if "S.hangar" not in modes:
        _fail("docs/modes.md must paint hangar chips from S.hangar")
    if "ROOM" not in modes or "wait_practice" not in modes:
        _fail("docs/modes.md must name the thin ROOM chip on wait_practice")
    if "Do not hide the gun with a ROOM chip" not in modes:
        _fail("docs/modes.md must fail loud if a ROOM chip hides the gun")
    if "Do not thicken the lobby" not in modes and "thicken the lobby" not in modes:
        _fail("docs/modes.md must refuse a thicker lobby")
    if "test_sablehud.py" not in bible:
        _fail("PRODUCTION.md must fail loud through test_sablehud.py")
    if "ROOM" not in bible or "wait_practice" not in bible:
        _fail("PRODUCTION.md must name the thin ROOM chip on wait_practice")
    if "ROOM chip hides the gun" not in bible:
        _fail("PRODUCTION.md must fail loud if a ROOM chip hides the gun / thickens the lobby")
    if "v0.20.0" not in bible:
        _fail("PRODUCTION.md must stand v0.20.0 until Build tags this gallery HUD tip")


def test_room_chip_on_wait_practice() -> None:
    js = proto_js()
    chip = _js_fn(js, "roomHudChip")
    if "S.hangar" not in chip:
        _fail("ROOM chip must read S.hangar — wait_practice (and match_live)")
    if "S.room" not in chip:
        _fail("ROOM chip must read S.room")
    if '"ROOM  "' not in chip:
        _fail("ROOM chip must stay a thin ROOM code label")
    if "wait_practice" not in chip or "match_live" not in chip:
        _fail("ROOM chip must map wait_practice / match_live")
    if "Locker.colors.mint" not in chip and "Locker.colors.bone" not in chip:
        _fail("ROOM chip must stay bone / mint / rust")
    if re.search(r"\bphase\b", chip) or "setPhase" in chip or "assignPhase" in chip:
        _fail("ROOM chip renamed a screen phase — read S.hangar only")
    if "aimBus" in chip or "fire(" in chip or "AimSample" in chip:
        _fail("ROOM chip gated fire / touched AimSample")
    if re.search(r"await\s+", chip) or "fetch(" in chip:
        _fail("ROOM chip awaits — HUD trapped HID")
    if "shadowBlur" in chip or "glow" in chip.lower() or "filter" in chip:
        _fail("ROOM chip bloomed")
    if "H * 0.78" in chip or "H*0.78" in chip or "H * 0.5" in chip:
        _fail("ROOM chip hides the gun or the reticle")
    if "Impact" in chip or "RAISE YOUR HAND" in chip:
        _fail("ROOM chip grew a tutorial wall")
    hud = _js_fn(js, "drawHUD")
    if "roomHudChip" not in hud or "drawSableChip" not in hud:
        _fail("ROOM chip left the thin SableHUD bar")
    if "SABLE_HUD_H" not in _js_fn(js, "drawSableChip"):
        _fail("ROOM chip must stay 22px — do not thicken chrome")
    mode_at = hud.find("drawModeChip")
    hangar_at = hud.find("hangarHudChip")
    room_at = hud.find("roomHudChip")
    if mode_at < 0 or hangar_at < 0 or room_at < 0:
        _fail("ROOM chip must stay additive with PAD/GUN + WAIT/READY/LIVE")
    if mode_at > hangar_at or hangar_at > room_at:
        _fail("ROOM chip wiped PAD/GUN or hangar chips")
    if 'phase === "range"' not in hud or '"SCORE "' not in hud:
        _fail("gallery SCORE must stay range-gated — ROOM must not thicken lobby")
    if "H * 0.78" in hud or "H*0.78" in hud or "H * 0.5" in hud or "Impact" in hud:
        _fail("ROOM chip hides the gun")
    if "setPhase" in hud or "fire(" in hud or "aimBus" in hud:
        _fail("HUD trapped lift/HID")
    d2 = _js_fn(js, "draw2D")
    lobby = d2[d2.find('phase === "lobby"') :]
    if not lobby:
        _fail("draw2D lost the waiting-arena path")
    xh = lobby.find("drawCrosshair")
    chips = lobby.find("drawHUD")
    if xh < 0 or chips < 0 or xh > chips:
        _fail("waiting-arena ROOM chip must paint over live aim — crosshair then chips")
    fire = _js_fn(js, "fire")
    if "roomHudChip" in fire or "hangarHudChip" in fire:
        _fail("fire() gated on ROOM / hangar chips — Fire = AimBus HID peek")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if re.search(r"await\s+", fire):
        _fail("fire() awaits — ROOM chip trapped HID")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    css = (ROOT / "proto/style.css").read_text(encoding="utf-8")
    if 'id="lobby-room"' not in html or "ROOM ———" not in html:
        _fail("lobby overlay lost ROOM — HUD chip is additive, not a wipe")
    lobby_css = re.search(r"\.lobby-inner \{([^}]+)\}", css)
    if not lobby_css or "padding: 24px 16px 40px" not in lobby_css.group(1):
        _fail("lobby was thickened — ROOM chip must stay on the 22px bar")
    if "gap: 12px" not in lobby_css.group(1):
        _fail("lobby was thickened — action gap grew")


def test_sablehud_soft_lock_bars() -> None:
    """ROOM chip soft-lock — same PR. Do not merge from the agent."""
    js = proto_js()
    hud = _js_fn(js, "drawHUD")
    chip = _js_fn(js, "roomHudChip")
    hangar = _js_fn(js, "hangarHudChip")
    if "roomHudChip" not in hud or "hangarHudChip" not in hud:
        _fail("ROOM chip must stay thin and additive with WAIT / READY / LIVE")
    if '"WAIT"' not in hangar or '"READY"' not in hangar or '"LIVE"' not in hangar:
        _fail("hangar chips must stay WAIT / READY / LIVE")
    if '"ROOM  "' not in chip:
        _fail("ROOM chip left the thin ROOM code label")
    if "if (roomChip) chips.push(roomChip)" not in hud:
        _fail("ROOM chip must stay additive — hangar chip stays, ROOM pushes next")
    if re.search(r'if \(phase === "range"\).*roomChip', hud):
        _fail("ROOM chip must not be RANGE-gated — wait_practice lobby must see it")
    mode_at = hud.find("drawModeChip")
    hangar_at = hud.find("hangarHudChip")
    room_at = hud.find("roomHudChip")
    if mode_at < 0 or hangar_at < 0 or room_at < 0 or mode_at > hangar_at or hangar_at > room_at:
        _fail("ROOM chip wiped PAD/GUN mode chips")
    if "clearRect" in hud:
        _fail("drawHUD wiped the bar — PAD/GUN must stay live")
    if "shadowBlur" in hud or "glow" in hud.lower() or "shadowBlur" in chip:
        _fail("ROOM / SableHUD bloomed")
    if 'if (phase === "range") chips.push(["SCORE "' not in hud:
        _fail("RANGE SCORE left the range gate — RANGE must stay pinned")
    if 'if (phase === "range") chips.push(["ROUND "' not in hud:
        _fail("RANGE ROUND left the range gate — RANGE must stay pinned")
    if _js_const(js, "SABLE_HUD_H") != 22:
        _fail("SableHUD bar must stay thin (22px)")
    plate = _js_fn(js, "drawSableChip")
    if "rgba(10,12,16" not in plate and "rgba(10, 12, 16" not in plate:
        _fail("chips must stay charcoal plates")
    if "Locker.colors.bone" not in hud or "Locker.colors.mint" not in hud or "Locker.colors.rust" not in hud:
        _fail("chips must stay bone / mint / rust")
    if "HUD_PAD" not in hud or "H * 0.78" in hud or "H*0.78" in hud or "H * 0.5" in hud:
        _fail("ROOM chip over cuff/reticle")
    if "Impact" in hud or "RAISE YOUR HAND" in hud:
        _fail("ROOM chip hid the gun")
    fire = _js_fn(js, "fire")
    if "aimBus.fire" not in fire or "roomHudChip" in fire or "hangarHudChip" in fire:
        _fail("fire() must peek AimBus — ROOM must not gate HID")
    if re.search(r"await\s+", fire):
        _fail("fire() awaits — soft-lock trapped HID")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    offline = re.search(
        r'\$\("btn-play"\)\.addEventListener\("click", \(\) => \{[\s\S]*?play\("range"\)',
        js,
    )
    if not offline or "S.online = false" not in offline.group(0):
        _fail("OFFLINE must stay one-click local")
    warm = _js_fn(js, "lobbyWarmup")
    if re.search(r"await\s+", warm) or "/api/lobby/start" in warm:
        _fail("WARM UP must stay one-click local")
    if 'id="btn-bay"' in html or "ENTER BAY" in html:
        _fail("Bay must stay parked")


def main() -> int:
    try:
        test_thin_arcade_chips()
        test_over_live_aim()
        test_offline_never_only_gun()
        test_hangar_chips_from_s_hangar()
        test_room_chip_on_wait_practice()
        test_sablehud_soft_lock_bars()
        test_lobby_stays_thin()
        test_docs_lock()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("sablehud lock ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
