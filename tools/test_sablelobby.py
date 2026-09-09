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
    if "alreadyLifted()" not in warm:
        _fail("WARM UP must phase-preserve when already lifted")
    if 'phase === "lobby"' not in warm or 'phase === "range"' not in warm:
        _fail("WARM UP must keep the live Yard — do not play() lock from lobby")
    if 'setPhase("range")' not in warm:
        _fail("already-live WARM UP must stay on the Yard")
    if 'play("range")' not in warm:
        _fail("cold WARM UP must still play(range)")
    if "resetLockState" in warm or 'setPhase("lock")' in warm or "goCalib" in warm:
        _fail("WARM UP forced calib/lock — waiting-Yard gun died")
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
    if "armPracticeCam()" not in phase:
        _fail("setPhase(lobby) must arm the waiting-Yard gun")
    if 'next === "lobby"' not in phase:
        _fail("setPhase must keep the Yard live on lobby")
    arm = _js_fn(js, "armPracticeCam")
    if "enableCamera" not in arm or "armVideoTrack" not in arm:
        _fail("waiting Yard must arm cam + Hands without lock")
    if "armPracticeDesktop()" not in arm:
        _fail("waiting Yard camera deny must arm desktop on the live lobby")
    if re.search(r"await\s+", arm) or "async function armPracticeCam" in js:
        _fail("armPracticeCam awaits — waiting Yard trapped lift/HID")
    if 'setPhase("lock")' in arm or "goCalib" in arm or "resetLockState" in arm:
        _fail("waiting Yard cam arm forced lock/calib")
    if "goDesktopRange(" in arm or "enterGame(" in arm:
        _fail("camera deny dumped lobby through goDesktopRange")
    if "play(" in arm:
        _fail("waiting Yard cam arm routed through play() lock tax")
    if re.search(r"\bfetch\s*\(", arm) or "/api/lobby" in arm:
        _fail("waiting Yard cam arm talks to the room")
    if "aimBus" in arm or "fire(" in arm:
        _fail("cam arm gated fire — gun never waits on getUserMedia")
    desk = _js_fn(js, "armPracticeDesktop")
    if "S.desktop = true" not in desk or 'S.mode = "DESKTOP"' not in desk:
        _fail("camera deny must keep a desktop peek on the waiting Yard")
    if "camReady" not in desk:
        _fail("armPracticeDesktop must not steal a live camera")
    if "updateMode(" not in desk:
        _fail("armPracticeDesktop must write updateMode DESKTOP truth immediately")
    if "afterLiftState()" not in desk:
        _fail("armPracticeDesktop must invoke afterLiftState after writing DESKTOP truth")
    if desk.find("updateMode(") > desk.find("afterLiftState()"):
        _fail("afterLiftState must run after updateMode writes DESKTOP truth")
    if "if (camReady) return" in desk and desk.find("if (camReady) return") > desk.find("updateMode("):
        _fail("armPracticeDesktop must refuse camReady before writing DESKTOP truth")
    if "goDesktopRange(" in desk or "enterGame(" in desk or 'setPhase("range")' in desk:
        _fail("armPracticeDesktop must stay lobby — do not dump into the 60s gallery")
    if re.search(r"await\s+", desk) or "async function armPracticeDesktop" in js:
        _fail("armPracticeDesktop awaits — waiting Yard trapped lift/HID")
    if "aimBus" in desk or "fire(" in desk:
        _fail("desktop arm gated fire — gun never waits on camera deny")
    frame = _js_fn(js, "frame")
    desk_else = re.search(r"else if \(S\.desktop\) \{([\s\S]*?)\n  \}", frame)
    if not desk_else or "updateMode" not in desk_else.group(1):
        _fail("frame must run updateMode on DESKTOP even if !camReady")
    if "maybePinchFire" in desk_else.group(1) or "runTrack" in desk_else.group(1):
        _fail("!camReady DESKTOP must not pinch or invent a hand track")
    keys = js[js.find('addEventListener("keydown"') : js.find('addEventListener("keyup"')]
    t_block = re.search(
        r'if \(e\.code === "KeyT"\) \{([\s\S]*?)\n  if \(e\.code === "KeyW"\)',
        keys,
    )
    if not t_block:
        _fail("KeyT handler missing")
    t_body = t_block.group(1)
    if 'phase === "lock"' not in t_body or "goDesktopRange()" not in t_body:
        _fail("Offline lock-phase KeyT must stay goDesktopRange")
    if "armPracticeDesktop()" not in t_body:
        _fail("KeyT must re-arm DESKTOP on cam-deny waiting Yard — do not leave a dead gun")
    if "camReady" not in t_body:
        _fail("KeyT re-arm must refuse to steal a live camera")
    if 'phase === "lobby"' not in t_body or "wait_practice" not in t_body:
        _fail("KeyT re-arm is waiting Yard only — lobby / wait_practice")
    if "S.desktop = !S.desktop" not in t_body:
        _fail("KeyT must still toggle DESKTOP off when camReady")
    if t_body.find("armPracticeDesktop()") > t_body.find("S.desktop = !S.desktop"):
        _fail("KeyT must re-arm / no-op before toggle-off on cam-deny waiting Yard")
    if t_body.find("goDesktopRange()") > t_body.find("S.desktop = !S.desktop"):
        _fail("waiting-Yard KeyT must not dump through goDesktopRange")
    if re.search(r"if \(camReady\)[\s\S]{0,80}armPracticeDesktop", t_body):
        _fail("Q4: camReady KeyT must not auto-desktop")
    if "enableCamera" in wait or "armPracticeCam" in wait:
        _fail("startWaitingYard must stay sync — cam arm is fire-and-forget from setPhase")
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
    pinch = _js_fn(js, "maybePinchFire")
    if "fire()" not in pinch:
        _fail("pinch must peek through fire() on the waiting Yard")
    if 'phase === "range"' in pinch or 'phase === "bay"' in pinch:
        _fail("maybePinchFire re-gates the verb — waiting Yard muted pinch")
    if re.search(r"await\s+", fire):
        _fail("fire() awaits — HUD-on-Yard trapped HID")
    if "enableCamera" in fire or "armPracticeCam" in fire or "armPracticeDesktop" in fire or "getUserMedia" in fire:
        _fail("fire() waits on camera arm — shot never waits on a camera")
    after = _js_fn(js, "afterLiftState")
    if 'phase === "lobby"' not in after:
        _fail("waiting-Yard lobby lift skips mint-tell")
    if "mintTell" not in after and "liftMint" not in after:
        _fail("waiting-Yard lobby lift lost the mint-tell chirp")
    if "liftMint" in fire or "mintTell" in fire or "afterLiftState" in fire:
        _fail("mint-tell landed inside fire() — never a fire gate")
    if 'canvasHUD.addEventListener("pointerdown"' in js:
        _fail("waiting-Yard HID lived on muted #hud — window must own the peek")
    if 'window.addEventListener("pointerdown", onHidPointerDown)' not in js:
        _fail("waiting-Yard HID must live on window")
    hid = _js_fn(js, "onHidPointerDown")
    if "hidChromeTarget" not in hid or "fire()" not in hid:
        _fail("window HID must peek fire() and spare WARM UP / ENTER RANGE")
    if 'phase === "lobby"' not in hid:
        _fail("window HID must peek on the waiting Yard")
    if "if (S.desktop) publishAim(e.clientX, e.clientY)" not in hid:
        _fail("waiting-Yard DESKTOP first pad must publish click UV before fire()")
    if hid.find("publishAim") > hid.find("fire()"):
        _fail("waiting-Yard DESKTOP publishAim must land before fire()")
    for m in re.finditer(r"publishAim\s*\(", hid):
        window = hid[max(0, m.start() - 80) : m.start()]
        if "S.desktop" not in window:
            _fail("waiting-Yard HID must not publishAim unless DESKTOP owns the mailbox")
    chrome = _js_fn(js, "hidChromeTarget")
    if "join-mute" not in chrome or "lobby-join" not in chrome:
        _fail("leftover JOIN/CODE must not eat waiting-Yard HID after join")
    if "button" not in chrome:
        _fail("WARM UP / ENTER RANGE / LEAVE must stay chrome")
    mute = _js_fn(js, "muteJoinPad")
    if "join-mute" not in mute:
        _fail("muteJoinPad must drop leftover JOIN/CODE hit-test")
    if "aimBus" in mute or "fire(" in mute:
        _fail("join-mute gated fire — leftover chrome is not a peek")
    join = _js_fn(js, "lobbyJoin")
    if "muteJoinPad()" not in join:
        _fail("JOIN must release leftover CODE/JOIN so the waiting Yard stays a live gun")
    if join.find("muteJoinPad()") > join.find('setPhase("lobby")'):
        _fail("muteJoinPad must release leftover JOIN/CODE before setPhase Look")
    create = _js_fn(js, "lobbyCreate")
    leave = _js_fn(js, "lobbyLeave")
    if "clearJoinMute()" not in create or "clearJoinMute()" not in leave:
        _fail("create/leave must re-arm JOIN/CODE — do not mute the next session")
    step = _js_fn(js, "stepSim")
    if 'phase === "lobby"' not in step or "updateRange(SIM_DT" not in step:
        _fail("waiting-arena plates must tick on the 128 Hz sim")
    if 'id="screen-lobby" class="screen screen-pass"' not in html:
        _fail("screen-lobby must be screen-pass HUD-on-Yard")
    if "pointer-events: none" not in css or "#screen-lobby.screen-pass .lobby-inner" not in css:
        _fail("lobby overlay must let HID reach the Yard")
    if "join-mute" not in css or "#btn-lobby-join" not in css:
        _fail("leftover JOIN/CODE must pass the pad through after join")
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
    if "S.desktop" not in lifted:
        _fail("alreadyLifted must treat DESKTOP as a live gun")
    if re.search(r"camReady\s*&&\s*\([^)]*S\.desktop", lifted) or re.search(
        r"camReady\s*&&\s*S\.desktop", lifted
    ) or re.search(r"S\.desktop\s*&&\s*camReady", lifted) or re.search(
        r"\([^)]*S\.desktop[^)]*\)\s*&&\s*camReady", lifted
    ):
        _fail("alreadyLifted ANDs camReady with S.desktop — DESKTOP is already a live gun")
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


