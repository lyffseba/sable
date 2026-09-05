#!/usr/bin/env python3
"""R4: shared seed + server ray resolve at the fire tick. Warm-up stays local.

Seed owns kind / peek / velocity / born_ms. A late first poll must not shift birth.
"""

from __future__ import annotations

import math
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lobby  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        raise AssertionError(f"missing function {name}")
    return m.group(0)


def _ids(snap: dict) -> list[str]:
    return [p["id"] for p in snap.get("plates") or []]


def _p0_uv(aspect: float = lobby.DEFAULT_ASPECT) -> list[float]:
    return list(lobby.uv_for_world(0.2, 0.35, -6.6, aspect))


def test_two_clients_share_seed_and_ray_hit() -> None:
    a = lobby.create("HOST")
    b = lobby.join(a["code"], "P2")
    t0 = 1_000.0
    st = lobby.start(a["code"], a["player"], now=t0, seed=0xC0FFEE)
    if not st.get("ok") or st.get("phase") != "range" or st.get("hangar") != "match_live":
        raise AssertionError(f"start {st}")
    if st.get("seed") != 0xC0FFEE:
        raise AssertionError(f"seed {st.get('seed')}")
    if _ids(st) != ["p0"]:
        raise AssertionError(f"first plate {_ids(st)}")
    p0 = st["plates"][0]
    if abs(p0["x"] - 0.2) > 1e-6 or abs(p0["z"] + 6.6) > 1e-6:
        raise AssertionError(f"p0 not on the shared pad {p0}")

    view_a = lobby.get(a["code"], now=t0)
    view_b = lobby.get(a["code"], now=t0)
    if view_a["seed"] != view_b["seed"] or _ids(view_a) != _ids(view_b):
        raise AssertionError(f"split views {view_a} vs {view_b}")

    later_a = lobby.get(a["code"], now=t0 + 2.6)
    later_b = lobby.get(a["code"], now=t0 + 2.6)
    if _ids(later_a) != _ids(later_b) or later_a["seed"] != later_b["seed"]:
        raise AssertionError(f"spawn desync {_ids(later_a)} vs {_ids(later_b)}")
    if len(_ids(later_a)) < 2:
        raise AssertionError(f"expected a second shared plate {_ids(later_a)}")

    other = lobby.create("HOST2")
    lobby.join(other["code"], "Q2")
    lobby.start(other["code"], other["player"], now=t0, seed=0xC0FFEE)
    twin_later = lobby.get(other["code"], now=t0 + 2.6)
    if _ids(twin_later) != _ids(later_a):
        raise AssertionError(f"same seed must spawn same ids {_ids(twin_later)} vs {_ids(later_a)}")

    uv = _p0_uv()
    sky = [0.02, 0.02]
    # Plate id is not authority — a sky ray must miss even if someone names p0.
    fake = lobby.hit(
        a["code"],
        a["player"],
        uv=sky,
        fire_ms=100.0,
        t_hw=1,
        now=t0 + 0.12,
        plate="p0",
    )
    if fake.get("hit") or "p0" not in _ids(lobby.get(a["code"], now=t0 + 0.12)):
        raise AssertionError(f"sky ray must miss {fake}")

    # Resolve later, rewind to the fire tick. Miss stays miss if the UV missed then.
    miss = lobby.hit(
        a["code"],
        a["player"],
        uv=sky,
        fire_ms=80.0,
        t_hw=2,
        now=t0 + 0.20,
    )
    if not miss.get("miss") or miss.get("hit"):
        raise AssertionError(f"miss must stay miss {miss}")
    if "p0" not in _ids(lobby.get(a["code"], now=t0 + 0.20)):
        raise AssertionError("miss must not shatter")

    shot = lobby.hit(
        a["code"],
        a["player"],
        uv=uv,
        fire_ms=90.0,
        t_hw=3,
        lifted=False,
        now=t0 + 0.22,
    )
    if not shot.get("ok") or shot.get("hit") != "p0":
        raise AssertionError(f"rewind ray should hit p0 {shot}")
    after_a = lobby.get(a["code"], now=t0 + 0.22)
    after_b = lobby.get(a["code"], now=t0 + 0.22)
    if "p0" in _ids(after_a) or "p0" in _ids(after_b):
        raise AssertionError(f"dead plate still live {_ids(after_a)} {_ids(after_b)}")
    dead_a = [d["id"] for d in after_a.get("dead") or []]
    dead_b = [d["id"] for d in after_b.get("dead") or []]
    if "p0" not in dead_a or dead_a != dead_b:
        raise AssertionError(f"dead set split {dead_a} vs {dead_b}")

    again = lobby.hit(a["code"], b["player"], uv=uv, fire_ms=100.0, now=t0 + 0.24)
    if again.get("hit"):
        raise AssertionError("second ray on a dead plate must not hit")

    outsider = lobby.hit(a["code"], "nobody", uv=uv, fire_ms=100.0, now=t0 + 0.24)
    if outsider.get("ok"):
        raise AssertionError("outsider must not write the house")


