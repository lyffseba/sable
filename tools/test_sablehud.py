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
    if "galleryHudLeftMs" not in hud or "gallerySessionLabel" not in hud:
        _fail("HUD must read the live gallery clock / session")
    if '"SCORE "' not in hud:
        _fail("HUD lost the SCORE chip")
    if '"ROUND "' not in hud and '"ROUND"' not in hud:
        _fail("HUD lost the ROUND chip")
    if '"60s GALLERY"' not in hud:
        _fail("HUD lost the 60s GALLERY chip")
    if '"GALLERY CLEAR"' not in hud:
        _fail("HUD lost the end chip")
    if "sharedMatch" not in hud or "S.over" not in hud:
        _fail("match_live CLEAR must snap from room over — not local left")
    if re.search(r'if \(left <= 0\) stateChip = "GALLERY CLEAR"', hud):
        _fail("match_live CLEAR invented from local left<=0")
    if re.search(r"galleryLeftMs\(simMs\(\)\)", hud):
        _fail("match_live ROUND invented from local simMs")
    results = _js_fn(js, "showResults")
    if "ACCURACY" not in results or "S.shots" not in results or "S.hits" not in results:
        _fail("GALLERY CLEAR ACCURACY must snap from room hits / shots")
    if "COMBO" not in results or "S.comboMax" not in results:
        _fail("GALLERY CLEAR COMBO must snap from room combo_max")
    if re.search(r'\["COMBO", S\.combo\]', results):
        _fail("GALLERY CLEAR COMBO invented from live S.combo")
    fire = _js_fn(js, "fire")
    shared_at = fire.find("if (sharedMatch())")
    scan_at = fire.find("hitscanRange")
    shared_return = fire.find("return;", shared_at) if shared_at >= 0 else -1
    if shared_at < 0 or scan_at < 0 or shared_return < 0:
        _fail("fire() must park match_live before local credit")
    if fire.find("S.shots++", scan_at, shared_return) >= 0:
        _fail("match_live ACCURACY invented from local S.shots++")
    if fire.find("S.comboMax", scan_at, shared_return) >= 0:
        _fail("match_live COMBO invented from local S.comboMax")
    wait_at = fire.find("if (S.waitingYard)")
    wait_return = fire.find("return;", wait_at) if wait_at >= 0 else -1
    if wait_at < 0 or wait_return < 0:
        _fail("fire() must park WAIT before the local SCORE book")
    if fire.find("popup(", wait_at, wait_return) >= 0:
        _fail("WAIT painted point popups — SCORE chip stays range-gated")
    if 'if (phase === "range") chips.push(["SCORE "' not in hud:
        _fail("gallery SCORE must stay range-gated — WAIT must not invent a SCORE chip")
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


