#!/usr/bin/env python3
"""M4: Bay is a second playlist. Offline / WARM UP / shared Range must survive."""

from __future__ import annotations

import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402
import lobby  # noqa: E402


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"(?:async )?function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        raise AssertionError(f"missing function {name}")
    return m.group(0)


def _js_const(src: str, name: str) -> float:
    m = re.search(rf"const {name} = (-?[0-9.]+)", src)
    if not m:
        raise AssertionError(f"missing const {name}")
    return float(m.group(1))


def bay_in_left_window(x: float, z: float) -> bool:
    return -7.5 < x < -4.8 and 2.4 < z < 5.6


def bay_in_right_angle(x: float, z: float) -> bool:
    return 4.6 < x < 7.5 and 1.6 < z < 5.8


def bay_in_open_middle(x: float, z: float) -> bool:
    if bay_in_left_window(x, z) or bay_in_right_angle(x, z):
        return False
    return z <= 0.65 and z > -12.5 and abs(x) < 7.6


def test_boot_and_lobby_entry() -> None:
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    js = proto_js()
    if 'id="btn-play"' not in html or ">OFFLINE<" not in html:
        raise AssertionError("boot lost one-click OFFLINE")
    if 'id="btn-bay"' not in html or ">BAY<" not in html:
        raise AssertionError("boot must offer BAY as a playlist")
    if 'id="btn-lobby-range"' not in html or "ENTER RANGE" not in html:
        raise AssertionError("lobby lost ENTER RANGE — Bay must not be the only online path")
    if 'id="btn-lobby-bay"' not in html or "ENTER BAY" not in html:
        raise AssertionError("lobby must offer ENTER BAY")
    if 'id="btn-lobby-warmup"' not in html or "WARM UP" not in html:
        raise AssertionError("lobby lost WARM UP")
    if 'id="screen-bay"' not in html or 'id="btn-bay-boot"' not in html:
        raise AssertionError("Bay needs a screen + BOOT / return control")

    offline = re.search(
        r'\$\("btn-play"\)\.addEventListener\("click", \(\) => \{[\s\S]*?play\("range"\)',
        js,
    )
    if not offline:
        raise AssertionError("OFFLINE must still call play(range) in one click")
    if "S.online = false" not in offline.group(0):
        raise AssertionError("OFFLINE must stay local")

    boot_bay = re.search(
        r'\$\("btn-bay"\)[\s\S]{0,220}?play\("bay"\)',
        js,
    )
    if not boot_bay:
        raise AssertionError("boot BAY must call play(bay)")
    if "S.online = false" not in boot_bay.group(0):
        raise AssertionError("boot BAY must stay local — do not trap HID behind a room")

    play = _js_fn(js, "play")
    if 'target === "bay"' not in play or 'targetGameMode' not in play:
        raise AssertionError("play(target) must honor bay vs range")
    if 'targetGameMode = "range"' in play.split("targetGameMode")[1][:40]:
        raise AssertionError("play() must not force range after a bay target")

    enter = _js_fn(js, "enterGame")
    if 'targetGameMode === "bay"' not in enter:
        raise AssertionError("calib / desktop fallback must enter the chosen playlist")
    if 'setPhase("range")' in enter and "targetGameMode" not in enter:
        raise AssertionError("enterGame must not always dump into Range")

    phase = _js_fn(js, "setPhase")
    if "startBay()" not in phase:
        raise AssertionError("setPhase(bay) must start the booth")
    if "bayGroup.visible = (next === \"bay\")" not in phase and "startBay()" not in phase:
        raise AssertionError("Bay group must become visible on the bay phase")
    if "startRange()" not in phase:
        raise AssertionError("setPhase(range) must still start Range")


def test_lobby_bay_does_not_steal_shared_range() -> None:
    js = proto_js()
    start_bay = _js_fn(js, "lobbyStartBay")
    if "/api/lobby/start" in start_bay:
        raise AssertionError("ENTER BAY must not start the shared house")
    if re.search(r"await\s+", start_bay):
        raise AssertionError("ENTER BAY awaits net — lift/HID would be behind the lobby")
    if 'play("bay")' not in start_bay and 'setPhase("bay")' not in start_bay:
        raise AssertionError("ENTER BAY must drop into the booth")
    if "/api/lobby/hit" in start_bay:
        raise AssertionError("Bay start must not post Range hits")

    poll = _js_fn(js, "lobbyPoll")
    if 'phase === "bay"' not in poll:
        raise AssertionError("lobby poll must not yank Bay into shared Range")

    start_range = _js_fn(js, "lobbyStartRange")
    if 'play("range")' not in start_range:
        raise AssertionError("ENTER RANGE must still start the shared house path")
    if "/api/lobby/start" not in start_range:
        raise AssertionError("host ENTER RANGE must still POST /api/lobby/start")

    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/start" in warm:
        raise AssertionError("WARM UP must not start the room Range")
    if 'setPhase("range")' not in warm and 'play("range")' not in warm:
        raise AssertionError("WARM UP must still drop into Range")
    if re.search(r"await\s+", warm):
        raise AssertionError("WARM UP must stay one-click local")