def test_stale_fire_tick_is_miss() -> None:
    a = lobby.create("HOST")
    t0 = 5_000.0
    lobby.start(a["code"], a["player"], now=t0, seed=1)
    late = lobby.hit(
        a["code"],
        a["player"],
        uv=_p0_uv(),
        fire_ms=0.0,
        now=t0 + 1.0,
    )
    if not late.get("miss") or not late.get("stale"):
        raise AssertionError(f"rewind older than the window must miss {late}")
    if "p0" not in _ids(lobby.get(a["code"], now=t0 + 1.0)):
        raise AssertionError("stale miss must not invent a shatter")


def test_warmup_stays_local() -> None:
    a = lobby.create("HOST")
    b = lobby.join(a["code"], "P2")
    warm = lobby.warmup(a["code"], b["player"])
    if warm.get("phase") != "wait" or warm.get("hangar") != "wait_practice" or "seed" in warm or warm.get("plates") or warm.get("scores"):
        raise AssertionError(f"warmup must not open the shared sim {warm}")
    g = lobby.get(a["code"])
    if g.get("phase") != "wait" or "seed" in g or g.get("plates") or g.get("scores"):
        raise AssertionError(f"wait get leaked sim {g}")
    miss = lobby.hit(a["code"], a["player"], uv=_p0_uv(), fire_ms=0)
    if miss.get("ok"):
        raise AssertionError("hit during wait must fail")


def test_hit_uses_sample_not_cam() -> None:
    src = (ROOT / "tools/lobby.py").read_text(encoding="utf-8")
    fn = re.search(r"def hit\([^)]*\)[^:]*:([\s\S]+)$", src)
    if not fn:
        raise AssertionError("missing lobby.hit")
    body = fn.group(1)
    if "confidence" in body or "AimSample" in body:
        raise AssertionError("hit must not read cam quality or change AimSample")
    if "del plate" not in body:
        raise AssertionError("plate id must not be authority")
    if "_hitscan" not in body or "fire_tick" not in body:
        raise AssertionError("hit must rewind and ray-test the peeked UV")


def test_client_keeps_local_practice_and_hid() -> None:
    js = proto_js()
    fire = _js_fn(js, "fire")
    if "await" in fire:
        raise AssertionError("shared fire must not await inside fire()")
    if "coastTrack" in fire or "updateAim" in fire:
        raise AssertionError("fire must still peek only")
    if "reportSharedFire" not in fire:
        raise AssertionError("shared range must send the peeked AimBus intent")
    report = _js_fn(js, "reportSharedFire")
    if "await" in report:
        raise AssertionError("reportSharedFire must be fire-and-forget")
    if "/api/lobby/hit" not in report:
        raise AssertionError("reportSharedFire posts the intent")
    if "shot.uv" not in report or "fire_ms" not in report or "t_hw" not in report:
        raise AssertionError("intent must be last committed UV + fire tick")
    if "hitscanRange" not in fire:
        raise AssertionError("local hitscan must be the house sphere")
    if "intersectObjects" in fire:
        raise AssertionError("local hitscan must not mesh-test the spun hex")
    intersect = fire.find("hitscanRange(")
    mark_range = fire.find("SablePerf.markHid", intersect)
    if intersect < 0 or mark_range < 0 or mark_range < intersect:
        raise AssertionError("HID→hitscan must mark at the house sphere")
    probe = fire[intersect:mark_range]
    if "applyGunKick" in probe or "peekMuzzleWorld" in probe or "getWorldPosition" in probe:
        raise AssertionError("Look landed inside the HID→hitscan probe")
    if "performance.now()" in report or "S.rangeStart" in report:
        raise AssertionError("fire_ms must speak sim Hz, not rAF present")
    if "committedSimMs" not in report and "simTick" not in report:
        raise AssertionError("fire_ms must be the last committed sim tick")
    if "confidence" in report:
        raise AssertionError("do not send cam confidence")
    if "plate:" in report:
        raise AssertionError("do not send plate id as authority")

    start = _js_fn(js, "startRange")
    if "sharedMatch()" not in start:
        raise AssertionError("startRange must branch shared vs local")
    if "spawnOrb3D" not in start:
        raise AssertionError("offline / warm-up must still spawn a local first plate")

    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/start" in warm or "/api/lobby/hit" in warm:
        raise AssertionError("warm-up must stay local practice")
    if "S.warmup = true" not in warm:
        raise AssertionError("warm-up flag must stay")

    sample = _js_fn(js, "AimSample") if False else js
    m = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not m:
        raise AssertionError("AimSample class missing")
    if "this.uv" not in m.group(0) or "this.t_hw" not in m.group(0):
        raise AssertionError("AimSample fields must stay")


