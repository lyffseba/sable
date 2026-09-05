#!/usr/bin/env python3
"""SableLobby lock: waiting arena is HUD-on-Yard always-practice.

Fail loud if Bay reappears on player chrome, Offline / WARM UP lose
one-click local practice, ENTER RANGE stops being host shared gallery
start, promote traps HID behind calib/lock or a lobby POST, hangar
chips thicken the lobby or hide the gun, a ROOM chip hides the gun
or thickens the lobby, or the lobby becomes a match-start screen again.
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
    if "hangarHudChip" not in hud:
        _fail("waiting arena lost hangar chips from S.hangar")
    if "roomHudChip" not in hud:
        _fail("waiting arena lost the thin ROOM chip")
    mode_at = hud.find("drawModeChip")
    hangar_at = hud.find("hangarHudChip")
    room_at = hud.find("roomHudChip")
    if mode_at < 0 or hangar_at < 0 or mode_at > hangar_at:
        _fail("hangar chips wiped PAD/GUN — mode chip must stay live")
    if room_at < 0 or hangar_at > room_at:
        _fail("ROOM chip must stay additive with WAIT — do not hide the gun")
    if '"SCORE "' not in hud or ('"ROUND "' not in hud and '"ROUND"' not in hud):
        _fail("RANGE clock/score left drawHUD — hangar chips must not unpin gallery")
    if "H * 0.78" in hud or "H*0.78" in hud or "H * 0.5" in hud or "Impact" in hud:
        _fail("hangar chips hide the gun")
    if "RAISE YOUR HAND" in hud or "ESC = miss" in hud:
        _fail("hangar chips grew a tutorial wall over the waiting Yard")
    chip = _js_fn(js, "hangarHudChip")
    if "S.hangar" not in chip or '"WAIT"' not in chip:
        _fail("waiting-arena WAIT chip must read S.hangar")
    if re.search(r"\bphase\b", chip):
        _fail("hangar chips must not rename screen phases")
    if "aimBus" in chip or "fire(" in chip:
        _fail("hangar chips gated fire — gun never gates on hangar")
    d2 = _js_fn(js, "draw2D")
    lobby_draw = d2[d2.find('phase === "lobby"') :]
    if not lobby_draw or "drawHUD" not in lobby_draw:
        _fail("waiting arena must paint hangar chips on the thin SableHUD bar")
    xh = lobby_draw.find("drawCrosshair")
    chips = lobby_draw.find("drawHUD")
    if xh < 0 or chips < 0 or xh > chips:
        _fail("waiting-arena chips must not paint over the cuff/reticle")


def test_enter_range_stays_shared() -> None:
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    js = proto_js()
    if 'id="btn-lobby-range"' not in html or "ENTER RANGE" not in html:
        _fail("lobby lost ENTER RANGE")
    start = _js_fn(js, "lobbyStartRange")
    if "enterRangePreserve()" not in start:
        _fail("ENTER RANGE no longer phase-preserves the live Yard")
    if "/api/lobby/start" not in start:
        _fail("host ENTER RANGE no longer shares the house")
    if re.search(r"await\s+", start) or "async function lobbyStartRange" in js:
        _fail("ENTER RANGE awaits net — lift/HID is behind the lobby POST")
    if "resetLockState" in start or 'setPhase("lock")' in start or "goCalib" in start:
        _fail("ENTER RANGE forced calib/lock — warm-up feel died")
    if 'play("bay")' in start or 'setPhase("bay")' in start:
        _fail("ENTER RANGE dropped into Bay")
    if "S.waitingYard = false" not in start:
        _fail("ENTER RANGE must leave waiting-arena practice before the share")
    if "lobbyPost(\"/api/lobby/start\")" not in start and "lobbyPost('/api/lobby/start')" not in start:
        _fail("host ENTER RANGE must fire-and-forget /api/lobby/start")
    preserve = _js_fn(js, "enterRangePreserve")
    if "clearRect" in preserve or "drawHUD" in preserve:
        _fail("promote WAIT→LIVE wiped the HUD")
    if "alreadyLifted()" not in preserve:
        _fail("phase-preserve must skip calib when already lifted")
    if 'phase === "lobby"' not in preserve or 'phase === "range"' not in preserve:
        _fail("phase-preserve must keep the live Yard the room is already on")
    if 'setPhase("range")' not in preserve:
        _fail("already-live ENTER RANGE must stay on the Yard")
    if 'play("range")' not in preserve:
        _fail("cold ENTER RANGE must still play(range)")
    if "resetLockState" in preserve or 'setPhase("lock")' in preserve or "goCalib" in preserve:
        _fail("phase-preserve reset lock — calib/lock trap")
    if re.search(r"await\s+", preserve) or "fetch(" in preserve:
        _fail("phase-preserve awaits — HID trap")
    if 'play("bay")' in preserve or 'setPhase("bay")' in preserve:
        _fail("phase-preserve dropped into Bay")
    lifted = _js_fn(js, "alreadyLifted")
    if "camReady" not in lifted or "S.smooth" not in lifted or "S.tpl" not in lifted:
        _fail("alreadyLifted must keep the live tracking predicate")
    if "resetLockState" in lifted:
        _fail("alreadyLifted must not reset lock")
    poll = _js_fn(js, "lobbyPoll")
    if "enterRangePreserve()" not in poll:
        _fail("guest promote must phase-preserve the live Yard")
    if re.search(r'phase === "lobby"\) play\("range"\)', poll):
        _fail("guest promote still forces play(range) from the waiting Yard")
    fire = _js_fn(js, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if re.search(r"await\s+", fire):
        _fail("fire() awaits — promote trapped HID")


def test_hangar_phase_enum() -> None:
    """Waiting-practice vs shared gallery must not live on lobby/range alone."""
    js = proto_js()
    lobby_py = (ROOT / "tools/lobby.py").read_text(encoding="utf-8")
    if 'hangar: "hangar"' not in js:
        _fail("S.hangar default missing — hangar session must boot hangar")
    if 'HANGAR_PHASES = ["hangar", "wait_practice", "match_live"]' not in js:
        _fail("HANGAR_PHASES must stay hangar | wait_practice | match_live")
    assign = _js_fn(js, "assignHangar")
    if "unknown hangar phase" not in assign:
        _fail("assignHangar must fail loud on an unknown hangar phase")
    if re.search(r"await\s+", assign) or "fetch(" in assign:
        _fail("assignHangar awaits — hangar write trapped HID")
    if "aimBus" in assign or "fire(" in assign:
        _fail("assignHangar touched AimBus / fire — hangar is not a fire gate")
    sync = _js_fn(js, "syncHangar")
    if 'assignHangar("hangar")' not in sync:
        _fail("syncHangar(boot/offline range) must write hangar")
    if 'assignHangar("wait_practice")' not in sync:
        _fail("syncHangar(lobby / warmup) must write wait_practice")
    if 'assignHangar("match_live")' not in sync:
        _fail("syncHangar(shared range) must write match_live")
    if re.search(r"await\s+", sync) or "fetch(" in sync:
        _fail("syncHangar awaits — lift/HID would wait on a phase write")
    if "aimBus" in sync or "fire(" in sync:
        _fail("syncHangar touched AimBus / fire")
    phase = _js_fn(js, "setPhase")
    if "syncHangar(next)" not in phase:
        _fail("setPhase must sync hangar — screen phase is not the session enum")
    wait = _js_fn(js, "startWaitingYard")
    if 'assignHangar("wait_practice")' not in wait:
        _fail("startWaitingYard must mark wait_practice")
    warm = _js_fn(js, "lobbyWarmup")
    if 'assignHangar("wait_practice")' not in warm:
        _fail("WARM UP must mark wait_practice before the Yard drop")
    preserve = _js_fn(js, "enterRangePreserve")
    if 'assignHangar("match_live")' not in preserve:
        _fail("ENTER RANGE phase-preserve must mark match_live")
    if 'phase === "lobby"' not in preserve or 'phase === "range"' not in preserve:
        _fail("phase-preserve must still keep the live Yard the room is already on")
    start_range = _js_fn(js, "startRange")
    if 'assignHangar("hangar")' not in start_range:
        _fail("Offline startRange must mark hangar")
    if 'assignHangar("wait_practice")' not in start_range:
        _fail("WARM UP startRange must mark wait_practice")
    if 'assignHangar("match_live")' not in start_range:
        _fail("shared startRange must mark match_live")
    poll = _js_fn(js, "lobbyPoll")
    if 'assignHangar("match_live")' not in poll:
        _fail("guest promote must mark match_live without waiting on hangar")
    fire = _js_fn(js, "fire")
    if "assignHangar" in fire or "syncHangar" in fire or "S.hangar" in fire:
        _fail("fire() must not gate on hangar — Fire = AimBus HID peek")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    offline = re.search(
        r'\$\("btn-play"\)\.addEventListener\("click", \(\) => \{[\s\S]*?play\("range"\)',
        js,
    )
    if not offline or 'assignHangar("hangar")' not in offline.group(0):
        _fail("OFFLINE must mark hangar in one click")
    if "def hangar_for_phase" not in lobby_py:
        _fail("server must own hangar_for_phase — wait/range map onto hangar")
    if "def _hangar_view" not in lobby_py or '"hangar": _hangar_view(room)' not in lobby_py:
        _fail("room snapshot must be a view of the room-owned hangar enum")
    if "unknown room phase" not in lobby_py:
        _fail("hangar_for_phase must fail loud on an unknown room phase")
    if "only ENTER RANGE promotes hangar" not in lobby_py:
        _fail("start() must be the only hangar promote to match_live")
    if "Practice never promotes hangar" not in lobby_py:
        _fail("warmup must never promote hangar")
    if '"phase": "wait"' not in lobby_py:
        _fail("server room phase must stay wait | range | bay")
    apply = _js_fn(js, "applyRoomHangar")
    if "data.hangar" not in apply:
        _fail("applyRoomHangar must write S.hangar from the room snapshot")
    if "room snapshot missing hangar" not in apply:
        _fail("applyRoomHangar must fail loud when the snapshot omits hangar")
    if re.search(r"await\s+", apply) or "fetch(" in apply:
        _fail("applyRoomHangar awaits — hangar wire trapped HID")
    if "aimBus" in apply or "fire(" in apply:
        _fail("applyRoomHangar touched AimBus / fire — hangar is not a fire gate")
    paint = _js_fn(js, "paintLobby")
    if "applyRoomHangar(data)" not in paint:
        _fail("paintLobby must apply room-owned hangar")
    if "!S.warmup" not in paint:
        _fail("paintLobby must not wire-gate WARM UP on hangar")
    if "applyRoomHangar(data)" not in poll:
        _fail("lobbyPoll must apply room-owned hangar")
    if "applyRoomHangar" in fire:
        _fail("fire() gated on applyRoomHangar — Fire = AimBus HID peek")


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
    if "enterRangePreserve" not in bible:
        _fail("PRODUCTION.md must name ENTER RANGE phase-preserve")
    if "phase-preserve" not in modes and "already lifted" not in modes:
        _fail("docs/modes.md must name ENTER RANGE phase-preserve")
    if "wait_practice" not in modes or "match_live" not in modes or "S.hangar" not in modes:
        _fail("docs/modes.md must name the durable hangar session enum")
    if "room snapshot owns hangar" not in modes and "owns hangar" not in modes:
        _fail("docs/modes.md must note the room snapshot owns hangar")
    if "S.hangar" not in bible or "wait_practice" not in bible or "match_live" not in bible:
        _fail("PRODUCTION.md must name the durable hangar session enum")
    if "owns hangar" not in bible and "SableNet hangar lock" not in bible:
        _fail("PRODUCTION.md must note the room snapshot owns hangar")
    if "SableNet hangar lock" not in modes:
        _fail("docs/modes.md must name the SableNet hangar lock")
    if "test_hangar_wire.py" not in bible:
        _fail("PRODUCTION.md must fail loud through test_hangar_wire.py")
    if "WAIT" not in modes or "READY" not in modes or "LIVE" not in modes:
        _fail("docs/modes.md must name hangar WAIT / READY / LIVE chips")
    if "WAIT" not in bible or "READY" not in bible or "LIVE" not in bible:
        _fail("PRODUCTION.md must name hangar WAIT / READY / LIVE chips")
    if "hangar chips thicken the lobby" not in bible:
        _fail("PRODUCTION.md must fail loud if hangar chips thicken the lobby / hide the gun")
    if "ROOM" not in modes or "wait_practice" not in modes:
        _fail("docs/modes.md must name the thin ROOM chip on wait_practice")
    if "Do not hide the gun with a ROOM chip" not in modes:
        _fail("docs/modes.md must fail loud if a ROOM chip hides the gun")
    if "ROOM" not in bible or "ROOM chip hides the gun" not in bible:
        _fail("PRODUCTION.md must fail loud if a ROOM chip hides the gun / thickens the lobby")
    ci = (ROOT / "tools/ci.sh").read_text(encoding="utf-8")
    if "test_sablelobby.py" not in ci:
        _fail("ci.sh must run the SableLobby always-practice gate")


def test_room_chip_thin() -> None:
    js = proto_js()
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    css = (ROOT / "proto/style.css").read_text(encoding="utf-8")
    chip = _js_fn(js, "roomHudChip")
    if "S.hangar" not in chip or "S.room" not in chip:
        _fail("ROOM chip must read S.hangar + S.room")
    if "wait_practice" not in chip or '"ROOM  "' not in chip:
        _fail("wait_practice must paint a thin ROOM code chip")
    if re.search(r"\bphase\b", chip):
        _fail("ROOM chip must not rename screen phases")
    if "aimBus" in chip or "fire(" in chip or "AimSample" in chip:
        _fail("ROOM chip gated fire — gun never gates on room")
    if re.search(r"await\s+", chip) or "fetch(" in chip:
        _fail("ROOM chip awaits — HUD trapped HID")
    if "H * 0.78" in chip or "H*0.78" in chip or "Impact" in chip:
        _fail("ROOM chip hides the gun")
    hud = _js_fn(js, "drawHUD")
    if "roomHudChip" not in hud or "drawSableChip" not in hud:
        _fail("ROOM chip left the thin SableHUD bar")
    if 'phase !== "range"' not in hud:
        _fail("SableHUD must not thicken the waiting arena with gallery chips")
    if '"SCORE "' not in hud or ('"ROUND "' not in hud and '"ROUND"' not in hud):
        _fail("RANGE clock/score left drawHUD — ROOM must not unpin gallery")
    if "H * 0.78" in hud or "H*0.78" in hud or "H * 0.5" in hud or "Impact" in hud:
        _fail("ROOM chip hides the gun")
    lobby = re.search(r"\.lobby-inner \{([^}]+)\}", css)
    if not lobby or "padding: 24px 16px 40px" not in lobby.group(1):
        _fail("lobby was thickened — ROOM chip must stay on the 22px bar")
    if "gap: 12px" not in lobby.group(1):
        _fail("lobby was thickened — action gap grew")
    if 'id="lobby-room"' not in html or "ROOM ———" not in html:
        _fail("lobby overlay lost ROOM — HUD chip is additive")
    if 'id="btn-play"' not in html or ">OFFLINE<" not in html:
        _fail("boot lost one-click OFFLINE")
    if 'id="btn-lobby-warmup"' not in html or "WARM UP" not in html:
        _fail("lobby lost WARM UP")
    fire = _js_fn(js, "fire")
    if "roomHudChip" in fire:
        _fail("fire() gated on ROOM chip — Fire = AimBus HID peek")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")
    if "if (roomChip) chips.push(roomChip)" not in hud:
        _fail("ROOM chip must stay additive with WAIT / READY / LIVE")
    if re.search(r'if \(phase === "range"\).*roomChip', hud):
        _fail("ROOM chip must not be RANGE-gated — wait_practice lobby must see it")
    if 'if (phase === "range") chips.push(["SCORE "' not in hud:
        _fail("RANGE SCORE left the range gate — RANGE must stay pinned")
    if 'if (phase === "range") chips.push(["ROUND "' not in hud:
        _fail("RANGE ROUND left the range gate — RANGE must stay pinned")
    mode_at = hud.find("drawModeChip")
    if mode_at < 0 or mode_at > hud.find("roomHudChip"):
        _fail("ROOM chip wiped PAD/GUN — mode chip must stay live")
    if "clearRect" in hud or "shadowBlur" in hud or "glow" in hud.lower():
        _fail("ROOM chip bloomed or wiped the bar")
    if "H * 0.78" in hud or "Impact" in hud:
        _fail("ROOM chip over cuff/reticle")


def main() -> int:
    try:
        test_no_bay_entry()
        test_offline_and_warmup_one_click()
        test_waiting_arena_always_practice()
        test_enter_range_stays_shared()
        test_hangar_phase_enum()
        test_aimsample_and_docs()
        test_room_chip_thin()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("sablelobby lock ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