def test_q4_seeking_chip_thin() -> None:
    """Q4 SEEKING chip stays on the 22px SableHUD bar — not a tutorial wall."""
    js = proto_js()
    chip = _js_fn(js, "seekingHudChip")
    if "camReady" not in chip or "wait_practice" not in chip:
        _fail("SEEKING chip must tell camReady fail-to-lock on wait_practice")
    if '"SEEKING"' not in chip:
        _fail("SEEKING chip lost the SEEKING label")
    if "S.forceGun" not in chip:
        _fail("SEEKING chip must hide when Space forceGun escapes")
    mode_chip = _js_fn(js, "drawModeChip")
    label = re.search(r"const label = ([^;]+);", mode_chip)
    if not label:
        _fail("drawModeChip lost the MODE label")
    cond = label.group(1)
    seek_at = cond.find('"SEEKING"')
    if seek_at < 0:
        _fail("drawModeChip must still paint SEEKING when not forceGun / GUN")
    if "S.forceGun" not in cond[:seek_at]:
        _fail("drawModeChip prefers SEEKING on Space forceGun — MODE must match seekingHudChip")
    if 'S.mode !== "GUN"' not in cond[:seek_at] and 'S.mode != "GUN"' not in cond[:seek_at]:
        _fail("drawModeChip prefers SEEKING when S.mode is GUN — MODE must match seekingHudChip")
    if "Locker.colors.rust" not in chip and "Locker.colors.bone" not in chip and "Locker.colors.mint" not in chip:
        _fail("SEEKING chip must stay bone / mint / rust")
    if "shadowBlur" in chip or "glow" in chip.lower() or "filter" in chip:
        _fail("SEEKING chip bloomed")
    if "H * 0.78" in chip or "Impact" in chip or "RAISE YOUR HAND" in chip:
        _fail("SEEKING chip hides the gun or grew a tutorial wall")
    if "aimBus" in chip or "fire(" in chip or "AimSample" in chip:
        _fail("SEEKING chip gated fire / touched AimSample")
    hud = _js_fn(js, "drawHUD")
    if "seekingHudChip" not in hud or "drawSableChip" not in hud:
        _fail("SEEKING chip left the thin SableHUD bar")
    if "if (seekChip) chips.push(seekChip)" not in hud:
        _fail("SEEKING chip must stay additive — do not thicken the lobby")
    if 'phase === "range"' not in hud or '"SCORE "' not in hud:
        _fail("gallery SCORE must stay range-gated — SEEKING must not thicken lobby")
    if "SABLE_HUD_H" not in _js_fn(js, "drawSableChip"):
        _fail("SEEKING chip must stay 22px — do not thicken chrome")
    if "H * 0.78" in hud or "Impact" in hud or "RAISE YOUR HAND" in hud:
        _fail("SEEKING chip hides the gun")
    mode_at = hud.find("drawModeChip")
    hangar_at = hud.find("hangarHudChip")
    room_at = hud.find("roomHudChip")
    seek_at = hud.find("seekingHudChip")
    if mode_at < 0 or hangar_at < 0 or room_at < 0 or seek_at < 0:
        _fail("SEEKING chip must stay additive with PAD/GUN + WAIT + ROOM")
    if mode_at > hangar_at or hangar_at > room_at or room_at > seek_at:
        _fail("SEEKING chip wiped PAD/GUN or hangar / ROOM chips")
    fire = _js_fn(js, "fire")
    if "seekingHudChip" in fire:
        _fail("fire() gated on SEEKING chip — Fire = AimBus HID peek")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")


