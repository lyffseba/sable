#!/usr/bin/env python3
"""Shared Bay 1v1: room owns score / pose / fire_ms rewind.

Fail loud if ENTER BAY cannot share first-to-5, if the room invents a
128 Hz friend loop, if local BAY / Offline / WARM UP die, if HID waits
on net, or if Bay becomes the only gun.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402
import lobby  # noqa: E402


def _fail(msg: str) -> None:
    raise AssertionError(f"SHARED BAY FAIL: {msg}")


def _fail_only_gun(msg: str) -> None:
    raise AssertionError(f"SHARED BAY FAIL: Bay became the only gun — {msg}")


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


def _a_uv_at_b() -> list[float]:
    ax, az = lobby.BAY_SPAWN_A
    bx, bz = lobby.BAY_SPAWN_B
    return list(lobby.bay_uv_for_world(bx, lobby.BAY_FOE_Y, bz, ax, az, "A"))


def test_two_clients_share_score_and_rewind() -> None:
    a = lobby.create("HOST")
    b = lobby.join(a["code"], "P2")
    t0 = 4_000.0
    st = lobby.start_bay(a["code"], a["player"], now=t0)
    if not st.get("ok") or st.get("phase") != "bay":
        _fail(f"start_bay {st}")
    if st.get("seed") is not None or st.get("plates"):
        _fail(f"ENTER BAY opened the shared house {st}")
    if st.get("to_win") != 5:
        _fail(f"shared Bay left first-to-5 {st}")
    seats = st.get("seats") or {}
    if seats.get(a["player"]) != "A" or seats.get(b["player"]) != "B":
        _fail(f"seats {seats}")
    if (st.get("scores") or {}).get(a["player"]) != 0:
        _fail("scores must start 0")

    view_a = lobby.get(a["code"], now=t0)
    view_b = lobby.get(a["code"], now=t0)
    if view_a.get("round") != view_b.get("round") or view_a.get("scores") != view_b.get("scores"):
        _fail(f"split bay views {view_a} vs {view_b}")

    house = lobby.start(a["code"], a["player"], now=t0)
    if house.get("ok"):
        _fail("ENTER RANGE must not steal a live bay match")

    other = lobby.create("HOST2")
    lobby.join(other["code"], "Q2")
    rng = lobby.start(other["code"], other["player"], now=t0, seed=1)
    if rng.get("phase") != "range":
        _fail("shared Range start died beside Bay")
    stolen = lobby.start_bay(other["code"], other["player"], now=t0)
    if stolen.get("ok"):
        _fail("start_bay must not overwrite a live house")

    lobby.pose(a["code"], a["player"], x=0.0, z=10.0, fire_ms=80.0, now=t0 + 0.10)
    lobby.pose(a["code"], b["player"], x=0.0, z=-10.0, fire_ms=80.0, now=t0 + 0.10)

    sky = lobby.hit(
        a["code"],
        a["player"],
        uv=[0.02, 0.02],
        fire_ms=90.0,
        t_hw=1,
        pose={"x": 0.0, "z": 10.0},
        now=t0 + 0.12,
    )
    if sky.get("hit") or not sky.get("miss"):
        _fail(f"sky ray must miss {sky}")
    if (lobby.get(a["code"], now=t0 + 0.12).get("scores") or {}).get(a["player"]) != 0:
        _fail("miss must not score")

    uv = _a_uv_at_b()
    shot = lobby.hit(
        a["code"],
        a["player"],
        uv=uv,
        fire_ms=100.0,
        t_hw=2,
        lifted=False,
        pose={"x": 0.0, "z": 10.0},
        now=t0 + 0.16,
    )
    if not shot.get("ok") or shot.get("hit") != b["player"]:
        _fail(f"rewind ray should hit seat B {shot}")
    after_a = lobby.get(a["code"], now=t0 + 0.16)
    after_b = lobby.get(a["code"], now=t0 + 0.16)
    if (after_a.get("scores") or {}).get(a["player"]) != 1:
        _fail(f"room must own YOU {after_a}")
    if after_a.get("scores") != after_b.get("scores"):
        _fail(f"score split {after_a} vs {after_b}")
    if after_a.get("round") != 2:
        _fail(f"a point must advance ROUND {after_a}")

    again = lobby.hit(
        a["code"],
        a["player"],
        uv=uv,
        fire_ms=110.0,
        pose={"x": 0.0, "z": 10.0},
        now=t0 + 0.20,
    )
    if again.get("hit"):
        _fail("freeze window must hold the next shot")

    outsider = lobby.hit(
        a["code"],
        "nobody",
        uv=uv,
        fire_ms=200.0,
        pose={"x": 0.0, "z": 10.0},
        now=t0 + 0.80,
    )
    if outsider.get("ok"):
        _fail("outsider must not write the booth")


def test_first_to_five_and_expose() -> None:
    a = lobby.create("HOST")
    b = lobby.join(a["code"], "P2")
    t0 = 8_000.0
    lobby.start_bay(a["code"], a["player"], now=t0)
    uv = _a_uv_at_b()
    now = t0
    for _ in range(4):
        now += 0.60
        fire_ms = (now - t0) * 1000.0 - 40.0
        lobby.pose(a["code"], b["player"], x=0.0, z=-10.0, fire_ms=fire_ms, now=now)
        shot = lobby.hit(
            a["code"],
            a["player"],
            uv=uv,
            fire_ms=fire_ms,
            pose={"x": 0.0, "z": 10.0},
            now=now + 0.04,
        )
        if not shot.get("hit"):
            _fail(f"point failed before match {shot}")
    if (lobby.get(a["code"], now=now + 0.04).get("scores") or {}).get(a["player"]) != 4:
        _fail("four hits must not end first-to-5")
    now += 0.60
    fire_ms = (now - t0) * 1000.0 - 40.0
    lobby.pose(a["code"], b["player"], x=0.0, z=-10.0, fire_ms=fire_ms, now=now)
    last = lobby.hit(
        a["code"],
        a["player"],
        uv=uv,
        fire_ms=fire_ms,
        pose={"x": 0.0, "z": 10.0},
        now=now + 0.04,
    )
    if not last.get("over") or (last.get("scores") or {}).get(a["player"]) != 5:
        _fail(f"fifth hit must MATCH {last}")

    c = lobby.create("HOST3")
    d = lobby.join(c["code"], "P3")
    t1 = 9_000.0
    lobby.start_bay(c["code"], c["player"], now=t1)
    fake = lobby.hit(
        c["code"],
        c["player"],
        fire_ms=90.0,
        pose={"x": 0.0, "z": 10.0},
        expose=True,
        now=t1 + 0.10,
    )
    if fake.get("expose") or (fake.get("scores") or {}).get(d["player"]):
        _fail(f"pad-side pose must not expose {fake}")
    died = lobby.hit(
        c["code"],
        c["player"],
        fire_ms=100.0,
        pose={"x": 0.0, "z": 0.0},
        expose=True,
        now=t1 + 0.14,
    )
    if not died.get("expose") or (died.get("scores") or {}).get(d["player"]) != 1:
        _fail(f"open middle must score THEM {died}")


def test_stale_and_warmup_and_local_clock() -> None:
    a = lobby.create("HOST")
    lobby.join(a["code"], "P2")
    t0 = 6_000.0
    lobby.start_bay(a["code"], a["player"], now=t0)
    late = lobby.hit(
        a["code"],
        a["player"],
        uv=_a_uv_at_b(),
        fire_ms=0.0,
        pose={"x": 0.0, "z": 10.0},
        now=t0 + 1.0,
    )
    if not late.get("miss") or not late.get("stale"):
        _fail(f"rewind older than the window must miss {late}")
    if (lobby.get(a["code"], now=t0 + 1.0).get("scores") or {}).get(a["player"]):
        _fail("stale miss must not invent a point")

    wait = lobby.create("HOST4")
    miss = lobby.hit(wait["code"], wait["player"], uv=_a_uv_at_b(), fire_ms=0)
    if miss.get("ok"):
        _fail("hit during wait must fail")
    warm = lobby.warmup(wait["code"], wait["player"])
    if warm.get("phase") != "wait" or warm.get("seats") or warm.get("scores"):
        _fail(f"warmup must not open the shared booth {warm}")
    pose = lobby.pose(wait["code"], wait["player"], x=0.0, z=10.0, fire_ms=0)
    if pose.get("ok"):
        _fail("pose during wait must fail")

    src = (ROOT / "tools/lobby.py").read_text(encoding="utf-8")
    if "time.sleep" in src:
        _fail("lobby.py sleeps — shared Bay is not a tick thread")
    bay_hit = re.search(r"def _bay_hit\([\s\S]*?\n\ndef hit\(", src)
    if not bay_hit:
        _fail("missing _bay_hit")
    body = bay_hit.group(0)
    if "range(128)" in body or "range(HZ)" in body:
        _fail("_bay_hit became a 128 Hz stepper")
    if "confidence" in body or "AimSample" in body:
        _fail("bay hit must not read cam quality or change AimSample")
    if "quantize_fire_ms" not in body:
        _fail("bay hit must snap fire_ms to sim Hz")
    if "bay_ray_from_uv" not in body or "BAY_FOE_RADIUS" not in body:
        _fail("bay hit must rewind and ray-test the peeked UV")
    pose_fn = re.search(r"def pose\([\s\S]*?\n\ndef get\(", src)
    if not pose_fn:
        _fail("missing pose mailbox")
    if "range(128)" in pose_fn.group(0):
        _fail("pose mailbox became a 128 Hz loop")


def test_client_keeps_local_and_hid() -> None:
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    js = proto_js()
    if 'id="btn-play"' not in html or ">OFFLINE<" not in html:
        _fail("boot lost one-click OFFLINE")
    offline = re.search(
        r'\$\("btn-play"\)\.addEventListener\("click", \(\) => \{[\s\S]*?play\("range"\)',
        js,
    )
    if not offline or "S.online = false" not in offline.group(0):
        _fail("OFFLINE must stay local one-click")
    if 'play("bay")' in offline.group(0):
        _fail_only_gun("OFFLINE was rerouted into Bay")
    if 'id="btn-bay"' not in html or ">BAY<" not in html:
        _fail_only_gun("boot lost BAY")
    if 'id="btn-lobby-warmup"' not in html or "WARM UP" not in html:
        _fail_only_gun("lobby lost WARM UP")
    if 'id="btn-lobby-range"' not in html or "ENTER RANGE" not in html:
        _fail_only_gun("lobby lost ENTER RANGE")
    if 'id="btn-lobby-bay"' not in html or "ENTER BAY" not in html:
        _fail_only_gun("lobby lost ENTER BAY")

    boot_bay = re.search(r'\$\("btn-bay"\)[\s\S]{0,220}?play\("bay"\)', js)
    if not boot_bay or "S.online = false" not in boot_bay.group(0):
        _fail("boot BAY trapped HID behind a room")
    if "/api/lobby" in boot_bay.group(0):
        _fail("boot BAY must stay free of /api/lobby/*")

    start_bay = _js_fn(js, "lobbyStartBay")
    if "/api/lobby/start\"" in start_bay or "/api/lobby/start'" in start_bay:
        _fail("ENTER BAY started the shared house")
    if "/api/lobby/bay" not in start_bay:
        _fail("host ENTER BAY must fire-and-forget /api/lobby/bay")
    if re.search(r"await\s+", start_bay) or "async function lobbyStartBay" in js:
        _fail("ENTER BAY awaits net — lift/HID is behind the lobby")
    if 'play("bay")' not in start_bay and 'setPhase("bay")' not in start_bay:
        _fail_only_gun("ENTER BAY no longer drops into the booth")
    if "stepSim" in start_bay or "simAcc" in start_bay or re.search(r"setTimeout", start_bay):
        _fail("ENTER BAY grew a tick tax")

    fire = _js_fn(js, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if "reportSharedBayFire" not in fire:
        _fail("shared Bay must send the peeked AimBus intent")
    if "/api/lobby" in fire or re.search(r"\bfetch\s*\(", fire):
        _fail("fire() talks to net — HID is behind the lobby")
    if re.search(r"await\s+", fire):
        _fail("fire() awaits — HID is behind a promise")

    bay = _js_fn(js, "fireBay3D")
    if "fetch(" in bay or "/api/lobby" in bay:
        _fail("local fireBay3D talks to net — boot BAY would wait on the lobby")
    if "committedSimMs" not in bay or "Bay.fireMs" not in bay:
        _fail("Bay fire_ms must speak the last committed sim tick")

    report = _js_fn(js, "reportSharedBayFire")
    if "await" in report:
        _fail("reportSharedBayFire must be fire-and-forget")
    if "/api/lobby/hit" not in report:
        _fail("shared Bay fire must POST the intent")
    if "committedSimMs" not in report:
        _fail("shared Bay fire_ms must speak sim Hz")
    if "performance.now()" in report or "S.rangeStart" in report:
        _fail("shared Bay fire_ms couples to present")
    if "confidence" in report or "plate:" in report:
        _fail("do not send cam confidence or plate id")
    if "Bay.pos" not in report:
        _fail("intent must include last committed booth pose")

    pose = _js_fn(js, "reportSharedBayPose")
    if "await" in pose:
        _fail("pose mailbox must be fire-and-forget")
    if "/api/lobby/pose" not in pose:
        _fail("shared Bay must POST last committed pose on the lazy poll")
    step = _js_fn(js, "stepSim")
    if "reportSharedBayPose" in step or "/api/lobby/pose" in step:
        _fail("pose mailbox leaked onto the 128 Hz step — friend loop")
    if "reportSharedBayFire" in step:
        _fail("stepSim must not shoot the shared booth")

    start = _js_fn(js, "startBay")
    if "S.simTick = 0" not in start:
        _fail("startBay must reset the sim tick — fire at tick 0 is legal")
    if "sharedBay()" not in start:
        _fail("startBay must branch shared vs local")

    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/bay" in warm or "/api/lobby/start" in warm:
        _fail("WARM UP must stay local practice")
    if re.search(r"await\s+", warm):
        _fail("WARM UP soft-locked behind net")

    poll = _js_fn(js, "lobbyPoll")
    if 'phase === "bay"' not in poll:
        _fail("lobby poll must not yank local Bay into shared Range")
    if "applySharedBay" not in poll:
        _fail("lobby poll must apply the room-owned booth snapshot")

    hud = _js_fn(js, "drawBayHUD")
    if '"YOU "' not in hud or '"THEM "' not in hud:
        _fail("shared Bay HUD lost YOU/THEM")
    if '"ROUND "' not in hud and '"ROUND"' not in hud:
        _fail("shared Bay HUD lost ROUND")
    if "WASD on PAD" in hud or "RAISE YOUR HAND" in hud:
        _fail("tutorial wall over live aim")

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
    if "room owns" not in modes.lower() and "room-owned" not in modes.lower():
        _fail("docs/modes.md must name room-owned shared Bay")
    if "/api/lobby/start" not in modes:
        _fail("docs/modes.md must keep ENTER BAY off the shared house start")
    if "FIRST TO 5" not in modes or "SableHUD" not in modes:
        _fail("docs/modes.md must keep thin Bay chips")
    if "never the only gun" not in modes.lower() and "never replaces gallery" not in modes:
        _fail("docs/modes.md must keep Bay from replacing gallery")
    if "128 Hz friend" not in tick.lower() and "friend loop" not in tick.lower():
        _fail("docs/tick.md must keep shared Bay off a 128 Hz friend loop")
    if "fire_ms" not in bay.lower() and "committedSimMs" not in bay:
        _fail("docs/maps/bay.md must keep fire_ms on the sim tick")
    if "test_shared_bay.py" not in bible:
        _fail("PRODUCTION.md must fail loud through test_shared_bay.py")
    if "M9" not in bible:
        _fail("PRODUCTION.md must stand the shared Bay milestone")
    if "M8" not in bible:
        _fail("do not drop the local Bay R6 M8 stand")
    if "v0.20.0" not in bible:
        _fail("do not drop the SableHUD v0.20.0 stand")
    ci = (ROOT / "tools/ci.sh").read_text(encoding="utf-8")
    if "test_shared_bay.py" not in ci:
        _fail("ci.sh must run the shared Bay lock")
    serve = (ROOT / "tools/serve_proto.py").read_text(encoding="utf-8")
    if "/api/lobby/bay" not in serve or "start_bay" not in serve:
        _fail("serve_proto must expose /api/lobby/bay")
    if "/api/lobby/pose" not in serve:
        _fail("serve_proto must expose the pose mailbox")


def main() -> int:
    try:
        test_two_clients_share_score_and_rewind()
        test_first_to_five_and_expose()
        test_stale_and_warmup_and_local_clock()
        test_client_keeps_local_and_hid()
        test_docs_and_ci()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("shared bay ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
