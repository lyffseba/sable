#!/usr/bin/env python3
"""R6 tick contract: 128 Hz sim, rAF render, HID fire outside both.

Fail loud if docs drift back to 64 Hz, if fire waits on the tick, if
Offline / WARM UP soft-lock, or if shared house becomes a fake 128 Hz loop.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402
import lobby  # noqa: E402

HZ = 128
DT = 1.0 / HZ


def _fail(msg: str) -> None:
    raise AssertionError(f"TICK FAIL: {msg}")


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


def test_named_rate_is_128() -> None:
    tick = (ROOT / "server/tick.py").read_text(encoding="utf-8")
    if "HZ = 128" not in tick:
        _fail("server/tick.py lost HZ = 128")
    if re.search(r"HZ\s*=\s*64\b", tick):
        _fail("server/tick.py drifted to 64 Hz")
    docs = (ROOT / "docs/tick.md").read_text(encoding="utf-8")
    if "128 Hz" not in docs:
        _fail("docs/tick.md must name 128 Hz")
    if re.search(r"Simulation is \*\*64 Hz\*\*", docs):
        _fail("docs/tick.md still claims 64 Hz is the sim rate")
    if "requestAnimationFrame" not in docs:
        _fail("docs/tick.md must keep render on rAF")
    if "AimBus" not in docs or "HID" not in docs:
        _fail("docs/tick.md must keep HID fire outside both clocks")
    if "rewind" not in docs.lower():
        _fail("docs/tick.md must keep shared house as rewind, not a friend tick")
    budget = (ROOT / "docs/perf_budget.md").read_text(encoding="utf-8")
    if "128 Hz" not in budget:
        _fail("docs/perf_budget.md must budget 128 Hz")
    if re.search(r"\b64 Hz\b", budget):
        _fail("docs/perf_budget.md still budgets 64 Hz")
    if "Jolt" in budget:
        _fail("docs/perf_budget.md still names Jolt — that clock is not in tree")
    bible = (ROOT / "docs/PRODUCTION.md").read_text(encoding="utf-8")
    if "Docs disagree" in bible:
        _fail("PRODUCTION.md still says docs disagree — contract was not picked")
    if "128 Hz" not in bible:
        _fail("PRODUCTION.md must name the 128 Hz contract")


def test_client_steps_local_sim_at_128() -> None:
    js = proto_js()
    if "const SIM_HZ = 128" not in js:
        _fail("client lost SIM_HZ = 128")
    if "const SIM_DT = 1 / SIM_HZ" not in js and "const SIM_DT = 1/SIM_HZ" not in js:
        _fail("client lost SIM_DT = 1 / SIM_HZ")
    step = _fn(js, "stepSim")
    if "updateRange(SIM_DT" not in step:
        _fail("stepSim must advance Range at SIM_DT")
    if "tickBay(SIM_DT" not in step:
        _fail("stepSim must advance Bay at SIM_DT")
    if re.search(r"\bfire\s*\(", step):
        _fail("stepSim shoots — HID fire leaked onto the sim clock")
    if "aimBus" in step:
        _fail("stepSim must not peek or wait on AimBus")
    frame = _fn(js, "frame")
    if "requestAnimationFrame(frame)" not in frame:
        _fail("render must stay on rAF")
    if "stepSim(" not in frame or "SIM_DT" not in frame:
        _fail("rAF must drain the 128 Hz accumulator, not replace it")
    if "updateRange(dt" in frame or "tickBay(dt)" in frame:
        _fail("Range/Bay still integrate on raw rAF dt")
    drain = re.search(r"while \(simAcc >= SIM_DT\) \{[\s\S]*?\}", frame)
    if not drain or "stepSim(t)" not in drain.group(0):
        _fail("rAF must drain simAcc through stepSim only")
    if re.search(r"\bfire\s*\(", drain.group(0)):
        _fail("sim drain loop shoots — HID fire leaked onto the tick")


def test_fire_never_waits_on_tick() -> None:
    js = proto_js()
    fire = _fn(js, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    banned = (
        r"await\s+",
        r"requestAnimationFrame",
        r"stepSim\s*\(",
        r"simAcc",
        r"SIM_DT",
        r"SIM_HZ",
        r"setInterval",
        r"postMessage",
        r"detectForVideo",
        r"createImageBitmap",
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
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    if 'id="btn-play"' not in html or ">OFFLINE<" not in html:
        _fail("OFFLINE one-click died while unifying the tick")
    play = re.search(
        r'\$\("btn-play"\)\.addEventListener\("click", \(\) => \{[\s\S]*?play\("range"\)',
        js,
    )
    if not play or "S.online = false" not in play.group(0):
        _fail("OFFLINE is no longer local one-click Range")
    warm = _fn(js, "lobbyWarmup")
    if re.search(r"await\s+", warm) or "/api/lobby/start" in warm:
        _fail("WARM UP soft-locked behind net")
    if 'setPhase("range")' not in warm and 'play("range")' not in warm:
        _fail("WARM UP no longer drops into local Range")


def test_shared_house_is_rewind_not_a_loop() -> None:
    src = (ROOT / "tools/lobby.py").read_text(encoding="utf-8")
    if "def _pose_at" not in src or "def _sync_sim" not in src:
        _fail("shared house lost closed-form pose / sync")
    if re.search(r"HZ\s*=\s*128", src) or "SIM_HZ" in src:
        _fail("lobby grew a 128 Hz friend loop — that would lie")
    if "time.sleep" in src:
        _fail("lobby.py sleeps — shared house is not a tick thread")
    pose_m = re.search(r"def _pose_at\([\s\S]*?\n\ndef ", src)
    if not pose_m:
        _fail("missing _pose_at")
    pose = pose_m.group(0)
    if "born_ms" not in pose or "life" not in pose:
        _fail("_pose_at must stay closed-form at elapsed_ms")
    if "for " in pose and "range(" in pose:
        _fail("_pose_at stepped a tick loop — rewind died")
    sync = re.search(r"def _sync_sim\([\s\S]*?return elapsed_ms\n", src)
    if not sync:
        _fail("missing _sync_sim")
    if "range(HZ)" in sync.group(0) or "range(128)" in sync.group(0):
        _fail("_sync_sim became a 128 Hz stepper")
    if lobby.RANGE_MS != 60_000:
        _fail("shared Range length drifted")
    t0 = 9_000.0
    a = lobby.create("HOST")
    lobby.start(a["code"], a["player"], now=t0, seed=0x51)
    early = lobby.get(a["code"], now=t0)
    later = lobby.get(a["code"], now=t0 + 2.6)
    if not early.get("plates"):
        _fail("shared house lost the first plate")
    if early["plates"][0]["id"] != "p0":
        _fail("shared first plate left the pad")
    if len(later.get("plates") or []) < 2:
        _fail("shared house no longer advances by wall elapsed_ms")


def test_dt_matches_hz() -> None:
    if abs(DT - (1.0 / 128.0)) > 1e-12:
        _fail("named DT drifted from 128 Hz")
    steps = 128
    if abs(steps * DT - 1.0) > 1e-12:
        _fail("128 steps must be one second")


def main() -> int:
    try:
        test_named_rate_is_128()
        test_client_steps_local_sim_at_128()
        test_fire_never_waits_on_tick()
        test_shared_house_is_rewind_not_a_loop()
        test_dt_matches_hz()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("tick contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