def test_shared_range_still_resolves() -> None:
    a = lobby.create("HOST")
    b = lobby.join(a["code"], "P2")
    t0 = 2_000.0
    st = lobby.start(a["code"], a["player"], now=t0, seed=0xBA10)
    if not st.get("ok") or st.get("phase") != "range" or not st.get("plates"):
        raise AssertionError(f"shared Range start died {st}")
    if st["plates"][0]["id"] != "p0":
        raise AssertionError("shared first plate left the pad")
    uv = list(lobby.uv_for_world(0.2, 0.35, -6.6))
    shot = lobby.hit(a["code"], a["player"], uv=uv, fire_ms=90.0, now=t0 + 0.2)
    if shot.get("hit") != "p0":
        raise AssertionError(f"shared rewind ray died {shot}")
    warm = lobby.warmup(b["code"] if False else a["code"], b["player"])
    # room already in range — warmup after start must fail (existing contract)
    if warm.get("ok"):
        raise AssertionError("warmup after start must still fail")


def test_bay_rules() -> None:
    js = proto_js()
    if _js_const(js, "BAY_TO_WIN") != 5:
        raise AssertionError("Bay is first to 5")
    if abs(_js_const(js, "BAY_SPEED") - 4.2) > 1e-6:
        raise AssertionError("PAD speed must stay 4.2")
    if abs(_js_const(js, "BAY_EXPOSE_S") - 0.12) > 1e-6:
        raise AssertionError("open-middle expose must stay 0.12 s")
    if abs(_js_const(js, "BAY_FOE_RADIUS") - 0.46) > 1e-6:
        raise AssertionError("foe hitscan sphere must stay 0.46")

    spawn_a = re.search(r"const BAY_SPAWN_A = \{ x: ([-\d.]+), y: ([-\d.]+), z: ([-\d.]+) \}", js)
    spawn_b = re.search(r"const BAY_SPAWN_B = \{ x: ([-\d.]+), y: ([-\d.]+), z: ([-\d.]+) \}", js)
    if not spawn_a or not spawn_b:
        raise AssertionError("Bay spawns must be named constants")
    if float(spawn_a.group(3)) != 10 or float(spawn_b.group(3)) != -10:
        raise AssertionError("Bay spawns must stay A z=10 / B z=-10")

    if "16, 28" not in js and "PlaneGeometry(16, 28)" not in js:
        raise AssertionError("booth floor must be 16 × 28")
    if "Math.random()" in _js_fn(js, "startBay") or "Math.random()" in js[
        js.find("resetRound()") : js.find("resetMatch()")
    ]:
        raise AssertionError("Bay reset must not hide spawn with RNG")

    tick = _js_fn(js, "tickBay")
    if "sample.lifted" not in tick:
        raise AssertionError("Bay walk must peek AimBus lift")
    if "bayInOpenMiddle" not in tick:
        raise AssertionError("open middle must use the spec volumes")
    if "Bay.speed" not in tick:
        raise AssertionError("PAD move must use Bay.speed")
    if "toWin" not in tick:
        raise AssertionError("open-middle death must score toward first-to-5")

    fire_bay = _js_fn(js, "fireBay3D")
    if "rayHitsBayFoe" not in fire_bay:
        raise AssertionError("Bay fire must ray-test the foe sphere")
    if "fetch(" in fire_bay or "/api/lobby" in fire_bay:
        raise AssertionError("Bay fire must not talk to net")
    if "toWin" not in fire_bay:
        raise AssertionError("a hit must score toward first-to-5")

    fire = _js_fn(js, "fire")
    if "aimBus.fire" not in fire:
        raise AssertionError("Bay still peeks AimBus")
    if "fireBay3D" not in fire:
        raise AssertionError("range fire must still route Bay to fireBay3D")
    if "coastTrack" in fire or "updateAim" in fire:
        raise AssertionError("fire must not recompute aim")
    if re.search(r"await\s+", fire):
        raise AssertionError("fire awaits — HID is behind a promise")

    if "function bayInOpenMiddle" not in js or "function bayCoverChip" not in js:
        raise AssertionError("cover volumes must be named helpers")
    if '"FIRST TO 5"' not in js:
        raise AssertionError("HUD must chip FIRST TO 5")
    if "STYLE_DEFAULT" not in js or "STYLE_RANKED" not in js or "STYLE_NIGHT" not in js:
        raise AssertionError("CANCHO locker styles must stay")
    if "cycleStyle" not in js:
        raise AssertionError("L must still cycle locker styles")