def test_q4_fail_to_lock_seeking_until_space() -> None:
    """Q4: camReady + no hand on waiting Yard → SEEKING until lock or Space.

    Never auto-desktop / goDesktopRange / invent OS cursor because lock
    timed out while camReady. Distinct from #73 camera-deny desktop.
    Offline tickLock / play() goDesktopRange stays Offline's path.
    Thin SableHUD SEEKING chip so the state is not silent.
    """
    js = proto_js()
    arm = _js_fn(js, "armPracticeCam")
    ready = re.search(r"if \(camReady\) \{([\s\S]*?)\n  \}", arm)
    if not ready:
        _fail("armPracticeCam lost the camReady early-return")
    ready_body = ready.group(1)
    if "goDesktopRange" in ready_body or "armPracticeDesktop" in ready_body or "S.desktop" in ready_body:
        _fail("Q4: camReady waiting-Yard arm invented OS-cursor desktop")
    if "initHands" not in ready_body or "armVideoTrack" not in ready_body:
        _fail("camReady waiting Yard must still arm Hands — do not dead-gun")
    if re.search(r"if \(ok\)[\s\S]{0,120}armPracticeDesktop", arm):
        _fail("camera-ok invented desktop — Q4 is SEEKING until lock or Space")
    if "LOCK_GIVE_MS" in arm or "setTimeout" in arm:
        _fail("armPracticeCam grew a lock timeout — never desktop-after-timeout")
    if "goDesktopRange(" in arm:
        _fail("camera deny dumped lobby through goDesktopRange")
    if "armPracticeDesktop()" not in arm:
        _fail("camera deny must still arm desktop on the live lobby")

    desk = _js_fn(js, "armPracticeDesktop")
    if "if (camReady) return" not in desk:
        _fail("armPracticeDesktop must refuse to steal a live camera — Q4 is not deny")
    if "S.desktop = true" not in desk or 'S.mode = "DESKTOP"' not in desk:
        _fail("camera deny must still set desktop on !camReady")
    if "updateMode(" not in desk:
        _fail("camera deny must write updateMode DESKTOP truth immediately")
    if "afterLiftState()" not in desk:
        _fail("camera deny must invoke afterLiftState after writing DESKTOP truth")
    if desk.find("updateMode(") > desk.find("afterLiftState()"):
        _fail("afterLiftState must run after updateMode writes DESKTOP truth")
    if "goDesktopRange(" in desk:
        _fail("armPracticeDesktop must stay lobby — do not dump into the 60s gallery")

    wait = _js_fn(js, "startWaitingYard")
    if "goDesktopRange" in wait or "armPracticeDesktop" in wait or "S.desktop" in wait:
        _fail("startWaitingYard invented desktop — Q4 is SEEKING until lock or Space")
    if "tickLock" in wait or "LOCK_GIVE_MS" in wait:
        _fail("startWaitingYard copied Offline lock timeout onto fail-to-lock")

    phase = _js_fn(js, "setPhase")
    if "goDesktopRange(" in phase:
        _fail("setPhase invented goDesktopRange — waiting Yard must not dump lock timeout")
    if "armPracticeCam()" not in phase:
        _fail("setPhase(lobby) must arm the waiting-Yard gun")

    tick = _js_fn(js, "tickLock")
    if "goDesktopRange" not in tick:
        _fail("Offline lock timeout goDesktopRange must stay Offline's path")
    frame = _js_fn(js, "frame")
    if 'phase === "lock") tickLock' not in frame and 'phase === "lock") { tickLock' not in frame:
        _fail("tickLock must stay on lock phase — not waiting Yard")
    if "goDesktopRange" in frame or "armPracticeDesktop" in frame:
        _fail("frame invented desktop — Q4 waiting Yard must not timeout to OS cursor")
    if re.search(r'phase === "lobby"[\s\S]{0,200}goDesktopRange', frame):
        _fail("frame lobby path invented goDesktopRange")
    if re.search(r'phase === "lobby"[\s\S]{0,200}S\.desktop\s*=\s*true', frame):
        _fail("frame lobby path invented S.desktop")
    play = _js_fn(js, "play")
    if "goDesktopRange" not in play:
        _fail("Offline play() camera-deny goDesktopRange must stay Offline's path")
    if "afterLiftState" in play:
        _fail("play() must not wait on the mint-tell — Offline stays one-click")
    enter = _js_fn(js, "enterGame")
    if "afterLiftState()" not in enter:
        _fail("enterGame must invoke afterLiftState when Offline DESKTOP arms")
    if enter.find("setPhase") > enter.find("afterLiftState()"):
        _fail("afterLiftState must run after setPhase so range/bay is live")
    for name in ("armPracticeCam", "startWaitingYard", "setPhase", "frame"):
        body = _js_fn(js, name)
        if "LOCK_GIVE_MS" in body and (
            "goDesktopRange" in body or "armPracticeDesktop" in body or "S.desktop = true" in body
        ):
            _fail(f"{name} copied Offline lock timeout onto waiting-Yard fail-to-lock")

    keys = re.search(r'if \(e\.code === "Space"\) \{([^}]+)\}', js)
    if not keys or "S.forceGun = true" not in keys.group(1):
        _fail("Space must stay the Q4 force-GUN escape")
    space = keys.group(1)
    if "goDesktopRange" in space:
        _fail("Space must force GUN — do not invent desktop on fail-to-lock")
    if "updateMode(" not in space:
        _fail("Space must invoke updateMode after forceGun — MODE/mailbox must not wait a frame")
    if space.find("S.forceGun = true") > space.find("updateMode("):
        _fail("Space must set forceGun before updateMode")
    if space.find("updateMode(") > space.find("afterLiftState()"):
        _fail("Space must invoke updateMode before afterLiftState — same order as KeyT")
    if "armPracticeDesktop" in space or "S.desktop" in space:
        _fail("Space must force GUN — do not invent desktop on fail-to-lock")
    t_keys = js[js.find('addEventListener("keydown"') : js.find('addEventListener("keyup"')]
    t_block = re.search(
        r'if \(e\.code === "KeyT"\) \{([\s\S]*?)\n  if \(e\.code === "KeyW"\)',
        t_keys,
    )
    if not t_block:
        _fail("KeyT handler missing")
    t_body = t_block.group(1)
    if "S.desktop = !S.desktop" not in t_body:
        _fail("Q4: camReady KeyT must still toggle DESKTOP off — hand path owns the gun")
    if re.search(r"if \(camReady\)[\s\S]{0,120}armPracticeDesktop", t_body):
        _fail("Q4: camReady KeyT must not auto-desktop")
    if "camReady" not in t_body or "armPracticeDesktop()" not in t_body:
        _fail("cam-deny waiting Yard KeyT must re-arm DESKTOP — deny is not Q4")
    mode = _js_fn(js, "updateMode")
    if "S.forceGun" not in mode or 'S.mode = "GUN"' not in mode:
        _fail("updateMode must still force GUN from Space")
    fire = _js_fn(js, "fire")
    if "S.forceGun" not in fire:
        _fail("fire() must still honor Space forceGun — Q4 escape is a live gun")
    if "goDesktopRange" in fire or "armPracticeDesktop" in fire:
        _fail("fire() invented desktop — Q4 never auto-desktop")

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
    if "S.desktop = true" in mode_chip or "armPracticeDesktop" in mode_chip:
        _fail("drawModeChip invented desktop")

    chip = _js_fn(js, "seekingHudChip")
    if "camReady" not in chip:
        _fail("SEEKING chip must require camReady — deny desktop is not Q4")
    if "S.desktop" not in chip or "DESKTOP" not in chip:
        _fail("SEEKING chip must refuse DESKTOP — never invent OS cursor")
    if "S.forceGun" not in chip or '"GUN"' not in chip:
        _fail("SEEKING chip must hide on Space forceGun — that is the Q4 escape")
    if '"SEEKING"' not in chip:
        _fail("waiting-Yard camReady+no hand must paint a thin SEEKING chip")
    if "wait_practice" not in chip:
        _fail("SEEKING chip must preserve into WARM UP wait_practice")
    if "Locker.colors.rust" not in chip and "Locker.colors.bone" not in chip and "Locker.colors.mint" not in chip:
        _fail("SEEKING chip must stay charcoal / bone / mint / rust")
    if "#ff2bd6" in chip:
        _fail("SEEKING SableHUD chip left the thin bar family for mode-chip magenta")
    if "goDesktopRange" in chip or "armPracticeDesktop" in chip or "S.desktop = true" in chip:
        _fail("SEEKING chip invented desktop")
    if "aimBus" in chip or "fire(" in chip or "AimSample" in chip:
        _fail("SEEKING chip gated fire / touched AimSample")
    if re.search(r"await\s+", chip) or "fetch(" in chip:
        _fail("SEEKING chip awaits — HUD trapped HID")
    if "RAISE YOUR HAND" in chip or "HOLD SPACE" in chip or "Impact" in chip:
        _fail("SEEKING chip grew a tutorial wall")
    if "H * 0.78" in chip or "H*0.78" in chip or "H * 0.5" in chip:
        _fail("SEEKING chip hides the gun")
    hud = _js_fn(js, "drawHUD")
    if "seekingHudChip" not in hud or "drawSableChip" not in hud:
        _fail("SEEKING chip left the thin SableHUD bar")
    if "if (seekChip) chips.push(seekChip)" not in hud:
        _fail("SEEKING chip must stay additive with WAIT / ROOM")
    if 'phase === "range"' not in hud or '"SCORE "' not in hud:
        _fail("gallery SCORE must stay range-gated — SEEKING must not thicken lobby")
    mode_at = hud.find("drawModeChip")
    hangar_at = hud.find("hangarHudChip")
    room_at = hud.find("roomHudChip")
    seek_at = hud.find("seekingHudChip")
    if mode_at < 0 or hangar_at < 0 or room_at < 0 or seek_at < 0:
        _fail("SEEKING chip must stay additive with PAD/GUN + WAIT + ROOM")
    if mode_at > hangar_at or hangar_at > room_at or room_at > seek_at:
        _fail("SEEKING chip wiped PAD/GUN or hangar / ROOM chips")
    if "H * 0.78" in hud or "Impact" in hud or "RAISE YOUR HAND" in hud:
        _fail("SEEKING chip hides the gun or grew a tutorial wall")
    if "setPhase" in hud or "fire(" in hud or "aimBus" in hud:
        _fail("HUD trapped lift/HID")
    d2 = _js_fn(js, "draw2D")
    lobby = d2[d2.find('phase === "lobby"') :]
    if not lobby or "drawHUD" not in lobby:
        _fail("waiting arena must paint the Q4 SEEKING chip on the thin SableHUD bar")
    xh = lobby.find("drawCrosshair")
    chips = lobby.find("drawHUD")
    if xh < 0 or chips < 0 or xh > chips:
        _fail("waiting-arena SEEKING chip must paint over live aim — crosshair then chips")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")


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
    if "onHidPointerDown" not in bible:
        _fail("PRODUCTION.md must name window HID pointerdown")
    if "canvasHUD" not in modes and "onHidPointerDown" not in modes:
        _fail("docs/modes.md must refuse a muted #hud pad")
    if "startWaitingYard" not in bible:
        _fail("PRODUCTION.md must name waiting-arena always-practice")
    if "armPracticeCam" not in bible:
        _fail("PRODUCTION.md must name waiting-Yard camera arm")
    if "armPracticeDesktop" not in bible:
        _fail("PRODUCTION.md must name waiting-Yard camera-deny desktop")
    if "goDesktopRange" not in bible:
        _fail("PRODUCTION.md must refuse camera-deny dump through goDesktopRange")
    if "dead gun" not in modes and "armPracticeCam" not in modes:
        _fail("docs/modes.md must refuse a waiting Yard on a dead gun")
    if "armPracticeDesktop" not in modes:
        _fail("docs/modes.md must name waiting-Yard camera-deny desktop")
    pipeline = (ROOT / "docs/aim_pipeline.md").read_text(encoding="utf-8")
    if "armPracticeDesktop" not in pipeline:
        _fail("docs/aim_pipeline.md must name waiting-Yard camera-deny desktop")
    if "Q4 fail-to-lock is SEEKING until lock or Space" not in bible:
        _fail("PRODUCTION.md must lock Q4 fail-to-lock as SEEKING until lock or Space")
    if "never OS cursor" not in bible:
        _fail("PRODUCTION.md must refuse OS cursor on waiting-Yard fail-to-lock")
    if "Camera deny is not fail-to-lock" not in bible:
        _fail("PRODUCTION.md must distinguish #73 camera-deny desktop from Q4")
    if "`goDesktopRange` stays Offline" not in bible:
        _fail("PRODUCTION.md must keep Offline lock timeout goDesktopRange on Offline")
    if "forceGun" not in bible:
        _fail("PRODUCTION.md must name Space forceGun as the Q4 escape")
    if "Q4 fail-to-lock is SEEKING until lock or Space" not in modes:
        _fail("docs/modes.md must lock Q4 fail-to-lock as SEEKING until lock or Space")
    if "Camera deny is not fail-to-lock" not in modes:
        _fail("docs/modes.md must distinguish camera-deny desktop from Q4")
    if "Q4 fail-to-lock is SEEKING until lock or Space" not in pipeline:
        _fail("docs/aim_pipeline.md must lock Q4 fail-to-lock as SEEKING until lock or Space")
    if "Camera deny is not fail-to-lock" not in pipeline:
        _fail("docs/aim_pipeline.md must distinguish camera-deny desktop from Q4")
    if "`lobby` is live for mint-tell" not in modes:
        _fail("docs/modes.md must name waiting-Yard lobby mint-tell")
    if "enterRangePreserve" not in bible:
        _fail("PRODUCTION.md must name ENTER RANGE phase-preserve")
    if "lobbyWarmup" not in bible or "play()" not in bible:
        _fail("PRODUCTION.md must name WARM UP phase-preserve off play() lock")
    if "phase-preserve" not in modes and "already lifted" not in modes:
        _fail("docs/modes.md must name ENTER RANGE phase-preserve")
    if "lobbyWarmup" not in modes or "play()" not in modes:
        _fail("docs/modes.md must refuse WARM UP play() lock tax")
    if "`alreadyLifted` treats DESKTOP as live" not in modes:
        _fail("docs/modes.md must name alreadyLifted DESKTOP live without camReady")
    if "`alreadyLifted` treats DESKTOP as live" not in bible:
        _fail("PRODUCTION.md must name alreadyLifted DESKTOP live without camReady")
    if "`onHidPointerDown` publishes click UV when DESKTOP owns the mailbox" not in modes:
        _fail("docs/modes.md must lock DESKTOP first-pad click UV")
    if "`onHidPointerDown` publishes click UV when DESKTOP owns the mailbox" not in bible:
        _fail("PRODUCTION.md must lock DESKTOP first-pad click UV")
    if "`onHidPointerDown` publishes click UV when DESKTOP owns the mailbox" not in pipeline:
        _fail("docs/aim_pipeline.md must lock DESKTOP first-pad click UV")
    lock = "`updateMode` writes DESKTOP truth (`seeking` false, `lifted` true) even if `!camReady`"
    if lock not in modes:
        _fail("docs/modes.md must lock DESKTOP updateMode truth without camReady")
    if lock not in bible:
        _fail("PRODUCTION.md must lock DESKTOP updateMode truth without camReady")
    if lock not in pipeline:
        _fail("docs/aim_pipeline.md must lock DESKTOP updateMode truth without camReady")
    keyt = "KeyT must not disarm DESKTOP on cam-deny waiting Yard"
    if keyt not in modes:
        _fail("docs/modes.md must lock KeyT cam-deny waiting-Yard DESKTOP hold")
    if keyt not in bible:
        _fail("PRODUCTION.md must lock KeyT cam-deny waiting-Yard DESKTOP hold")
    if keyt not in pipeline:
        _fail("docs/aim_pipeline.md must lock KeyT cam-deny waiting-Yard DESKTOP hold")
    cursor = "`syncCursor` shows the OS cursor when `S.desktop`"
    if cursor not in modes:
        _fail("docs/modes.md must lock DESKTOP OS-cursor visibility")
    if cursor not in bible:
        _fail("PRODUCTION.md must lock DESKTOP OS-cursor visibility")
    if cursor not in pipeline:
        _fail("docs/aim_pipeline.md must lock DESKTOP OS-cursor visibility")
    mint = "`draw2D` skips `drawCrosshair` when `S.desktop`"
    if mint not in modes:
        _fail("docs/modes.md must lock DESKTOP mint-reticle skip")
    if mint not in bible:
        _fail("PRODUCTION.md must lock DESKTOP mint-reticle skip")
    if mint not in pipeline:
        _fail("docs/aim_pipeline.md must lock DESKTOP mint-reticle skip")
    conf = "`publishAim` writes confidence 1 when `S.desktop`"
    if conf not in modes:
        _fail("docs/modes.md must lock DESKTOP publishAim confidence 1")
    if conf not in bible:
        _fail("PRODUCTION.md must lock DESKTOP publishAim confidence 1")
    if conf not in pipeline:
        _fail("docs/aim_pipeline.md must lock DESKTOP publishAim confidence 1")
    tell = "`armPracticeDesktop` invokes `afterLiftState` after writing DESKTOP truth"
    if tell not in modes:
        _fail("docs/modes.md must lock cam-deny mint-tell after DESKTOP truth")
    if tell not in bible:
        _fail("PRODUCTION.md must lock cam-deny mint-tell after DESKTOP truth")
    if tell not in pipeline:
        _fail("docs/aim_pipeline.md must lock cam-deny mint-tell after DESKTOP truth")
    offline = "`enterGame` invokes `afterLiftState` after `setPhase`"
    if offline not in modes:
        _fail("docs/modes.md must lock Offline DESKTOP mint-tell on enterGame")
    if offline not in bible:
        _fail("PRODUCTION.md must lock Offline DESKTOP mint-tell on enterGame")
    if offline not in pipeline:
        _fail("docs/aim_pipeline.md must lock Offline DESKTOP mint-tell on enterGame")
    space = "`Space` forceGun invokes `updateMode` before `afterLiftState`"
    if space not in modes:
        _fail("docs/modes.md must lock Space forceGun updateMode before afterLiftState")
    if space not in bible:
        _fail("PRODUCTION.md must lock Space forceGun updateMode before afterLiftState")
    if space not in pipeline:
        _fail("docs/aim_pipeline.md must lock Space forceGun updateMode before afterLiftState")
    mode_lock = '`drawModeChip` does not prefer SEEKING when `S.forceGun` or `S.mode === "GUN"`'
    if mode_lock not in modes:
        _fail("docs/modes.md must lock drawModeChip forceGun / GUN over SEEKING")
    if mode_lock not in bible:
        _fail("PRODUCTION.md must lock drawModeChip forceGun / GUN over SEEKING")
    if mode_lock not in pipeline:
        _fail("docs/aim_pipeline.md must lock drawModeChip forceGun / GUN over SEEKING")
    if "muteJoinPad" not in modes or "JOIN/CODE" not in modes:
        _fail("docs/modes.md must refuse leftover JOIN/CODE eating the pad")
    if "muteJoinPad" not in bible:
        _fail("PRODUCTION.md must name leftover JOIN/CODE mute")
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
        test_q4_fail_to_lock_seeking_until_space()
        test_aimsample_and_docs()
        test_room_chip_thin()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("sablelobby lock ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