def test_sit_pose_authority() -> None:
    """Sit Y is closed-form from life. Two clients agree. Hit uses that pose."""
    if abs(lobby.SIT_BOB_RATE - 1.6) > 1e-12 or abs(lobby.SIT_BOB_AMP - 0.07) > 1e-12:
        raise AssertionError("sit bob constants drifted")
    if abs(lobby.sit_pose_y(0.35, 0.0) - 0.35) > 1e-12:
        raise AssertionError("life 0 sit must sit on the pad")
    want = 0.35 + math.sin(1.0 * lobby.SIT_BOB_RATE) * lobby.SIT_BOB_AMP
    bobbed = lobby.sit_pose_y(0.35, 1.0)
    if abs(bobbed - want) > 1e-12:
        raise AssertionError(f"sit bob must be closed-form sin(life) {bobbed} vs {want}")
    if abs(bobbed - 0.35) < 0.02:
        raise AssertionError("sit bob amp died — friends would not see motion")
    if lobby.sit_pose_y(0.35, lobby.SIT_DWELL_S + 0.5) >= 0.35:
        raise AssertionError("sit must drop after dwell")

    a = lobby.create("HOST")
    lobby.join(a["code"], "P2")
    t0 = 4_000.0
    lobby.start(a["code"], a["player"], now=t0, seed=0x51)
    later_a = lobby.get(a["code"], now=t0 + 1.0)
    later_b = lobby.get(a["code"], now=t0 + 1.0)
    p0a = next(p for p in later_a["plates"] if p["id"] == "p0")
    p0b = next(p for p in later_b["plates"] if p["id"] == "p0")
    if abs(p0a["y"] - p0b["y"]) > 1e-12:
        raise AssertionError(f"two clients split sit Y {p0a['y']} vs {p0b['y']}")
    if abs(p0a["y"] - lobby.sit_pose_y(0.35, 1.0)) > 1e-9:
        raise AssertionError(f"shared sit Y left sit_pose_y {p0a['y']}")

    uv = list(lobby.uv_for_world(p0a["x"], p0a["y"], p0a["z"]))
    shot = lobby.hit(
        a["code"],
        a["player"],
        uv=uv,
        fire_ms=1000.0,
        t_hw=9,
        now=t0 + 1.05,
    )
    if shot.get("hit") != "p0":
        raise AssertionError(f"rewind ray must hit the bobbed sit pose {shot}")

    js = proto_js()
    sit = _js_fn(js, "sitPoseY")
    if "SIT_BOB_RATE" not in sit or "SIT_BOB_AMP" not in sit or "Math.sin" not in sit:
        raise AssertionError("client sitPoseY must share the lobby closed-form bob")
    apply_m = re.search(
        r"function applySharedSim\([^)]*\) \{[\s\S]*?\nasync function pullSharedSim",
        js,
    )
    if not apply_m:
        raise AssertionError("applySharedSim missing")
    apply = apply_m.group(0)
    if "o.mesh.position.set(p.x, p.y, p.z)" not in apply:
        raise AssertionError("applySharedSim must snap sit pose from the room")
    set_at = apply.find("o.mesh.position.set(p.x, p.y, p.z)")
    clay_at = apply.find('o.kind === "clay"')
    if clay_at >= 0 and set_at > clay_at:
        raise AssertionError("applySharedSim skipped sit — flyers-only snap")
    if "sitPoseY(o.baseY, o.life)" not in js:
        raise AssertionError("updateRange must use sitPoseY")
    if "o.phase += dt * 1.6" in js or "o.phase = 0" in js:
        raise AssertionError("updateRange accumulated a local sit phase")
    fire = _js_fn(js, "fire")
    if "await" in fire or "sitPoseY" in fire:
        raise AssertionError("fire() must still peek AimBus — sit pose is not a fire gate")
    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/start" in warm or "/api/lobby/hit" in warm:
        raise AssertionError("WARM UP must stay local after sit pose lock")
    parked = lobby.create("HOST3")
    guest = lobby.join(parked["code"], "R2")
    parked_warm = lobby.warmup(parked["code"], guest["player"])
    if parked_warm.get("seed") or parked_warm.get("plates"):
        raise AssertionError("wait_practice must not open the shared sit sim")


def _euler_flyer_y(y0: float, vy0: float, life: float, dt: float = 1.0 / 128.0) -> float:
    """Semi-implicit Euler the client used before flyerPose. Prove it drifts."""
    y = float(y0)
    vy = float(vy0)
    t = 0.0
    while t + dt <= life + 1e-12:
        y += vy * dt
        vy -= lobby.GRAVITY * dt
        t += dt
    return y


