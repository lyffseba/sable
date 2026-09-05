#!/usr/bin/env python3
"""Bay competitive 1v1 on the R6 contract.

Fail loud if local first-to-5 leaves 128 Hz / HID-outside / fire_ms,
if parked lobbyStartBay awaits net, if Offline / WARM UP die, if Bay
reappears on player chrome, or if Bay HUD grows a tutorial wall over the cuff.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402


def _fail(msg: str) -> None:
    raise AssertionError(f"BAY R6 FAIL: {msg}")


def _fail_only_gun(msg: str) -> None:
    raise AssertionError(f"BAY R6 FAIL: Bay became the only gun — {msg}")


def _js_fn(src: str, name: str) -> str:
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


def _js_const(src: str, name: str) -> str:
    m = re.search(rf"const {name} = ([^;\n]+)", src)
    if not m:
        _fail(f"missing const {name}")
    return m.group(1).strip()


def test_pose_lives_on_128() -> None:
    js = proto_js()
    if _js_const(js, "SIM_HZ") != "128":
        _fail("R6 sim must stay 128 Hz")
    if "const SIM_DT = 1 / SIM_HZ" not in js and "const SIM_DT = 1/SIM_HZ" not in js:
        _fail("client lost SIM_DT = 1 / SIM_HZ")
    step = _js_fn(js, "stepSim")
    if "tickBay(SIM_DT" not in step:
        _fail("stepSim must advance Bay at SIM_DT")
    if re.search(r"\bfire\s*\(", step) or "aimBus" in step:
        _fail("stepSim must not shoot or peek AimBus")
    if "performance.now" in step:
        _fail("stepSim hitch to present")
    tick = _js_fn(js, "tickBay")
    if "performance.now" in tick or "lastT" in tick:
        _fail("tickBay hitch to wall / rAF present")
    if re.search(r"\bfire\s*\(", tick) or "fireBay3D" in tick:
        _fail("tickBay shoots — HID leaked onto the sim clock")
    if "aimBus.fire" in tick:
        _fail("tickBay peeks the fire mailbox — walk may read lift, fire stays HID")
    frame = _js_fn(js, "frame")
    if "tickBay(dt)" in frame or "updateRange(dt" in frame:
        _fail("Bay/Range still integrate on raw rAF dt")
    drain = re.search(r"while \(simAcc >= SIM_DT\) \{[\s\S]*?\}", frame)
    if not drain or "stepSim()" not in drain.group(0):
        _fail("rAF must drain simAcc through stepSim only")
    start = _js_fn(js, "startBay")
    if "S.simTick = 0" not in start:
        _fail("startBay must reset the sim tick — fire at tick 0 is legal")
    if "Bay.fireMs = 0" not in start and "fireMs = 0" not in start:
        _fail("startBay must clear the fire_ms stamp")


def test_hid_fire_stamps_sim_ms() -> None:
    js = proto_js()
    fire = _js_fn(js, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if "fireBay3D" not in fire:
        _fail("range fire must still route Bay to fireBay3D")
    banned = (
        r"await\s+",
        r"requestAnimationFrame",
        r"stepSim\s*\(",
        r"simAcc",
        r"SIM_DT",
        r"SIM_HZ",
        r"postMessage",
        r"detectForVideo",
        r"hands_worker",
        r"new Worker",
    )
    for pat in banned:
        if re.search(pat, fire):
            _fail(f"fire() waits on tick/rAF/worker ({pat})")
    if "/api/lobby" in fire or re.search(r"\bfetch\s*\(", fire):
        _fail("fire() talks to net — HID is behind the lobby")
    if "coastTrack" in fire or "updateAim" in fire:
        _fail("fire() recomputes aim")
    if "performance.now() - S.rangeStart" in fire:
        _fail("fire couples to present")
    bay = _js_fn(js, "fireBay3D")
    if "committedSimMs" not in bay:
        _fail("Bay fire_ms must speak the last committed sim tick")
    if "Bay.fireMs" not in bay:
        _fail("fireBay3D must stamp Bay.fireMs")
    if "performance.now" in bay or "S.rangeStart" in bay:
        _fail("Bay fire_ms couples to present")
    if "fetch(" in bay or "/api/lobby" in bay:
        _fail("Bay fire talks to net — do not invent a friend tick")
    if re.search(r"await\s+", bay):
        _fail("fireBay3D awaits — HID is behind a promise")
    if "Math.random" in bay:
        _fail("Bay fire hid the shot with RNG")
    if "getWorldPosition" in bay or "peekMuzzleWorld" in bay or "addBulletTracer" in bay:
        _fail("fireBay3D must stay the sphere — Look tracers peek muzzle after markHid")
    committed = _js_fn(js, "committedSimMs")
    if "simTick" not in committed:
        _fail("committedSimMs must read S.simTick")
    if "performance.now" in committed:
        _fail("committedSimMs hitch to present")


def test_enter_bay_soft_lock() -> None:
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
    boot_bay = re.search(r'\$\("btn-bay"\)[\s\S]{0,220}?play\("bay"\)', js)
    if boot_bay:
        _fail("boot still wires BAY — soft-park must hide the player entry")
    start_bay = _js_fn(js, "lobbyStartBay")
    if "/api/lobby/start" in start_bay:
        _fail("parked lobbyStartBay started the shared house")
    if re.search(r"await\s+", start_bay) or "async function lobbyStartBay" in js:
        _fail("parked lobbyStartBay awaits net — lift/HID is behind the lobby")
    if 'play("bay")' not in start_bay and 'setPhase("bay")' not in start_bay:
        _fail("parked lobbyStartBay lost the booth drop")
    if "stepSim" in start_bay or "simAcc" in start_bay or re.search(r"setTimeout", start_bay):
        _fail("parked lobbyStartBay grew a tick tax")
    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/start" in warm or re.search(r"await\s+", warm):
        _fail("WARM UP soft-locked behind net")
    if 'play("bay")' in warm or 'setPhase("bay")' in warm:
        _fail_only_gun("WARM UP dropped into Bay")
    start_range = _js_fn(js, "lobbyStartRange")
    if ("enterRangePreserve()" not in start_range and 'play("range")' not in start_range) or "/api/lobby/start" not in start_range:
        _fail_only_gun("ENTER RANGE no longer shares the Salt House")
    if re.search(r"await\s+", start_range):
        _fail("ENTER RANGE awaits net — lift/HID is behind the lobby POST")
    poll = _js_fn(js, "lobbyPoll")
    if 'phase === "bay"' not in poll:
        _fail("lobby poll must not yank Bay into shared Range")


def test_thin_chips_no_tutorial() -> None:
    js = proto_js()
    if _js_const(js, "SABLE_HUD_H") != "22":
        _fail("SableHUD bar must stay thin (22px chips)")
    hud = _js_fn(js, "drawBayHUD")
    if "drawSableChip" not in hud:
        _fail("Bay feedback left the SableHUD chip bar")
    if "baySessionLabel" not in hud:
        _fail("Bay HUD must read FIRST TO 5 / MATCH from baySessionLabel")
    if '"YOU "' not in hud:
        _fail("Bay HUD lost the YOU chip")
    if '"THEM "' not in hud:
        _fail("Bay HUD lost the THEM chip")
    if '"ROUND "' not in hud and '"ROUND"' not in hud:
        _fail("Bay HUD lost the ROUND chip")
    if "HUD_PAD" not in hud:
        _fail("Bay SableHUD must stay a top bar over live aim")
    if "Impact" in hud:
        _fail("Bay HUD thickened — no Impact billboard")
    if "WASD on PAD" in hud or "LOWER THE CUFF" in hud or "CLICK fires" in hud:
        _fail("tutorial wall over live aim")
    if "RAISE YOUR HAND" in hud or "LIFT to aim" in hud:
        _fail("tutorial wall over live aim")
    if "H * 0.78" in hud or "H*0.78" in hud or "H * 0.5" in hud or "H*0.5" in hud:
        _fail("Bay HUD hides the gun or the reticle")
    if "H - 32" in hud or "H - 70" in hud or "H-32" in hud or "H-70" in hud:
        _fail("Bay HUD painted over the cuff")
    if "shadowBlur" in hud or "glow" in hud.lower():
        _fail("Bay HUD bloomed over the reticle")
    if "setPhase" in hud or "fire(" in hud or "aimBus" in hud:
        _fail("Bay HUD trapped lift/HID")
    sess = _js_fn(js, "baySessionLabel")
    if '"FIRST TO 5"' not in sess:
        _fail("baySessionLabel must chip FIRST TO 5")
    if '"MATCH"' not in sess:
        _fail("baySessionLabel must chip MATCH at first-to-5")
    if "bayOver" not in sess:
        _fail("session label must read bayOver")
    d2 = _js_fn(js, "draw2D")
    bay = d2[d2.find('phase === "bay"') :]
    if not bay:
        _fail("draw2D lost the Bay path")
    xh = bay.find("drawCrosshair")
    chips = bay.find("drawBayHUD")
    if xh < 0 or chips < 0 or xh > chips:
        _fail("Bay SableHUD must paint over live aim — crosshair then chips")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")


def test_docs_and_ci() -> None:
    modes = (ROOT / "docs/modes.md").read_text(encoding="utf-8")
    bible = (ROOT / "docs/PRODUCTION.md").read_text(encoding="utf-8")
    tick = (ROOT / "docs/tick.md").read_text(encoding="utf-8")
    bay = (ROOT / "docs/maps/bay.md").read_text(encoding="utf-8")
    if "Bay rules" not in modes:
        _fail("docs/modes.md must name Bay competitive rules")
    if "SableHUD" not in modes or "FIRST TO 5" not in modes:
        _fail("docs/modes.md must keep thin Bay chips")
    if "tutorial wall" not in modes.lower():
        _fail("docs/modes.md must refuse a Bay tutorial wall")
    if "parked" not in modes.lower() and "sole active" not in modes.lower():
        _fail("docs/modes.md must park Bay — Yard is the sole active map")
    if "128 Hz" not in tick or "Bay.fireMs" not in tick:
        _fail("docs/tick.md must lock Bay fire_ms on the 128 Hz grid")
    if "SableHUD" not in bay or "tutorial wall" not in bay.lower():
        _fail("docs/maps/bay.md must name thin chips / no tutorial wall")
    if "committedSimMs" not in bay:
        _fail("docs/maps/bay.md must stamp fire_ms on the sim tick")
    if "test_bay_r6.py" not in bible:
        _fail("PRODUCTION.md must fail loud through test_bay_r6.py")
    if "M8" not in bible:
        _fail("PRODUCTION.md must stand the Bay R6 milestone")
    if "v0.20.0" not in bible:
        _fail("do not drop the SableHUD v0.20.0 stand")
    ci = (ROOT / "tools/ci.sh").read_text(encoding="utf-8")
    if "test_bay_r6.py" not in ci:
        _fail("ci.sh must run the Bay R6 competitive lock")


def main() -> int:
    try:
        test_pose_lives_on_128()
        test_hid_fire_stamps_sim_ms()
        test_enter_bay_soft_lock()
        test_thin_chips_no_tutorial()
        test_docs_and_ci()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("bay r6 competitive ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
