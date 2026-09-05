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
    if "simTick: 0" not in js or "simHz: 128" not in js:
        _fail("S lost the sim tick mailbox")
    step = _fn(js, "stepSim")
    if re.search(r"function stepSim\s*\(\s*now", step) or re.search(
        r"function stepSim\s*\(\s*t\b", step
    ):
        _fail("stepSim still takes rAF present — sim hitch to frame time")
    if "performance.now" in step or "lastT" in step:
        _fail("stepSim hitch to wall / rAF present")
    if "S.simTick +" not in step and "S.simTick++" not in step:
        _fail("stepSim must own S.simTick")
    if "updateRange(SIM_DT" not in step:
        _fail("stepSim must advance Range at SIM_DT")
    if "tickBay(SIM_DT" not in step:
        _fail("stepSim must advance Bay at SIM_DT")
    if "simMs()" not in step:
        _fail("Range elapsed must be committed sim ms, not rAF now")
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
    if "stepSim(t)" in frame or "stepSim(now)" in frame:
        _fail("rAF present leaked into stepSim")
    drain = re.search(r"while \(simAcc >= SIM_DT\) \{[\s\S]*?\}", frame)
    if not drain or "stepSim()" not in drain.group(0):
        _fail("rAF must drain simAcc through stepSim only")
    if re.search(r"\bfire\s*\(", drain.group(0)):
        _fail("sim drain loop shoots — HID fire leaked onto the tick")
    ranged = _fn(js, "updateRange")
    if "now - S.rangeStart" in ranged:
        _fail("updateRange elapsed hitch to wall rangeStart")
    if "performance.now" in ranged:
        _fail("updateRange hitch to present")


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
    if "stepSim" in warm or "simAcc" in warm or re.search(r"setTimeout", warm):
        _fail("WARM UP grew a tick tax")
    if re.search(r"if\s*\(\s*!S\.simTick", fire) or "simTick <" in fire:
        _fail("fire waits on the first sim step — Offline tax")
    if "budgetMs: 8" not in js:
        _fail("HID→hitscan 8 ms p99 bar left the probe")


def test_fire_ms_speaks_sim_hz_not_present() -> None:
    js = proto_js()
    report = _fn(js, "reportSharedFire")
    if "performance.now()" in report:
        _fail("fire_ms couples to present")
    if "S.rangeStart" in report:
        _fail("fire_ms couples to rAF rangeStart")
    if "committedSimMs" not in report and "simTick" not in report:
        _fail("fire_ms must speak the last committed sim tick")
    bay = _fn(js, "fireBay3D")
    if "committedSimMs" not in bay or "Bay.fireMs" not in bay:
        _fail("Bay fire_ms must stamp the last committed sim tick")
    if "performance.now" in bay or "S.rangeStart" in bay:
        _fail("Bay fire_ms couples to present")
    fire = _fn(js, "fire")
    if "performance.now() - S.rangeStart" in fire:
        _fail("fire couples to present")
    src = (ROOT / "tools/lobby.py").read_text(encoding="utf-8")
    if "def quantize_fire_ms" not in src or "SIM_HZ = 128" not in src:
        _fail("lobby rewind lost the 128 Hz fire_ms grid")
    hit_at = src.find("def hit(")
    if hit_at < 0 or "quantize_fire_ms" not in src[hit_at:]:
        _fail("lobby.hit must snap fire_ms to sim Hz, not rAF present")
    dt = 1000.0 / 128.0
    base = lobby.quantize_fire_ms(90.0)
    a = lobby.quantize_fire_ms(base + 0.01)
    b = lobby.quantize_fire_ms(base + dt - 0.01)
    if a != b or a != base:
        _fail("mid-tick fire_ms must snap to the same committed tick")
    if abs(a / dt - round(a / dt)) > 1e-9:
        _fail("quantized fire_ms must land on the 128 Hz grid")
    if lobby.quantize_fire_ms(0) != 0.0:
        _fail("tick 0 fire_ms must stay 0 — Offline has no first-step tax")