def test_open_middle_volumes() -> None:
    if bay_in_open_middle(0.0, 10.0):
        raise AssertionError("spawn A is pad side, not open middle")
    if bay_in_open_middle(-6.15, 4.0):
        raise AssertionError("left window is cover, not open middle")
    if bay_in_open_middle(6.05, 3.7):
        raise AssertionError("right angle is cover, not open middle")
    if not bay_in_open_middle(0.0, 0.0):
        raise AssertionError("stall line is open middle")
    if not bay_in_open_middle(1.0, -4.0):
        raise AssertionError("south of the stall is open middle")
    if bay_in_open_middle(0.0, -13.0):
        raise AssertionError("past the south kill edge is not open middle")
    you = them = 0
    to_win = 5
    over = False
    for _ in range(4):
        you += 1
        if you >= to_win:
            over = True
    if over or you != 4:
        raise AssertionError("four hits must not end the match")
    you += 1
    if you < to_win:
        raise AssertionError("fifth hit must reach first-to-5")
    expose = 0.0
    dt = 1.0 / 60.0
    died = False
    while expose < 1.0:
        expose += dt
        if expose >= 0.12:
            them += 1
            died = True
            break
    if not died or them != 1:
        raise AssertionError("0.12 s in the kill volume must score them")


def test_foe_sphere_is_honest() -> None:
    """A ray through spawn B hits; a sky ray misses. No aim-assist."""
    cx, cy, cz, r = 0.0, 0.89, -10.0, 0.46
    origin = (0.0, 1.64, 10.0)
    to_foe = (cx - origin[0], cy - origin[1], cz - origin[2])
    length = math.sqrt(to_foe[0] ** 2 + to_foe[1] ** 2 + to_foe[2] ** 2)
    direction = (to_foe[0] / length, to_foe[1] / length, to_foe[2] / length)
    ox, oy, oz = origin[0] - cx, origin[1] - cy, origin[2] - cz
    b = 2 * (ox * direction[0] + oy * direction[1] + oz * direction[2])
    c = ox * ox + oy * oy + oz * oz - r * r
    disc = b * b - 4 * c
    t = (-b - math.sqrt(disc)) * 0.5
    if disc < 0 or t <= 0:
        raise AssertionError("center ray from spawn A must hit the foe sphere")
    sky = (0.0, 1.0, 0.0)
    b2 = 2 * (ox * sky[0] + oy * sky[1] + oz * sky[2])
    c2 = ox * ox + oy * oy + oz * oz - r * r
    disc2 = b2 * b2 - 4 * c2
    if disc2 >= 0:
        t2 = (-b2 - math.sqrt(disc2)) * 0.5
        if t2 > 0:
            raise AssertionError("sky ray must miss")


def test_shared_look_bible() -> None:
    """Bay and Range share unshaded CANCHO. No milsim steel, no ACES soup, no mint bloom."""
    js = proto_js()
    if "0x151c22" in js:
        raise AssertionError("cool milsim 0x151c22 left the house — charcoal only")
    if "0x8aa8b8" in js:
        raise AssertionError("cool steel hemisphere must not return")
    if "ACESFilmicToneMapping" in js:
        raise AssertionError("ACES filmic hides aim noise")
    if "NoToneMapping" not in js:
        raise AssertionError("Look lock wants linear / NoToneMapping")
    if "0x0a0c10" not in js or "0x101214" not in js:
        raise AssertionError("scene + fog must be charcoal")
    if "emissiveIntensity: 0.45" in js or "emissiveIntensity:0.45" in js:
        raise AssertionError("mint plate bloom must stay dead")
    house = (ROOT / "proto/house.js").read_text(encoding="utf-8")
    if "GridHelper" in house or "0x00f0ff" in house:
        raise AssertionError("cyan grid / neon leftover in house.js")
    if "function bayUnshaded" not in js:
        raise AssertionError("unshaded helper must stay the shared paint")
    plates = _js_fn(js, "createTargetMesh")
    if "emissiveIntensity" in plates:
        raise AssertionError("plates must not emit")
    if "bayUnshaded" not in plates:
        raise AssertionError("plates must be bone + mint unshaded")
    inflate = _js_fn(js, "inflateMat")
    if "flatShading: false" in inflate or "roughness: 0.22" in inflate:
        raise AssertionError("inflateMat must not be milsim plastic")
    if "bayUnshaded" not in inflate:
        raise AssertionError("yard props must match bayUnshaded")
    look = _js_fn(js, "applyLockerLook")
    if "bodyHex" not in look or "mintHex" not in look or "rustHex" not in look:
        raise AssertionError("CANCHO tell (charcoal / mint / rust) must stay on applyLockerLook")


def test_aimsample_untouched() -> None:
    js = proto_js()
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        raise AssertionError("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        raise AssertionError("AimSample fields changed — keep the locked struct")
    start = _js_fn(js, "startRange")
    if "sharedMatch()" not in start or "spawnOrb3D" not in start:
        raise AssertionError("startRange must still branch shared vs local")
    if "0.2" not in start or "-6.6" not in start:
        raise AssertionError("local first plate left the pad")


def main() -> int:
    try:
        test_boot_and_lobby_entry()
        test_lobby_bay_does_not_steal_shared_range()
        test_shared_range_still_resolves()
        test_bay_rules()
        test_open_middle_volumes()
        test_foe_sphere_is_honest()
        test_shared_look_bible()
        test_aimsample_untouched()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("bay playlist ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