def test_flyer_pose_authority() -> None:
    """Flyer pose is closed-form from life. Two clients agree. Hit uses that pose."""
    if abs(lobby.GRAVITY - 4.6) > 1e-12:
        raise AssertionError("GRAVITY drifted from the shared house")
    born = lobby.flyer_pose(-8.5, 1.089, -5.054, 4.2, 1.4, -0.8, 0.0)
    if abs(born["x"] + 8.5) > 1e-12 or abs(born["y"] - 1.089) > 1e-12:
        raise AssertionError("life 0 flyer must sit on birth")
    life = 1.0
    want = lobby.flyer_pose(-8.5, 1.089, -5.054, 4.2, 1.4, -0.8, life)
    closed_y = 1.089 + 1.4 * life - 0.5 * lobby.GRAVITY * life * life
    if abs(want["y"] - closed_y) > 1e-12:
        raise AssertionError(f"flyer Y must be closed-form {want['y']} vs {closed_y}")
    euler_y = _euler_flyer_y(1.089, 1.4, life)
    if abs(euler_y - want["y"]) < 0.01:
        raise AssertionError("Euler vs closed-form must still diverge — that was the hole")
    if abs(want["vy"] - (1.4 - lobby.GRAVITY * life)) > 1e-12:
        raise AssertionError("flyer vy must be vy0 - g*life")

    a = lobby.create("HOST")
    lobby.join(a["code"], "P2")
    t0 = 4_000.0
    lobby.start(a["code"], a["player"], now=t0, seed=0x51)
    # Seed owns p1 birth at the 2s want. First-poll time must not stamp born_ms.
    lobby.get(a["code"], now=t0 + 2.0)
    later_a = lobby.get(a["code"], now=t0 + 3.0)
    later_b = lobby.get(a["code"], now=t0 + 3.0)
    fly_a = next(p for p in later_a["plates"] if p["id"] == "p1")
    fly_b = next(p for p in later_b["plates"] if p["id"] == "p1")
    if fly_a["kind"] != "clay":
        raise AssertionError(f"seed 0x51 must spawn clay p1 {fly_a}")
    if abs(fly_a["y"] - fly_b["y"]) > 1e-12 or abs(fly_a["x"] - fly_b["x"]) > 1e-12:
        raise AssertionError(f"two clients split flyer pose {fly_a} vs {fly_b}")
    closed = lobby.flyer_pose(
        fly_a["x0"], fly_a["y0"], fly_a["z0"],
        fly_a["vx0"], fly_a["vy0"], fly_a["vz0"],
        fly_a["life"],
    )
    if abs(fly_a["y"] - closed["y"]) > 1e-9 or abs(fly_a["x"] - closed["x"]) > 1e-9:
        raise AssertionError(f"shared flyer left flyer_pose {fly_a} vs {closed}")
    if abs(fly_a["life"] - 1.0) > 1e-9:
        raise AssertionError(f"p1 clay at t=3s must have life 1s {fly_a['life']}")
    euler_live = _euler_flyer_y(fly_a["y0"], fly_a["vy0"], fly_a["life"])
    if abs(euler_live - fly_a["y"]) < 0.01:
        raise AssertionError("live shared flyer must not be the old Euler Y")

    uv = list(lobby.uv_for_world(fly_a["x"], fly_a["y"], fly_a["z"]))
    shot = lobby.hit(
        a["code"],
        a["player"],
        uv=uv,
        fire_ms=3000.0,
        t_hw=11,
        now=t0 + 3.05,
    )
    if shot.get("hit") != fly_a["id"]:
        raise AssertionError(f"rewind ray must hit the closed-form flyer {shot}")

    js = proto_js()
    fly = _js_fn(js, "flyerPose")
    if "GRAVITY" not in fly or "0.5" not in fly:
        raise AssertionError("client flyerPose must share the lobby closed-form")
    ranged = _js_fn(js, "updateRange")
    if "flyerPose(" not in ranged:
        raise AssertionError("updateRange must use flyerPose")
    if "o.vy -=" in ranged or "o.mesh.position.y +=" in ranged:
        raise AssertionError("updateRange Euler-integrated flyers — rewind would split")
    apply_m = re.search(
        r"function applySharedSim\([^)]*\) \{[\s\S]*?\nasync function pullSharedSim",
        js,
    )
    if not apply_m:
        raise AssertionError("applySharedSim missing")
    apply = apply_m.group(0)
    if "bindFlyerBirthFromPlate" not in apply:
        raise AssertionError("applySharedSim must bind flyer birth from the room")
    fire = _js_fn(js, "fire")
    if "await" in fire or "flyerPose" in fire:
        raise AssertionError("fire() must still peek AimBus — flyer pose is not a fire gate")
    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/start" in warm or "/api/lobby/hit" in warm:
        raise AssertionError("WARM UP must stay local after flyer pose lock")
    parked = lobby.create("HOST4")
    guest = lobby.join(parked["code"], "S2")
    parked_warm = lobby.warmup(parked["code"], guest["player"])
    if parked_warm.get("seed") or parked_warm.get("plates"):
        raise AssertionError("wait_practice must not open the shared flyer sim")


def _hex_contains(x: float, y: float, radius: float) -> bool:
    """Same 6 verts as proto hexPlateGeo (i/6 * 2π − π/6). Look only — not hitscan."""
    verts = []
    for i in range(6):
        ang = (i / 6.0) * math.pi * 2.0 - math.pi / 6.0
        verts.append((math.cos(ang) * radius, math.sin(ang) * radius))
    for i in range(6):
        x0, y0 = verts[i]
        x1, y1 = verts[(i + 1) % 6]
        cross = (x1 - x0) * (y - y0) - (y1 - y0) * (x - x0)
        if cross < -1e-12:
            return False
    return True