def test_shared_house_is_rewind_not_a_loop() -> None:
    src = (ROOT / "tools/lobby.py").read_text(encoding="utf-8")
    if "def _pose_at" not in src or "def _sync_sim" not in src:
        _fail("shared house lost closed-form pose / sync")
    if "time.sleep" in src:
        _fail("lobby.py sleeps — shared house is not a tick thread")
    pose_m = re.search(r"def _pose_at\([\s\S]*?\n\ndef ", src)
    if not pose_m:
        _fail("missing _pose_at")
    pose = pose_m.group(0)
    if "born_ms" not in pose or "life" not in pose:
        _fail("_pose_at must stay closed-form at elapsed_ms")
    if "sit_pose_y" not in pose:
        _fail("_pose_at must use closed-form sit_pose_y — sit Y is house authority")
    if "flyer_pose" not in pose:
        _fail("_pose_at must use closed-form flyer_pose — flyer Y is house authority")
    if "for " in pose and "range(" in pose:
        _fail("_pose_at stepped a tick loop — rewind died")
    if abs(lobby.sit_pose_y(0.35, 0.0) - 0.35) > 1e-12:
        _fail("sit_pose_y(life 0) must stay on the pad")
    if "def sit_pose_y" not in src or "math.sin" not in src:
        _fail("sit_pose_y must stay closed-form")
    born = lobby.flyer_pose(0.0, 1.0, -6.0, 0.0, 1.4, 0.0, 0.0)
    if abs(born["y"] - 1.0) > 1e-12:
        _fail("flyer_pose(life 0) must stay on birth")
    if abs(lobby.flyer_pose(0.0, 1.0, -6.0, 0.0, 1.4, 0.0, 1.0)["y"] - (1.0 + 1.4 - 0.5 * lobby.GRAVITY)) > 1e-12:
        _fail("flyer_pose must stay closed-form y0+vy0*t-0.5*g*t^2")
    if "def flyer_pose" not in src or "0.5 * GRAVITY" not in src:
        _fail("flyer_pose must stay closed-form")
    sync = re.search(r"def _sync_sim\([\s\S]*?return elapsed_ms\n", src)
    if not sync:
        _fail("missing _sync_sim")
    if "range(HZ)" in sync.group(0) or "range(128)" in sync.group(0):
        _fail("_sync_sim became a 128 Hz stepper")
    if "quantize_fire_ms" in sync.group(0):
        _fail("snapshot sync quantized — snapshot must stay a view")
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
    view = lobby.get(a["code"], now=t0 + 0.201)
    view_ms = view.get("elapsed_ms")
    if view_ms is None:
        _fail("snapshot lost elapsed_ms")
    if abs(float(view_ms) - lobby.quantize_fire_ms(view_ms)) < 1e-6:
        _fail(f"snapshot must stay a wall view, not a tick grid {view_ms}")
    uv = [p for p in (later.get("plates") or []) if p["id"] == "p0"]
    shot = lobby.hit(
        a["code"],
        a["player"],
        uv=lobby.uv_for_world(0.2, 0.35, -6.6),
        fire_ms=90.0,
        t_hw=1,
        now=t0 + 0.22,
    )
    if not shot.get("ok") or shot.get("hit") != "p0":
        _fail(f"quantized rewind must still hit the pad plate {shot}")
    dead = lobby.get(a["code"], now=t0 + 0.22).get("dead") or []
    at = next((d.get("at_ms") for d in dead if d.get("id") == "p0"), None)
    if at is None or abs(float(at) - lobby.quantize_fire_ms(90.0)) > 1e-9:
        _fail(f"dead.at_ms must be the quantized sim tick, not rAF 90 {at}")


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
        test_fire_ms_speaks_sim_hz_not_present()
        test_shared_house_is_rewind_not_a_loop()
        test_dt_matches_hz()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("tick contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