def test_mag_chip_hand_path() -> None:
    """Thin MAG / DRY after CONF on hand/GUN. Never invent under DESKTOP."""
    js = proto_js()
    chip = _js_fn(js, "drawModeChip")
    if '"MAG "' not in chip and '"MAG " +' not in chip and "MAG " not in chip:
        _fail("MAG chip missing on hand/GUN path — drawModeChip must paint MAG n")
    if '"DRY"' not in chip:
        _fail("MAG chip must paint rust DRY at 0")
    if "S.mag" not in chip:
        _fail("MAG chip must track S.mag — reload honesty")
    mag_gate = re.search(r"if\s*\(\s*!S\.desktop\s*\)\s*\{([\s\S]+)", chip)
    if not mag_gate:
        _fail("MAG chip must gate on if (!S.desktop) — HID does not own mag")
    gated = mag_gate.group(1)
    if "MAG " not in gated or '"DRY"' not in gated or "S.mag" not in gated:
        _fail("MAG chip shows under DESKTOP — paint only inside if (!S.desktop)")
    if "fillRect(mx, 16," not in chip and "fillRect(mx,16," not in chip:
        _fail("MAG chip left the 22px MODE row")
    if ", 22)" not in chip and ",22)" not in chip:
        _fail("MAG chip must stay 22px — do not thicken the bar")
    if "Locker.colors.rust" not in chip:
        _fail("DRY must be rust")
    if "Locker.colors.mint" not in chip and "Locker.colors.bone" not in chip:
        _fail("MAG n must stay bone/mint")
    if "shadowBlur" in chip or "glow" in chip.lower():
        _fail("MAG chip bloomed")
    if "H * 0.78" in chip or "Impact" in chip or "RAISE YOUR HAND" in chip:
        _fail("MAG chip hides the cuff or grew a tutorial wall")
    if "aimBus" in chip or "fire(" in chip or "AimSample" in chip:
        _fail("MAG chip gated fire / touched AimSample")
    if "S.desktop = true" in chip or "armPracticeDesktop" in chip:
        _fail("drawModeChip must not arm DESKTOP")
    label = re.search(r"const label = ([^;]+);", chip)
    if not label:
        _fail("drawModeChip lost the MODE label")
    cond = label.group(1)
    seek_at = cond.find('"SEEKING"')
    if seek_at < 0:
        _fail("drawModeChip must still paint SEEKING when not forceGun / GUN")
    if "S.forceGun" not in cond[:seek_at]:
        _fail("drawModeChip prefers SEEKING on Space forceGun — MODE must match seekingHudChip")
    if 'S.mode !== "GUN"' not in cond[:seek_at] and 'S.mode != "GUN"' not in cond[:seek_at]:
        _fail("drawModeChip prefers SEEKING when S.mode is GUN — MODE must match seekingHudChip")
    hangar = _js_fn(js, "hangarHudChip")
    room = _js_fn(js, "roomHudChip")
    seek = _js_fn(js, "seekingHudChip")
    hud = _js_fn(js, "drawHUD")
    for name, body in (("hangarHudChip", hangar), ("roomHudChip", room), ("seekingHudChip", seek)):
        if "MAG " in body or '"DRY"' in body:
            _fail(f"{name} invented a MAG chip — do not thicken hangar/lobby")
    if '"MAG "' in hud or "MAG " + "S.mag" in hud:
        _fail("drawHUD grew a MAG chip — keep MAG on the MODE row, not the hangar bar")
    if _js_const(js, "SABLE_HUD_H") != 22:
        _fail("SableHUD bar must stay thin (22px)")
    if 'phase === "range"' not in hud or '"SCORE "' not in hud:
        _fail("gallery SCORE must stay range-gated — MAG must not thicken lobby")
    if "H * 0.78" in hud or "Impact" in hud:
        _fail("MAG chip hides the gun")
    css = (ROOT / "proto/style.css").read_text(encoding="utf-8")
    lobby = re.search(r"\.lobby-inner \{([^}]+)\}", css)
    if not lobby or "padding: 24px 16px 40px" not in lobby.group(1):
        _fail("lobby was thickened — MAG must stay on the 22px MODE row")
    if "gap: 12px" not in lobby.group(1):
        _fail("lobby was thickened — action gap grew")
    fire = _js_fn(js, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if "spendGestureRound" not in fire or "missTick" not in fire:
        _fail("empty shark-fin must still dry-click — MAG chip is a tell, not a new verb")
    if re.search(r"if \(!spendGestureRound\(\)\) \{ missTick\(\); return; \}", fire) is None:
        if "if (!spendGestureRound()) { missTick(); return; }" not in fire:
            _fail("empty shark-fin stopped dry-clicking / started firing")
    spend = _js_fn(js, "spendGestureRound")
    if "S.finHeld" not in spend:
        _fail("mag spend is the shark-fin path — empty shark-fin stays missTick")
    if "S.desktop" in spend:
        _fail("spendGestureRound must not invent a DESKTOP mag story")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")


def test_safe_chip_hand_path() -> None:
    """Thin SAFE after CONF (with MAG). Pointing + thumb-parallel honesty."""
    js = proto_js()
    chip = _js_fn(js, "drawModeChip")
    if '"SAFE"' not in chip:
        _fail("SAFE chip missing on hand/GUN path — drawModeChip must paint SAFE")
    if "thumbParallel" not in chip or "indexExtended" not in chip:
        _fail("SAFE show predicate must use thumbParallel + pointing (indexExtended)")
    if "S.handLm" not in chip:
        _fail("SAFE show predicate must read S.handLm")
    desk_gate = re.search(r"if\s*\(\s*!S\.desktop\s*\)\s*\{([\s\S]+)", chip)
    if not desk_gate:
        _fail("SAFE chip must gate on if (!S.desktop) — HID does not own SAFE")
    gated = desk_gate.group(1)
    if '"SAFE"' not in gated:
        _fail("SAFE chip shows under DESKTOP — paint only inside if (!S.desktop)")
    if "thumbParallel" not in gated or "indexExtended" not in gated or "S.handLm" not in gated:
        _fail("SAFE show predicate must live on the hand path — thumbParallel + indexExtended(S.handLm)")
    if "fillRect(sx, 16," not in chip and "fillRect(sx,16," not in chip:
        _fail("SAFE chip left the 22px MODE row")
    if ", 22)" not in chip and ",22)" not in chip:
        _fail("SAFE chip must stay 22px — do not thicken the bar")
    if "Locker.colors.mint" not in chip or "Locker.colors.bone" not in chip:
        _fail("SAFE must stay bone/mint charcoal plate")
    if "shadowBlur" in chip or "glow" in chip.lower():
        _fail("SAFE chip bloomed")
    if "H * 0.78" in chip or "Impact" in chip or "RAISE YOUR HAND" in chip:
        _fail("SAFE chip hides the cuff or grew a tutorial wall")
    if "aimBus" in chip or "fire(" in chip or "AimSample" in chip:
        _fail("SAFE chip gated fire / touched AimSample")
    if "S.desktop = true" in chip or "armPracticeDesktop" in chip:
        _fail("drawModeChip must not arm DESKTOP")
    if 'S.mode = "SAFE"' in chip or 'label = "SAFE"' in chip:
        _fail("do not rename S.mode → SAFE — additive tell only")
    label = re.search(r"const label = ([^;]+);", chip)
    if not label:
        _fail("drawModeChip lost the MODE label")
    cond = label.group(1)
    if '"SAFE"' in cond:
        _fail("drawModeChip renamed MODE to SAFE — fights GUN lift / SEEKING / forceGun")
    seek_at = cond.find('"SEEKING"')
    if seek_at < 0:
        _fail("drawModeChip must still paint SEEKING when not forceGun / GUN")
    if "S.forceGun" not in cond[:seek_at]:
        _fail("drawModeChip prefers SEEKING on Space forceGun — MODE must match seekingHudChip")
    if 'S.mode !== "GUN"' not in cond[:seek_at] and 'S.mode != "GUN"' not in cond[:seek_at]:
        _fail("drawModeChip prefers SEEKING when S.mode is GUN — MODE must match seekingHudChip")
    hangar = _js_fn(js, "hangarHudChip")
    room = _js_fn(js, "roomHudChip")
    seek = _js_fn(js, "seekingHudChip")
    hud = _js_fn(js, "drawHUD")
    for name, body in (("hangarHudChip", hangar), ("roomHudChip", room), ("seekingHudChip", seek)):
        if '"SAFE"' in body or "SAFE" in body:
            _fail(f"{name} invented a SAFE chip — do not thicken hangar/lobby")
    if '"SAFE"' in hud:
        _fail("drawHUD grew a SAFE chip — keep SAFE on the MODE row, not the hangar bar")
    if _js_const(js, "SABLE_HUD_H") != 22:
        _fail("SableHUD bar must stay thin (22px)")
    if 'phase === "range"' not in hud or '"SCORE "' not in hud:
        _fail("gallery SCORE must stay range-gated — SAFE must not thicken lobby")
    if "H * 0.78" in hud or "Impact" in hud:
        _fail("SAFE chip hides the gun")
    css = (ROOT / "proto/style.css").read_text(encoding="utf-8")
    lobby = re.search(r"\.lobby-inner \{([^}]+)\}", css)
    if not lobby or "padding: 24px 16px 40px" not in lobby.group(1):
        _fail("lobby was thickened — SAFE must stay on the 22px MODE row")
    if "gap: 12px" not in lobby.group(1):
        _fail("lobby was thickened — action gap grew")
    fire = _js_fn(js, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if "spendGestureRound" not in fire or "missTick" not in fire:
        _fail("empty shark-fin must still dry-click — SAFE chip is a tell, not a new verb")
    spend = _js_fn(js, "spendGestureRound")
    if "S.finHeld" not in spend:
        _fail("mag spend is the shark-fin path — empty shark-fin stays missTick")
    if "S.desktop" in spend:
        _fail("spendGestureRound must not invent a DESKTOP mag story")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")
    gate = _js_fn(js, "productGunHidFire")
    if "return false" not in gate:
        _fail("productGunHidFire must stay false")
    if "fire(" in gate:
        _fail("productGunHidFire must not peek — it only answers the gate")


def test_engine_chips_are_hands_and_mojo() -> None:
    """MODE-row engine chips: HANDS + MOJO. GEMINI / GEMINI OFF is retired."""
    js = proto_js()
    chip = _js_fn(js, "drawModeChip")
    if re.search(r"\bGEMINI(\s+OFF)?\b", chip) or re.search(r"gemini", chip, re.I):
        _fail(
            "drawModeChip must not paint GEMINI / GEMINI OFF as product engine status — "
            "Hands-class + Mojo are the live engine tells"
        )
    if "S.engine.gemini" in js:
        _fail("S.engine.gemini is dead — do not wire a Gemini engine into HUD")
    if '"HANDS"' not in chip or "HANDS OFF" not in chip:
        _fail("drawModeChip must still paint HANDS / HANDS OFF")
    if "MOJO 1.0" not in chip or "MOJO OFF" not in chip:
        _fail("drawModeChip must still paint MOJO 1.0 / MOJO OFF")
    if "S.engine.hands" not in chip or "S.engine.mojo" not in chip:
        _fail("engine chips must read S.engine.hands / S.engine.mojo")
    hud = _js_fn(js, "drawHUD")
    if "GEMINI" in hud or "gemini" in hud.lower():
        _fail("drawHUD must not invent a GEMINI engine chip")
    if _js_const(js, "SABLE_HUD_H") != 22:
        _fail("SableHUD bar must stay thin (22px)")


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
    if "Q4 fail-to-lock is SEEKING until lock or Space" not in modes:
        _fail("docs/modes.md must name the Q4 SEEKING chip")
    if "Q4 fail-to-lock is SEEKING until lock or Space" not in bible:
        _fail("PRODUCTION.md must name the Q4 SEEKING chip")
    mode_lock = '`drawModeChip` does not prefer SEEKING when `S.forceGun` or `S.mode === "GUN"`'
    if mode_lock not in modes:
        _fail("docs/modes.md must lock drawModeChip forceGun / GUN over SEEKING")
    if mode_lock not in bible:
        _fail("PRODUCTION.md must lock drawModeChip forceGun / GUN over SEEKING")
    if "test_sablehud.py" not in bible:
        _fail("PRODUCTION.md must fail loud through test_sablehud.py")
    if "ROOM" not in bible or "wait_practice" not in bible:
        _fail("PRODUCTION.md must name the thin ROOM chip on wait_practice")
    if "ROOM chip hides the gun" not in bible:
        _fail("PRODUCTION.md must fail loud if a ROOM chip hides the gun / thickens the lobby")
    if "v0.20.0" not in bible:
        _fail("PRODUCTION.md must stand v0.20.0 until Build tags this gallery HUD tip")
    if "mag tell = reload honesty" not in modes.lower() and "Mag tell = reload honesty" not in modes:
        _fail("docs/modes.md must lock mag tell = reload honesty")
    if "do not invent a pad mag story" not in modes.lower() and "Do not invent MAG under DESKTOP" not in modes:
        _fail("docs/modes.md must refuse a DESKTOP / pad mag story")
    if "empty shark-fin stays missTick" not in modes.lower() and "Empty shark-fin stays missTick" not in modes:
        _fail("docs/modes.md must keep empty shark-fin on missTick")
    if "mag tell = reload honesty" not in bible and "Mag tell = reload honesty" not in bible:
        _fail("PRODUCTION.md must lock mag tell = reload honesty")
    if "do not invent a pad mag story" not in bible.lower():
        _fail("PRODUCTION.md must refuse a DESKTOP / forceGun pad mag story")
    if "empty shark-fin stays" not in bible.lower():
        _fail("PRODUCTION.md must keep empty shark-fin on missTick")
    if "SAFE tell = thumb-parallel honesty" not in bible:
        _fail("PRODUCTION.md must lock SAFE tell = thumb-parallel honesty")
    if "SAFE tell = thumb-parallel honesty" not in modes:
        _fail("docs/modes.md must lock SAFE tell = thumb-parallel honesty")


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
        test_q4_seeking_chip_thin()
        test_mag_chip_hand_path()
        test_safe_chip_hand_path()
        test_engine_chips_are_hands_and_mojo()
        test_docs_lock()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("sablehud lock ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