def test_hitscan_sphere_authority() -> None:
    """HID peek and room rewind share one sphere. The spun hex is Look only."""
    if abs(lobby._plate_radius("clay") - 0.50) > 1e-12:
        raise AssertionError("clay sphere drifted from 0.50")
    if abs(lobby._plate_radius("rise") - 0.50) > 1e-12:
        raise AssertionError("rise sphere drifted from 0.50")
    if abs(lobby._plate_radius("sit") - 0.62) > 1e-12:
        raise AssertionError("sit sphere drifted from 0.62")
    if lobby.CAM_EYE != (0.0, 1.64, 2.05) or lobby.FOV_Y_DEG != 62.0:
        raise AssertionError("yard camera left the shared house")

    sit_r = lobby._plate_radius("sit")
    apothem = sit_r * math.cos(math.pi / 6.0)
    graze = (apothem + sit_r) * 0.5
    if _hex_contains(0.0, 0.0, sit_r) is False:
        raise AssertionError("hex winding flipped — center must be inside")
    if _hex_contains(graze, 0.0, sit_r):
        raise AssertionError("hex graze fixture must sit outside the plate")
    if math.hypot(graze, 0.0) >= sit_r:
        raise AssertionError("hex graze fixture must sit inside the sphere disk")

    cam_x, _, _ = lobby._cam_basis()
    cx, cy, cz = 0.2, 0.35, -6.6
    wx = cx + cam_x[0] * graze
    wy = cy + cam_x[1] * graze
    wz = cz + cam_x[2] * graze
    uv = list(lobby.uv_for_world(wx, wy, wz))
    center = list(lobby.uv_for_world(cx, cy, cz))
    if abs(uv[0] - center[0]) < 1e-5 and abs(uv[1] - center[1]) < 1e-5:
        raise AssertionError("graze UV must not be the plate center")
    origin, direction = lobby.ray_from_uv(uv[0], uv[1])
    t_hit = lobby._ray_sphere(origin, direction, (cx, cy, cz), sit_r)
    if t_hit is None:
        raise AssertionError("house sphere must accept the hex-graze UV")

    a = lobby.create("HOST")
    lobby.join(a["code"], "P2")
    t0 = 6_000.0
    lobby.start(a["code"], a["player"], now=t0, seed=0x51)
    view_a = lobby.get(a["code"], now=t0 + 0.10)
    view_b = lobby.get(a["code"], now=t0 + 0.10)
    p0a = next(p for p in view_a["plates"] if p["id"] == "p0")
    p0b = next(p for p in view_b["plates"] if p["id"] == "p0")
    if abs(p0a["x"] - p0b["x"]) > 1e-12 or abs(p0a["y"] - p0b["y"]) > 1e-12:
        raise AssertionError(f"two clients split sit pose before the graze {p0a} vs {p0b}")

    sky = [0.02, 0.02]
    miss = lobby.hit(a["code"], a["player"], uv=sky, fire_ms=80.0, t_hw=20, now=t0 + 0.12)
    if miss.get("hit") or not miss.get("miss"):
        raise AssertionError(f"sky ray must still miss the sphere {miss}")

    shot = lobby.hit(
        a["code"],
        a["player"],
        uv=uv,
        fire_ms=90.0,
        t_hw=21,
        now=t0 + 0.14,
    )
    if shot.get("hit") != "p0":
        raise AssertionError(f"rewind sphere must accept the hex-graze UV {shot}")
    after_a = lobby.get(a["code"], now=t0 + 0.14)
    after_b = lobby.get(a["code"], now=t0 + 0.14)
    if "p0" in _ids(after_a) or "p0" in _ids(after_b):
        raise AssertionError("graze hit must shatter for both clients")

    js = proto_js()
    rad = _js_fn(js, "plateRadius")
    if "0.50" not in rad or "0.62" not in rad:
        raise AssertionError("client plateRadius must share the lobby sphere")
    if '"clay"' not in rad or '"rise"' not in rad:
        raise AssertionError("client plateRadius must own clay/rise 0.50")
    ray = _js_fn(js, "rayFromUv")
    if "CAM_EYE" not in ray or "FOV_Y_DEG" not in ray:
        raise AssertionError("client rayFromUv must share the yard camera")
    if "1 - uvy * 2" not in ray and "1 - uvy*2" not in ray:
        raise AssertionError("client rayFromUv NDC must match lobby.ray_from_uv")
    scan = _js_fn(js, "hitscanRange")
    if "plateRadius" not in scan or "raySphere" not in scan:
        raise AssertionError("hitscanRange must ray-test the house sphere")
    if "intersectObjects" in scan or "Raycaster" in scan:
        raise AssertionError("hitscanRange must not mesh-test the spun hex")
    if "S.orbs" not in scan:
        raise AssertionError("hitscanRange must peek last committed plates")
    fire = _js_fn(js, "fire")
    if "hitscanRange" not in fire:
        raise AssertionError("fire() must peek the house sphere")
    if "shot.uv" not in fire:
        raise AssertionError("fire() must peek AimBus UV")
    if "intersectObjects" in fire:
        raise AssertionError("fire() mesh-tested the hex — rewind would split")
    if "await" in fire or "sitPoseY" in fire or "flyerPose" in fire:
        raise AssertionError("fire() must still peek AimBus — hitscan is not a pose gate")
    if "1.64" not in js or "2.05" not in js:
        raise AssertionError("client CAM_EYE left the yard camera")
    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/start" in warm or "/api/lobby/hit" in warm:
        raise AssertionError("WARM UP must stay local after hitscan lock")
    parked = lobby.create("HOST5")
    guest = lobby.join(parked["code"], "T2")
    parked_warm = lobby.warmup(parked["code"], guest["player"])
    if parked_warm.get("seed") or parked_warm.get("plates"):
        raise AssertionError("wait_practice must not open the shared hitscan sim")


