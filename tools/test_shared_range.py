#!/usr/bin/env python3
"""R4: shared seed + server ray resolve at the fire tick. Warm-up stays local."""

from __future__ import annotations

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
    if not st.get("ok") or st.get("phase") != "range":
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
    if warm.get("phase") != "wait" or "seed" in warm or warm.get("plates"):
        raise AssertionError(f"warmup must not open the shared sim {warm}")
    g = lobby.get(a["code"])
    if g.get("phase") != "wait" or "seed" in g or g.get("plates"):
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


def main() -> int:
    try:
        test_two_clients_share_seed_and_ray_hit()
        test_stale_fire_tick_is_miss()
        test_warmup_stays_local()
        test_hit_uses_sample_not_cam()
        test_client_keeps_local_practice_and_hid()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("shared range ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
