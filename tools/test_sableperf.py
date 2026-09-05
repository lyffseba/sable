#!/usr/bin/env python3
"""Post-Worker SablePerf / gun contract.

Fail loud if HandLandmarker detect sneaks back onto main rAF, if the
HID→hitscan probe is missing or reordered, or if fire waits on the worker.
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
    intersect = fire.find("intersectObjects")
    mark_range = fire.find("SablePerf.markHid", intersect) if intersect >= 0 else -1
    report_at = fire.find("reportSharedFire")
    if intersect < 0 or mark_range < 0:
        _fail("Range hitscan lost SablePerf.markHid")
    if mark_range < intersect:
        _fail("SablePerf.markHid must stay at first hitscan intersect")
    if report_at < 0 or mark_range > report_at:
        _fail("shared report must run after local hitscan, never instead of it")

    bay = fire.find('phase === "bay"')
    bay_fire = fire.find("fireBay3D", bay) if bay >= 0 else -1
    bay_mark = fire.find("SablePerf.markHid", bay) if bay >= 0 else -1
    if bay < 0 or bay_fire < 0 or bay_mark < 0 or bay_fire > bay_mark:
        _fail("Bay HID→hitscan must mark after fireBay3D, still under the 8 ms probe")


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
        test_offline_warmup_lock_never_cursor()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("sableperf post-worker gun ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