def test_hit_score_authority() -> None:
    """Room owns gallery SCORE. Two clients agree. Local peek does not credit."""
    a = lobby.create("HOST")
    b = lobby.join(a["code"], "P2")
    t0 = 7_000.0
    st = lobby.start(a["code"], a["player"], now=t0, seed=0x51)
    if st.get("scores") != {} or st.get("combos") != {} or st.get("hits") != {}:
        raise AssertionError(f"fresh house must start score-empty {st}")
    if "scores" not in st or "combos" not in st or "hits" not in st:
        raise AssertionError("match_live snapshot must carry the score book")

    sky = [0.02, 0.02]
    miss = lobby.hit(
        a["code"],
        a["player"],
        uv=sky,
        fire_ms=80.0,
        t_hw=30,
        now=t0 + 0.12,
    )
    if miss.get("hit") or not miss.get("miss"):
        raise AssertionError(f"sky ray must miss {miss}")
    if (miss.get("scores") or {}).get(a["player"]):
        raise AssertionError(f"miss must not invent SCORE {miss}")
    if (miss.get("combos") or {}).get(a["player"], 1) != 0:
        raise AssertionError(f"miss must drop combo {miss}")
    view_a = lobby.get(a["code"], now=t0 + 0.12)
    view_b = lobby.get(a["code"], now=t0 + 0.12)
    if view_a.get("scores") != view_b.get("scores"):
        raise AssertionError(f"miss score book split {view_a.get('scores')} vs {view_b.get('scores')}")

    uv = _p0_uv()
    shot = lobby.hit(
        a["code"],
        a["player"],
        uv=uv,
        fire_ms=90.0,
        t_hw=31,
        now=t0 + 0.14,
    )
    if shot.get("hit") != "p0":
        raise AssertionError(f"rewind must still hit p0 {shot}")
    if (shot.get("scores") or {}).get(a["player"]) != 100:
        raise AssertionError(f"first sit must credit 100 {shot}")
    if (shot.get("combos") or {}).get(a["player"]) != 1:
        raise AssertionError(f"first hit combo must be 1 {shot}")
    if (shot.get("hits") or {}).get(a["player"]) != 1:
        raise AssertionError(f"first hit must count {shot}")
    after_a = lobby.get(a["code"], now=t0 + 0.14)
    after_b = lobby.get(a["code"], now=t0 + 0.14)
    if after_a.get("scores") != after_b.get("scores"):
        raise AssertionError(f"two clients split SCORE {after_a.get('scores')} vs {after_b.get('scores')}")
    if after_a.get("combos") != after_b.get("combos") or after_a.get("hits") != after_b.get("hits"):
        raise AssertionError("two clients split combo / hits")
    if (after_b.get("scores") or {}).get(b["player"]):
        raise AssertionError("guest must not inherit host SCORE")

    again = lobby.hit(a["code"], b["player"], uv=uv, fire_ms=100.0, now=t0 + 0.16)
    if again.get("hit"):
        raise AssertionError("second ray on a dead plate must not hit")
    if (again.get("scores") or {}).get(b["player"]):
        raise AssertionError(f"dead-plate miss must not credit the guest {again}")
    if (again.get("combos") or {}).get(b["player"], 1) != 0:
        raise AssertionError("dead-plate miss must drop guest combo")
    if (again.get("scores") or {}).get(a["player"]) != 100:
        raise AssertionError("guest miss must not rewrite host SCORE")

    parked = lobby.create("HOST6")
    guest = lobby.join(parked["code"], "U2")
    parked_warm = lobby.warmup(parked["code"], guest["player"])
    if parked_warm.get("scores") or parked_warm.get("combos") or parked_warm.get("hits"):
        raise AssertionError("wait_practice must not open the shared score book")
    g = lobby.get(parked["code"])
    if g.get("scores") or g.get("plates") or g.get("seed"):
        raise AssertionError("wait get leaked score / sim")

    js = proto_js()
    fire = _js_fn(js, "fire")
    shared_at = fire.find("if (sharedMatch())")
    score_at = fire.find("S.score +=")
    if shared_at < 0:
        raise AssertionError("fire() must park match_live before local credit")
    if score_at < 0:
        raise AssertionError("Offline / WARM UP must still credit locally")
    if score_at < shared_at:
        raise AssertionError("local SCORE increment landed before the shared park")
    shared_return = fire.find("return;", shared_at)
    if shared_return < 0 or shared_return > score_at:
        raise AssertionError("match_live must return before local SCORE / shatter")
    if "reportSharedFire(shot)" not in fire and "reportSharedFire(shot, " not in fire:
        raise AssertionError("shared fire must still POST the peeked intent")
    if "await" in fire:
        raise AssertionError("fire() must still peek AimBus — SCORE is not a fire gate")
    apply_m = re.search(
        r"function applySharedSim\([^)]*\) \{[\s\S]*?\nasync function pullSharedSim",
        js,
    )
    if not apply_m:
        raise AssertionError("applySharedSim missing")
    apply = apply_m.group(0)
    if "data.scores" not in apply or "S.score" not in apply:
        raise AssertionError("applySharedSim must snap SCORE from the room")
    if "data.combos" not in apply or "S.combo" not in apply:
        raise AssertionError("applySharedSim must snap combo from the room")
    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/start" in warm or "/api/lobby/hit" in warm:
        raise AssertionError("WARM UP must stay local after score lock")


