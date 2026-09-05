#!/usr/bin/env python3
"""Post-Worker SablePerf / gun contract.

Fail loud if HandLandmarker detect sneaks back onto main rAF, if the
HID→hitscan probe is missing or reordered, if fire waits on the worker,
or if Shared Bay net lands inside the 8 ms HID→hitscan bar.
"""

from __future__ import annotations

import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402

DETECT_CALL = re.compile(r"\.detectForVideo\s*\(")
WORKER_WAIT = re.compile(
    r"await\s+|postMessage|createImageBitmap|detectForVideo|hands_worker|new Worker|fetch\("
)


def _fail(msg: str) -> None:
    raise AssertionError(f"SABLEPERF FAIL: {msg}")


def _fn(src: str, name: str) -> str:
    """Brace-match a function so nested blocks do not truncate the body."""
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


def _object(src: str, name: str) -> str:
    m = re.search(rf"const {name} = \{{", src)
    if not m:
        _fail(f"missing {name} object")
    start = src.find("{", m.start())
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
    _fail(f"{name} object is unclosed")
    raise AssertionError("unreachable")


def _pct(samples: list[float], p: float) -> float:
    s = sorted(samples)
    if not s:
        return 0.0
    i = min(len(s) - 1, math.ceil(p * len(s)) - 1)
    return s[i]


def test_no_main_thread_detect() -> None:
    js = proto_js()
    hands = (ROOT / "proto/hands.js").read_text(encoding="utf-8")
    worker = (ROOT / "proto/hands_worker.js").read_text(encoding="utf-8")
    aim = (ROOT / "proto/aim.js").read_text(encoding="utf-8")
    boot = (ROOT / "proto/boot.js").read_text(encoding="utf-8")
    house = (ROOT / "proto/house.js").read_text(encoding="utf-8")
    game = (ROOT / "proto/game.js").read_text(encoding="utf-8")

    if not DETECT_CALL.search(worker):
        _fail("worker lost HandLandmarker.detectForVideo")
    if 'type: "module"' in hands or "type: 'module'" in hands:
        _fail("module worker breaks MediaPipe importScripts — detect falls back to main")
    if re.search(r"^import ", worker, re.M):
        _fail("classic worker must not use static ESM import")

    for rel, src in (("aim.js", aim), ("boot.js", boot), ("house.js", house), ("game.js", game)):
        if DETECT_CALL.search(src):
            _fail(f"{rel} called detectForVideo — detect leaked onto main")

    main = _fn(hands, "mpTrackMain")
    if not DETECT_CALL.search(main):
        _fail("mpTrackMain is the named last-resort; it must be the only main detect")
    for m in DETECT_CALL.finditer(hands):
        if not (main and hands.find(main) <= m.start() < hands.find(main) + len(main)):
            snippet = hands[max(0, m.start() - 40) : m.start() + 20]
            if "detectForVideo lives" in snippet:
                continue
            _fail("detectForVideo sneaked onto main outside mpTrackMain")

    mp = _fn(js, "mpTrack")
    if DETECT_CALL.search(mp):
        _fail("mpTrack happy path called detectForVideo on main")
    if "S.hands.worker" not in mp:
        _fail("mpTrack must prefer the Worker mailbox")
    if "kickAndFresh" not in mp and "kickWorkerDetect" not in mp:
        _fail("mpTrack must kick the worker, not detect on rAF")
    worker_at = mp.find("S.hands.worker")
    last_resort = mp.find("mpTrackMain")
    if last_resort >= 0 and last_resort < worker_at:
        _fail("mpTrackMain ran before the Worker check — detect is back on main")

    kick = _fn(js, "kickAndFresh")
    if DETECT_CALL.search(kick) or "mpTrackMain" in kick:
        _fail("kickAndFresh must peek last landmarks, never detect on main")
    if "kickWorkerDetect" not in kick:
        _fail("kickAndFresh must post a frame and return")

    for name in ("frame", "runTrack", "armVideoTrack", "grabFrame"):
        body = _fn(js, name)
        if DETECT_CALL.search(body):
            _fail(f"{name}() ran HandLandmarker.detect on the rAF / game loop")
        if "mpTrackMain" in body:
            _fail(f"{name}() called mpTrackMain — sync detect on the critical path")

    frame = _fn(js, "frame")
    if "runTrack" not in frame:
        _fail("rAF frame lost runTrack — tracker no longer publishes the mailbox")
    if "fire(" in frame and "maybePinchFire" not in frame:
        _fail("rAF frame must not fire() except via pinch after updateMode")
    step = _fn(js, "stepSim")
    if "fire(" in step:
        _fail("stepSim must not fire — HID stays off the 128 Hz clock")


