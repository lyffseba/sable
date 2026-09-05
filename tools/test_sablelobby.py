#!/usr/bin/env python3
"""SableLobby lock: waiting arena is HUD-on-Yard always-practice.

Fail loud if Bay reappears on player chrome, Offline / WARM UP lose
one-click local practice, ENTER RANGE stops being host shared gallery
start, or the lobby becomes a match-start screen again.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402


def _fail(msg: str) -> None:
    raise AssertionError(f"SABLELOBBY FAIL: {msg}")


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"(?:async )?function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        _fail(f"missing function {name}")
    return m.group(0)


def test_no_bay_entry() -> None:
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    js = proto_js()
    if 'id="btn-bay"' in html or re.search(r">\s*BAY\s*<", html):
        _fail("boot still offers BAY — Yard is the sole active map")
    if 'id="btn-lobby-bay"' in html or "ENTER BAY" in html:
        _fail("lobby still offers ENTER BAY — Bay is parked")
    boot_bay = re.search(r'\$\("btn-bay"\)[\s\S]{0,220}?play\("bay"\)', js)
    if boot_bay:
        _fail("boot still wires BAY — soft-park must hide the player entry")
    if re.search(r'lobbyStartBay\(\)', _js_fn(js, "paintLobby")):
        _fail("lobby chrome reintroduced Bay")


def test_offline_and_warmup_one_click() -> None:
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
    if "S.waitingYard = false" not in offline.group(0):
        _fail("OFFLINE must leave waiting-arena practice")
    if 'play("bay")' in offline.group(0):
        _fail("OFFLINE was rerouted into Bay")
    if 'id="btn-lobby-warmup"' not in html or "WARM UP" not in html:
        _fail("lobby lost WARM UP")
    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/start" in warm:
        _fail("WARM UP started the shared house")
    if re.search(r"await\s+", warm):
        _fail("WARM UP awaits net — not one-click local practice")
    if re.search(r"setTimeout|stepSim|simAcc", warm):
        _fail("WARM UP grew a tick tax")
    if 'setPhase("range")' not in warm and 'play("range")' not in warm:
        _fail("WARM UP no longer drops into Range")
    if 'play("bay")' in warm or 'setPhase("bay")' in warm:
        _fail("WARM UP dropped into Bay")
    if "/api/lobby/leave" in warm:
        _fail("WARM UP must not leave the room")


def test_waiting_arena_always_practice() -> None:
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    css = (ROOT / "proto/style.css").read_text(encoding="utf-8")
    js = proto_js()
    if 'id="screen-lobby"' not in html or "screen-pass" not in html:
        _fail("waiting arena must stay HUD-on-Yard (screen-pass), not a blocking screen")
    wait = _js_fn(js, "startWaitingYard")
    if re.search(r"await\s+", wait) or "fetch(" in wait or "/api/lobby" in wait:
        _fail("waiting-arena practice awaits net — lift/HID would trap")
    if "/api/lobby/start" in wait:
        _fail("waiting-arena practice started the shared house")
    if "S.waitingYard = true" not in wait:
        _fail("startWaitingYard must mark local waiting practice")
    if "0.2" not in wait or "-6.6" not in wait:
        _fail("waiting-arena first plate left the Yard pad")
    if 'play("bay")' in wait or 'setPhase("bay")' in wait:
        _fail("waiting-arena practice dropped into Bay")
    phase = _js_fn(js, "setPhase")
    if "startWaitingYard()" not in phase:
        _fail("setPhase(lobby) must arm Yard always-practice")
    if 'next === "lobby"' not in phase:
        _fail("setPhase must keep the Yard live on lobby")
    match = _js_fn(js, "sharedMatch")
    if "!S.warmup" not in match or "!S.waitingYard" not in match:
        _fail("sharedMatch must exclude WARM UP and waiting-arena practice")
    ranged = _js_fn(js, "updateRange")
    if "galleryOver" not in ranged or 'setPhase("results")' not in ranged:
        _fail("scored gallery must still end through galleryOver")
    if "waitingYard" not in ranged:
        _fail("waiting-arena practice must not take the 60s lock")
    fire = _js_fn(js, "fire")
    if 'phase !== "lobby"' not in fire and 'phase === "lobby"' not in fire:
        _fail("HID fire must peek on the waiting Yard")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if re.search(r"await\s+", fire):
        _fail("fire() awaits — HUD-on-Yard trapped HID")
    step = _js_fn(js, "stepSim")
    if 'phase === "lobby"' not in step or "updateRange(SIM_DT" not in step:
        _fail("waiting-arena plates must tick on the 128 Hz sim")
    if 'id="screen-lobby" class="screen screen-pass"' not in html:
        _fail("screen-lobby must be screen-pass HUD-on-Yard")
    if "pointer-events: none" not in css or "#screen-lobby.screen-pass .lobby-inner" not in css:
        _fail("lobby overlay must let HID reach the Yard")
    lobby = re.search(r"\.lobby-inner \{([^}]+)\}", css)
    if not lobby or "padding: 24px 16px 40px" not in lobby.group(1):
        _fail("lobby was thickened")
    if "gap: 12px" not in lobby.group(1):
        _fail("lobby was thickened — action gap grew")
    inner = re.search(
        r'<div class="lobby-inner">([\s\S]*?)</div>\s*</div>\s*<div id="screen-range"',
        html,
    )
    if not inner:
        _fail("lobby-inner markup missing")
    body = inner.group(1)
    if "SCORE" in body or "ROUND" in body or "SableHUD" in body:
        _fail("lobby grew gallery HUD chips")
    if "WARM UP" not in body or "ENTER RANGE" not in body or "LEAVE" not in body:
        _fail("hangar lost a Yard path")
    if "ENTER BAY" in body or 'id="btn-lobby-bay"' in body:
        _fail("lobby chrome still offers ENTER BAY — Bay is parked")
    hud = _js_fn(js, "drawHUD")
    if 'phase !== "range"' not in hud:
        _fail("SableHUD must not thicken the waiting arena with gallery chips")


def test_enter_range_stays_shared() -> None:
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    js = proto_js()
    if 'id="btn-lobby-range"' not in html or "ENTER RANGE" not in html:
        _fail("lobby lost ENTER RANGE")
    start = _js_fn(js, "lobbyStartRange")
    if 'play("range")' not in start:
        _fail("ENTER RANGE no longer starts the Salt House")
    if "/api/lobby/start" not in start:
        _fail("host ENTER RANGE no longer shares the house")
    if 'play("bay")' in start or 'setPhase("bay")' in start:
        _fail("ENTER RANGE dropped into Bay")
    if "S.waitingYard = false" not in start:
        _fail("ENTER RANGE must leave waiting-arena practice before the share")


def test_aimsample_and_docs() -> None:
    js = proto_js()
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")
    modes = (ROOT / "docs/modes.md").read_text(encoding="utf-8")
    if "HUD-on-Yard" not in modes or "always-practice" not in modes:
        _fail("docs/modes.md must name HUD-on-Yard always-practice")
    if "Do not thicken the lobby" not in modes and "thicken the lobby" not in modes:
        _fail("docs/modes.md must refuse a thicker lobby")
    bible = (ROOT / "docs/PRODUCTION.md").read_text(encoding="utf-8")
    if "test_sablelobby.py" not in bible:
        _fail("PRODUCTION.md must fail loud through test_sablelobby.py")
    if "startWaitingYard" not in bible:
        _fail("PRODUCTION.md must name waiting-arena always-practice")
    ci = (ROOT / "tools/ci.sh").read_text(encoding="utf-8")
    if "test_sablelobby.py" not in ci:
        _fail("ci.sh must run the SableLobby always-practice gate")


def main() -> int:
    try:
        test_no_bay_entry()
        test_offline_and_warmup_one_click()
        test_waiting_arena_always_practice()
        test_enter_range_stays_shared()
        test_aimsample_and_docs()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("sablelobby lock ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