def test_escape_miss_authority() -> None:
    """ESC = miss on the room book. Two clients agree. Offline still local."""
    a = lobby.create("HOST")
    b = lobby.join(a["code"], "P2")
    t0 = 8_000.0
    lobby.start(a["code"], a["player"], now=t0, seed=0x51)
    uv = _p0_uv()
    shot = lobby.hit(
        a["code"],
        a["player"],
        uv=uv,
        fire_ms=90.0,
        t_hw=40,
        now=t0 + 0.14,
    )
    if (shot.get("combos") or {}).get(a["player"]) != 1:
        raise AssertionError(f"setup hit must credit combo 1 {shot}")
    if (shot.get("scores") or {}).get(a["player"]) != 100:
        raise AssertionError(f"setup hit must credit SCORE 100 {shot}")

    mid_a = lobby.get(a["code"], now=t0 + 1.0)
    mid_b = lobby.get(a["code"], now=t0 + 1.0)
    if (mid_a.get("combos") or {}).get(a["player"]) != 1:
        raise AssertionError(f"young house must keep combo {mid_a.get('combos')}")
    if mid_a.get("combos") != mid_b.get("combos"):
        raise AssertionError("two clients split combo before ESC")
    if (mid_a.get("scores") or {}).get(a["player"]) != 100:
        raise AssertionError("young house must keep SCORE")

    late_a = lobby.get(a["code"], now=t0 + 9.0)
    late_b = lobby.get(a["code"], now=t0 + 9.0)
    if (late_a.get("combos") or {}).get(a["player"], 1) != 0:
        raise AssertionError(f"ESC must drop combo {late_a.get('combos')}")
    if late_a.get("combos") != late_b.get("combos"):
        raise AssertionError(
            f"two clients split ESC combo {late_a.get('combos')} vs {late_b.get('combos')}"
        )
    if (late_a.get("scores") or {}).get(a["player"]) != 100:
        raise AssertionError("ESC must not rewrite SCORE")
    if (late_a.get("hits") or {}).get(a["player"]) != 1:
        raise AssertionError("ESC must not invent a hit")
    if not late_a.get("escaped"):
        raise AssertionError("room must note the ESC")
    if late_a.get("escaped") != late_b.get("escaped"):
        raise AssertionError("two clients split the ESC set")

    parked = lobby.create("HOST7")
    guest = lobby.join(parked["code"], "V2")
    parked_warm = lobby.warmup(parked["code"], guest["player"])
    if parked_warm.get("escaped") or parked_warm.get("scores") or parked_warm.get("combos"):
        raise AssertionError("wait_practice must not open the shared ESC book")
    g = lobby.get(parked["code"])
    if g.get("escaped") or g.get("scores") or g.get("seed"):
        raise AssertionError("wait get leaked ESC / sim")

    js = proto_js()
    apply_m = re.search(
        r"function applySharedSim\([^)]*\) \{[\s\S]*?\nasync function pullSharedSim",
        js,
    )
    if not apply_m:
        raise AssertionError("applySharedSim missing")
    apply = apply_m.group(0)
    if '"ESC"' not in apply or "missTick" not in apply:
        raise AssertionError("applySharedSim must tell ESC when a plate leaves without a kill")
    if "S.combo = 0" in apply:
        raise AssertionError("applySharedSim must not locally zero combo — snap the room book")
    if "data.combos" not in apply or "S.combo" not in apply:
        raise AssertionError("applySharedSim must still snap combo from the room")
    ranged = _js_fn(js, "updateRange")
    if "S.combo = 0" not in ranged:
        raise AssertionError("Offline / WARM UP must still drop combo on ESC")
    fire = _js_fn(js, "fire")
    if "await" in fire:
        raise AssertionError("fire() must still peek AimBus — ESC is not a fire gate")
    if "S.combo = 0" in fire[fire.find("if (sharedMatch())") : fire.find("S.score +=")]:
        raise AssertionError("match_live fire() must not locally drop combo")
    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/start" in warm or "/api/lobby/hit" in warm:
        raise AssertionError("WARM UP must stay local after ESC lock")