def test_sableperf_probe_order() -> None:
    js = proto_js()
    probe = _object(js, "SablePerf")
    if "budgetMs: 8" not in probe:
        _fail("SablePerf must prove HID→hitscan under 8 ms")
    if "begin(" not in probe or "markHid(" not in probe or "stats(" not in probe:
        _fail("SablePerf probe API missing (begin / markHid / stats)")
    if "performance.now()" not in probe:
        _fail("SablePerf must stamp t0 with performance.now")
    if "p99" not in probe or "p50" not in probe:
        _fail("SablePerf.stats() must report p50/p99")
    if "drawModeChip" in probe:
        _fail("SablePerf must not paint a HUD")
    if "sableperf=1" not in js:
        _fail("SablePerf must stay flag-gated (?sableperf=1)")
    if "globalThis.SablePerf" not in js and "window.SablePerf" not in js:
        _fail("window.SablePerf / globalThis.SablePerf probe missing")
    aim = (ROOT / "docs/aim_pipeline.md").read_text(encoding="utf-8")
    if "after" not in aim or "markHid" not in aim or "Look" not in aim:
        _fail("docs/aim_pipeline.md must keep Look after markHid")
    bible = (ROOT / "docs/PRODUCTION.md").read_text(encoding="utf-8")
    if "gun kick" not in bible.lower() and "getWorldPosition" not in bible:
        _fail("PRODUCTION.md must fail loud if Look lands inside the HID→hitscan probe")

    fire = _fn(js, "fire")
    gate = fire.find("if (!S.desktop && !S.lifted")
    begin_at = fire.find("SablePerf.begin")
    bang_at = fire.find("bang();")
    if gate < 0 or begin_at < 0 or bang_at < 0:
        _fail("fire() must keep the lift gate, SablePerf.begin, and bang()")
    if not (gate < begin_at < bang_at):
        _fail("SablePerf t0 must start after the lift/desktop gate and before bang()")

    first_mark = fire.find("SablePerf.markHid")
    if first_mark < 0 or first_mark < bang_at:
        _fail("SablePerf.markHid must stay after bang(), at first hitscan")
    intersect = fire.find("hitscanRange(")
    mark_range = fire.find("SablePerf.markHid", intersect) if intersect >= 0 else -1
    report_at = fire.find("reportSharedFire")
    if intersect < 0 or mark_range < 0:
        _fail("Range hitscan lost SablePerf.markHid")
    if mark_range < intersect:
        _fail("SablePerf.markHid must stay at first hitscan sphere")
    probe = fire[intersect:mark_range]
    if "applyGunKick" in probe or "peekMuzzleWorld" in probe or "getWorldPosition" in probe:
        _fail("Look (gun kick / muzzle world) landed inside the HID→hitscan probe")
    if "gunGroup" in probe or "gunMuzzleLight" in probe:
        _fail("gun Look mutated inside the 8 ms bar — peel it after markHid")
    kick_after = fire.find("applyGunKick", mark_range)
    muzzle_after = fire.find("peekMuzzleWorld", mark_range)
    if kick_after < 0 or muzzle_after < 0:
        _fail("Range Look (gun kick / muzzle) must run after markHid, not vanish")
    if kick_after > report_at >= 0:
        _fail("Range gun kick must stay after the sphere and before shared report")
    peek = _fn(js, "peekMuzzleWorld")
    if "if (gunMuzzleLight)" not in peek:
        _fail("peekMuzzleWorld must be null-safe — a missing cuff must not throw on the click")
    if "getWorldPosition" not in peek:
        _fail("peekMuzzleWorld lost the Look tracer origin")
    if "intersectObjects" in fire:
        _fail("Range hitscan must be the house sphere — mesh traverse taxes the 8 ms bar")
    if report_at < 0 or mark_range > report_at:
        _fail("shared report must run after local hitscan, never instead of it")

    bay = fire.find('phase === "bay"')
    bay_fire = fire.find("fireBay3D", bay) if bay >= 0 else -1
    bay_mark = fire.find("SablePerf.markHid", bay) if bay >= 0 else -1
    bay_report = fire.find("reportSharedBayFire", bay) if bay >= 0 else -1
    if bay < 0 or bay_fire < 0 or bay_mark < 0 or bay_fire > bay_mark:
        _fail("Bay HID→hitscan must mark after fireBay3D, still under the 8 ms probe")
    if bay_report < 0 or bay_mark > bay_report:
        _fail("reportSharedBayFire must stay after markHid — Shared Bay must not tax the 8 ms bar")
    bay_probe = fire[bay:bay_mark]
    if "peekMuzzleWorld" in bay_probe or "getWorldPosition" in bay_probe or "applyGunKick" in bay_probe:
        _fail("Bay Look (muzzle world / gun kick) landed inside the HID→hitscan probe")
    bay_muzzle = fire.find("peekMuzzleWorld", bay_mark) if bay_mark >= 0 else -1
    if bay_muzzle < 0 or (bay_report >= 0 and bay_muzzle > bay_report):
        _fail("Bay peekMuzzleWorld must run after markHid, not vanish or follow the lobby POST")


