#!/usr/bin/env python3
"""R4: two logical clients share plate seed/ids; a hit updates both views."""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lobby  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        raise AssertionError(f"missing function {name}")
    return m.group(0)


def _ids(snap: dict) -> list[str]:
    return [p["id"] for p in snap.get("plates") or []]


def test_two_clients_share_seed_and_hit() -> None:
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
    if view_a["elapsed_ms"] != view_b["elapsed_ms"]:
        raise AssertionError("elapsed must match at the same now")

    later_a = lobby.get(a["code"], now=t0 + 2.6)
    later_b = lobby.get(a["code"], now=t0 + 2.6)
    if _ids(later_a) != _ids(later_b) or later_a["seed"] != later_b["seed"]:
        raise AssertionError(f"spawn desync {_ids(later_a)} vs {_ids(later_b)}")
    if len(_ids(later_a)) < 2:
        raise AssertionError(f"expected a second shared plate {_ids(later_a)}")

    other = lobby.create("HOST2")
    lobby.join(other["code"], "Q2")
    twin = lobby.start(other["code"], other["player"], now=t0, seed=0xC0FFEE)
    twin_later = lobby.get(other["code"], now=t0 + 2.6)
    if _ids(twin_later) != _ids(later_a):
        raise AssertionError(f"same seed must spawn same ids {_ids(twin_later)} vs {_ids(later_a)}")

    live = _ids(later_a)
    target = live[0]
    shot = lobby.hit(a["code"], a["player"], target, now=t0 + 2.7)
    if not shot.get("ok") or shot.get("hit") != target:
        raise AssertionError(f"hit {shot}")
    after_a = lobby.get(a["code"], now=t0 + 2.7)
    after_b = lobby.get(a["code"], now=t0 + 2.7)
    if target in _ids(after_a) or target in _ids(after_b):
        raise AssertionError(f"dead plate still live {_ids(after_a)} {_ids(after_b)}")
    dead_a = [d["id"] for d in after_a.get("dead") or []]
    dead_b = [d["id"] for d in after_b.get("dead") or []]
    if target not in dead_a or dead_a != dead_b:
        raise AssertionError(f"dead set split {dead_a} vs {dead_b}")

    again = lobby.hit(a["code"], b["player"], target, now=t0 + 2.8)
    if again.get("ok"):
        raise AssertionError("second hit on a dead plate must fail")

    outsider = lobby.hit(a["code"], "nobody", live[1] if len(live) > 1 else "p1", now=t0 + 2.8)
    if outsider.get("ok"):
        raise AssertionError("outsider must not write the house")


def test_warmup_stays_local() -> None:
    a = lobby.create("HOST")
    b = lobby.join(a["code"], "P2")
    warm = lobby.warmup(a["code"], b["player"])
    if warm.get("phase") != "wait" or "seed" in warm or warm.get("plates"):
        raise AssertionError(f"warmup must not open the shared sim {warm}")
    g = lobby.get(a["code"])
    if g.get("phase") != "wait" or "seed" in g or g.get("plates"):
        raise AssertionError(f"wait get leaked sim {g}")
    miss = lobby.hit(a["code"], a["player"], "p0")
    if miss.get("ok"):
        raise AssertionError("hit during wait must fail")


def test_hit_never_reads_cam() -> None:
    src = (ROOT / "tools/lobby.py").read_text(encoding="utf-8")
    fn = re.search(r"def hit\([^)]*\)[^:]*:([\s\S]+)$", src)
    if not fn:
        raise AssertionError("missing lobby.hit")
    body = fn.group(1)
    for banned in ("confidence", "AimSample", "camera", "lifted", "aim"):
        if banned in body:
            raise AssertionError(f"hit must not read {banned}")


def test_client_keeps_local_practice_and_hid() -> None:
    js = (ROOT / "proto/game.js").read_text(encoding="utf-8")
    fire = _js_fn(js, "fire")
    if "await" in fire:
        raise AssertionError("shared hit must not await inside fire()")
    if "coastTrack" in fire or "updateAim" in fire:
        raise AssertionError("fire must still peek only")
    if "reportSharedHit" not in fire:
        raise AssertionError("HID hit must report plate id after local shatter")
    report = _js_fn(js, "reportSharedHit")
    if "await" in report or "async " in report:
        raise AssertionError("reportSharedHit must be fire-and-forget")
    if "/api/lobby/hit" not in report:
        raise AssertionError("reportSharedHit posts the plate id")

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


def main() -> int:
    try:
        test_two_clients_share_seed_and_hit()
        test_warmup_stays_local()
        test_hit_never_reads_cam()
        test_client_keeps_local_practice_and_hid()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("shared range ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