def test_seed_owns_born_ms() -> None:
    """Seed owns birth. A late first poll must not shift the house."""
    src = (ROOT / "tools/lobby.py").read_text(encoding="utf-8")
    adv = re.search(r"def _advance_spawns\([\s\S]*?\n\ndef ", src)
    if not adv:
        raise AssertionError("missing _advance_spawns")
    body = adv.group(0)
    if "_next_spawn_ms" not in body:
        raise AssertionError("spawns must read the seed schedule, not the observer")
    if "_spawn_random(sim, elapsed_ms" in body:
        raise AssertionError("observer elapsed stamped born_ms — seed no longer owns birth")
    if "range(128)" in body or "range(HZ)" in body:
        raise AssertionError("_advance_spawns became a 128 Hz friend loop")
    nxt = re.search(r"def _next_spawn_ms\([\s\S]*?\n\ndef ", src)
    if not nxt:
        raise AssertionError("missing _next_spawn_ms")
    if "2000.0" not in nxt.group(0):
        raise AssertionError("second plate must be born at the 2s want")
    note = re.search(r"def _note_escapes\([\s\S]*?\n\ndef ", src)
    if not note or "_escape_ms" not in note.group(0):
        raise AssertionError("ESC at_ms must be the closed-form leave, not the poll")

    t0 = 11_000.0
    a = lobby.create("HOST")
    lobby.join(a["code"], "P2")
    lobby.start(a["code"], a["player"], now=t0, seed=0x51)
    b = lobby.create("HOST2")
    lobby.join(b["code"], "Q2")
    lobby.start(b["code"], b["player"], now=t0, seed=0x51)

    early_a = lobby.get(a["code"], now=t0 + 2.0)
    late_b = lobby.get(b["code"], now=t0 + 2.6)
    later_a = lobby.get(a["code"], now=t0 + 2.6)
    if _ids(early_a) != ["p0", "p1"]:
        raise AssertionError(f"2s want must birth p1 on the seed schedule {_ids(early_a)}")
    p1_early = next(p for p in early_a["plates"] if p["id"] == "p1")
    p1_a = next(p for p in later_a["plates"] if p["id"] == "p1")
    p1_b = next(p for p in late_b["plates"] if p["id"] == "p1")
    if abs(p1_early["born_ms"] - 2000.0) > 1e-9:
        raise AssertionError(f"p1 must be born at 2000, not the observer {p1_early['born_ms']}")
    if abs(p1_a["born_ms"] - p1_b["born_ms"]) > 1e-9:
        raise AssertionError(f"late first poll split born_ms {p1_a['born_ms']} vs {p1_b['born_ms']}")
    if abs(p1_a["x"] - p1_b["x"]) > 1e-9 or abs(p1_a["y"] - p1_b["y"]) > 1e-9:
        raise AssertionError(f"late first poll split flyer pose {p1_a} vs {p1_b}")
    if later_a["seed"] != late_b["seed"] or _ids(later_a) != _ids(late_b):
        raise AssertionError(f"same seed split the house {_ids(later_a)} vs {_ids(late_b)}")

    c = lobby.create("HOST3")
    lobby.start(c["code"], c["player"], now=t0, seed=0x51)
    death = lobby.quantize_fire_ms(90.0)
    shot = lobby.hit(
        c["code"],
        c["player"],
        uv=_p0_uv(),
        fire_ms=90.0,
        t_hw=50,
        now=t0 + 0.14,
    )
    if shot.get("hit") != "p0":
        raise AssertionError(f"setup hit must still shatter p0 {shot}")
    p1_hit = next((p for p in shot.get("plates") or [] if p["id"] == "p1"), None)
    if not p1_hit:
        raise AssertionError(f"hit snap must carry the seed-schedule replacement {shot}")
    if abs(float(p1_hit["born_ms"]) - death) > 1e-9:
        raise AssertionError(
            f"replacement born_ms must be the death tick {p1_hit['born_ms']} vs {death}"
        )
    repl = lobby.get(c["code"], now=t0 + 0.14)
    p1 = next((p for p in repl.get("plates") or [] if p["id"] == "p1"), None)
    if not p1:
        raise AssertionError(f"death must birth a replacement on the schedule {repl}")
    if abs(float(p1["born_ms"]) - death) > 1e-9:
        raise AssertionError(
            f"get() split replacement birth {p1['born_ms']} vs {death}"
        )

    parked = lobby.create("HOST8")
    guest = lobby.join(parked["code"], "W2")
    parked_warm = lobby.warmup(parked["code"], guest["player"])
    if parked_warm.get("seed") or parked_warm.get("plates"):
        raise AssertionError("wait_practice must not open the shared seed schedule")

    js = proto_js()
    fire = _js_fn(js, "fire")
    if "await" in fire:
        raise AssertionError("fire() must still peek AimBus — seed schedule is not a fire gate")
    if "aimBus.fire" not in fire:
        raise AssertionError("fire() no longer peeks AimBus")
    start = _js_fn(js, "startRange")
    if "sharedMatch()" not in start or "spawnOrb3D" not in start:
        raise AssertionError("Offline / WARM UP must still spawn a local first plate")
    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/start" in warm or "/api/lobby/hit" in warm:
        raise AssertionError("WARM UP must stay local after seed lock")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        raise AssertionError("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        raise AssertionError("AimSample fields changed — keep the locked struct")


def main() -> int:
    try:
        test_two_clients_share_seed_and_ray_hit()
        test_stale_fire_tick_is_miss()
        test_warmup_stays_local()
        test_hit_uses_sample_not_cam()
        test_client_keeps_local_practice_and_hid()
        test_sit_pose_authority()
        test_flyer_pose_authority()
        test_hitscan_sphere_authority()
        test_hit_score_authority()
        test_escape_miss_authority()
        test_seed_owns_born_ms()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("shared range ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