def test_sableperf_budget_math() -> None:
    under = [0.4, 0.5, 0.6, 0.7, 0.8, 1.1, 1.2, 2.0, 3.1, 4.5]
    p50 = _pct(under, 0.5)
    p99 = _pct(under, 0.99)
    if p50 > p99:
        _fail("p50 must be <= p99")
    if p99 >= 8:
        _fail("fixture p99 must stay under the 8 ms bar")
    if _pct(under + [12.0], 0.99) < 8:
        _fail("a 12 ms hit must fail the 8 ms p99 bar")
    if _pct([], 0.99) != 0.0:
        _fail("empty probe must not invent a p99")


def test_fire_never_waits_on_worker_or_net() -> None:
    js = proto_js()
    fire = _fn(js, "fire")
    if WORKER_WAIT.search(fire):
        _fail("fire() waits on the worker or net — HID is no longer a peek")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if "coastTrack" in fire or "updateAim" in fire:
        _fail("fire() recomputes aim")
    if "kickWorkerDetect" in fire or "mpTrack" in fire or "runTrack" in fire:
        _fail("fire() talks to the tracker")
    if "/api/lobby" in fire:
        _fail("fire() talks to the lobby")

    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")


def test_shared_bay_never_taxes_hid_probe() -> None:
    """Shared Bay net stays fire-and-forget after markHid — never on the click."""
    js = proto_js()
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")

    probe = _object(js, "SablePerf")
    if "budgetMs: 8" not in probe:
        _fail("SablePerf 8 ms bar died after Shared Bay")
    if "p99 < this.budgetMs" not in probe:
        _fail("SablePerf.stats() must still fail loud when p99 leaves 8 ms")
    if "sableperf=1" not in js:
        _fail("SablePerf must stay flag-gated (?sableperf=1)")
    if "globalThis.SablePerf" not in js and "window.SablePerf" not in js:
        _fail("window.SablePerf / globalThis.SablePerf probe missing")
    if "drawModeChip" in probe:
        _fail("SablePerf must not paint a HUD")

    fire = _fn(js, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if WORKER_WAIT.search(fire):
        _fail("fire() waits on the worker or net — Shared Bay taxed HID")
    if "/api/lobby" in fire or re.search(r"\bfetch\s*\(", fire):
        _fail("fire() talks to net — HID is behind the lobby")
    if re.search(r"await\s+", fire):
        _fail("fire() awaits — HID is behind a promise")
    if "reportSharedBayPose" in fire:
        _fail("reportSharedBayPose leaked onto the click")
    if "lobbyPoll" in fire or "pullSharedBay" in fire or "lobbyPost" in fire:
        _fail("lobby poll / snapshot leaked onto the click")
    if "Math.random" in fire or re.search(r"\bbloom\b", fire, re.I):
        _fail("fire hid noise with RNG or bloom")
    if "coastTrack" in fire or "updateAim" in fire:
        _fail("fire() recomputes aim")

    bay = fire.find('phase === "bay"')
    bay_fire = fire.find("fireBay3D", bay) if bay >= 0 else -1
    bay_mark = fire.find("SablePerf.markHid", bay) if bay >= 0 else -1
    bay_report = fire.find("reportSharedBayFire", bay) if bay >= 0 else -1
    if bay < 0 or bay_fire < 0 or bay_mark < 0 or bay_report < 0:
        _fail("Bay HID→hitscan must mark, then fire-and-forget the room")
    if not (bay_fire < bay_mark < bay_report):
        _fail("reportSharedBayFire landed inside the HID→hitscan probe — Shared Bay taxed the 8 ms bar")
    bay_probe = fire[bay:bay_mark]
    if "peekMuzzleWorld" in bay_probe or "getWorldPosition" in bay_probe or "applyGunKick" in bay_probe:
        _fail("Bay Look (muzzle world / gun kick) landed inside the HID→hitscan probe")

    report = _fn(js, "reportSharedBayFire")
    if "async function reportSharedBayFire" in js:
        _fail("reportSharedBayFire must not be async")
    if re.search(r"await\s+", report):
        _fail("reportSharedBayFire must be fire-and-forget")
    if "fetch(" not in report or ".then(" not in report:
        _fail("reportSharedBayFire must POST then continue")
    if "/api/lobby/hit" not in report:
        _fail("shared Bay fire must POST the intent")
    if "committedSimMs" not in report:
        _fail("shared Bay fire_ms must speak sim Hz")
    if "performance.now()" in report:
        _fail("shared Bay fire_ms couples to present")

    pose = _fn(js, "reportSharedBayPose")
    if "async function reportSharedBayPose" in js or re.search(r"await\s+", pose):
        _fail("reportSharedBayPose must be fire-and-forget")
    if "/api/lobby/pose" not in pose:
        _fail("shared Bay must POST last committed pose on the lazy poll")

    poll = _fn(js, "lobbyPoll")
    if "reportSharedBayPose" not in poll:
        _fail("pose mailbox must stay on the lazy lobby poll")
    if "setInterval(lobbyPoll" not in js:
        _fail("lobby poll must stay a lazy interval, not a click")
    if re.search(r"setInterval\(\s*lobbyPoll\s*,\s*(\d+)", js):
        interval = int(re.search(r"setInterval\(\s*lobbyPoll\s*,\s*(\d+)", js).group(1))
        if interval < 200:
            _fail("lobby poll must not become a friend loop")

    step = _fn(js, "stepSim")
    if "reportSharedBayPose" in step or "reportSharedBayFire" in step or "lobbyPoll" in step:
        _fail("shared Bay net leaked onto the 128 Hz step")

    bay_local = _fn(js, "fireBay3D")
    if "fetch(" in bay_local or "/api/lobby" in bay_local:
        _fail("local fireBay3D talks to net — boot BAY would wait on the lobby")

    if 'id="btn-play"' not in html or ">OFFLINE<" not in html:
        _fail("boot lost one-click OFFLINE GALLERY")
    offline = re.search(
        r'\$\("btn-play"\)\.addEventListener\("click", \(\) => \{[\s\S]*?play\("range"\)',
        js,
    )
    if not offline or "S.online = false" not in offline.group(0):
        _fail("OFFLINE GALLERY must stay local one-click")
    if 'play("bay")' in offline.group(0):
        _fail("OFFLINE was rerouted into Bay")

    if 'id="btn-bay"' in html or re.search(r">\s*BAY\s*<", html):
        _fail("boot still offers BAY — Yard is the sole active map")
    boot_bay = re.search(r'\$\("btn-bay"\)[\s\S]{0,220}?play\("bay"\)', js)
    if boot_bay:
        _fail("boot still wires BAY — soft-park must hide the player entry")

    if 'id="btn-lobby-bay"' in html or "ENTER BAY" in html:
        _fail("lobby still offers ENTER BAY — Bay is parked")
    start_bay = _fn(js, "lobbyStartBay")
    if re.search(r"await\s+", start_bay) or "async function lobbyStartBay" in js:
        _fail("parked lobbyStartBay awaits net — lift/HID is behind the lobby")
    if "/api/lobby/start\"" in start_bay or "/api/lobby/start'" in start_bay:
        _fail("parked lobbyStartBay started the shared house")
    if 'play("bay")' not in start_bay and 'setPhase("bay")' not in start_bay:
        _fail("parked lobbyStartBay lost the booth drop")

    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")


def test_offline_warmup_lock_never_cursor() -> None:
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    css = (ROOT / "proto/style.css").read_text(encoding="utf-8")
    js = proto_js()

    if 'id="btn-play"' not in html or ">OFFLINE<" not in html:
        _fail("boot lost one-click OFFLINE")
    play = re.search(
        r'\$\("btn-play"\)\.addEventListener\("click", \(\) => \{[\s\S]*?play\("range"\)',
        js,
    )
    if not play:
        _fail("OFFLINE is no longer one click into Range")
    if "S.online = false" not in play.group(0):
        _fail("OFFLINE stayed online — shared house would be the only gun")
    if "S.warmup = false" not in play.group(0):
        _fail("OFFLINE must clear WARM UP so startRange stays local")

    warm = _fn(js, "lobbyWarmup")
    if "S.warmup = true" not in warm:
        _fail("WARM UP flag missing")
    if "/api/lobby/start" in warm or re.search(r"await\s+", warm):
        _fail("WARM UP waits on net — not one-click local practice")
    if 'setPhase("range")' not in warm and 'play("range")' not in warm:
        _fail("WARM UP no longer drops into Range")
    if 'id="btn-lobby-warmup"' not in html or "WARM UP" not in html:
        _fail("waiting room lost WARM UP")

    if "#game.nocursor" not in css or "cursor: none" not in css:
        _fail("lock-never-cursor lost the CSS hide")
    move = re.search(r"pointermove[\s\S]{0,280}", js)
    if not move or "if (S.desktop)" not in move.group(0):
        _fail("OS pointer writes aim outside DESKTOP — lock-never-cursor died")
    sync = _fn(js, "syncCursor")
    if 'phase === "lock"' not in sync or "nocursor" not in sync:
        _fail("lock phase must hide the OS cursor")


def main() -> int:
    try:
        test_no_main_thread_detect()
        test_sableperf_probe_order()
        test_sableperf_budget_math()
        test_fire_never_waits_on_worker_or_net()
        test_shared_bay_never_taxes_hid_probe()
        test_offline_warmup_lock_never_cursor()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("sableperf post-worker gun ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
