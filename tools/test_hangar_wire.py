#!/usr/bin/env python3
"""SableNet hangar lock: room owns hangar | wait_practice | match_live.

Fail loud if practice promotes the room, poll is not a view of that enum,
HID waits on hangar, or Offline / WARM UP talk to the room for hangar.
Bay stays parked. AimSample stays locked.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lobby  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402


def _fail(msg: str) -> None:
    raise AssertionError(f"SABLE HANGAR WIRE FAIL: {msg}")


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"(?:async )?function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        _fail(f"missing function {name}")
    return m.group(0)


def test_round_trip() -> None:
    a = lobby.create("HOST")
    if a.get("hangar") != "wait_practice":
        _fail(f"create hangar {a.get('hangar')}")
    b = lobby.join(a["code"], "P2")
    g = lobby.get(a["code"])
    if b.get("hangar") != "wait_practice" or g.get("hangar") != "wait_practice":
        _fail(f"wait hangar split {b.get('hangar')} {g.get('hangar')}")
    if a.get("hangar") != b.get("hangar"):
        _fail("two clients must see the same room hangar")

    warm = lobby.warmup(a["code"], b["player"])
    if warm.get("phase") != "wait" or warm.get("hangar") != "wait_practice":
        _fail(f"WARM UP must keep wait_practice {warm}")
    if "seed" in warm or warm.get("plates") or warm.get("scores"):
        _fail("WARM UP must not open the shared sim")

    st = lobby.start(a["code"], a["player"], now=2_000.0, seed=7)
    if st.get("phase") != "range" or st.get("hangar") != "match_live":
        _fail(f"start hangar {st.get('hangar')} phase {st.get('phase')}")
    view_a = lobby.get(a["code"], now=2_000.0)
    view_b = lobby.get(a["code"], now=2_000.0)
    if view_a.get("hangar") != "match_live" or view_a.get("hangar") != view_b.get("hangar"):
        _fail(f"range hangar split {view_a.get('hangar')} {view_b.get('hangar')}")

    bay = lobby.create("HOST2")
    lobby.join(bay["code"], "Q2")
    booth = lobby.start_bay(bay["code"], bay["player"], now=3_000.0)
    if booth.get("phase") != "bay" or booth.get("hangar") != "hangar":
        _fail(f"parked bay hangar {booth.get('hangar')} phase {booth.get('phase')}")
    if lobby.get(a["code"], now=2_100.0).get("hangar") != "match_live":
        _fail("bay start must not rewrite another room hangar")


def test_fail_loud() -> None:
    try:
        lobby.hangar_for_phase("arena")
    except ValueError as exc:
        if "unknown room phase" not in str(exc):
            _fail(f"unknown phase must name the miss {exc}")
    else:
        _fail("hangar_for_phase swallowed an unknown room phase")
    try:
        lobby.snapshot({"code": "XXXX", "phase": "wait", "host": "h", "slots": []})
    except ValueError as exc:
        if "missing hangar" not in str(exc):
            _fail(f"snapshot must fail loud when hangar is omitted {exc}")
    else:
        _fail("snapshot swallowed a missing hangar field")
    try:
        lobby.snapshot({"code": "XXXX", "phase": "wait", "hangar": "match_live", "host": "h", "slots": []})
    except ValueError as exc:
        if "wait_practice" not in str(exc):
            _fail(f"wait+LIVE must fail loud {exc}")
    else:
        _fail("wait room accepted match_live — practice must not promote")
    try:
        lobby.snapshot({"code": "XXXX", "phase": "bay", "hangar": "match_live", "host": "h", "slots": []})
    except ValueError as exc:
        if "parked bay" not in str(exc):
            _fail(f"bay+LIVE must fail loud {exc}")
    else:
        _fail("parked bay accepted match_live")
    for phase, want in (("wait", "wait_practice"), ("range", "match_live"), ("bay", "hangar")):
        got = lobby.hangar_for_phase(phase)
        if got != want:
            _fail(f"{phase} hangar {got} want {want}")
        if got not in lobby.HANGAR_PHASES:
            _fail(f"{got} left HANGAR_PHASES")


def test_practice_never_promotes() -> None:
    src = (ROOT / "tools/lobby.py").read_text(encoding="utf-8")
    if src.count('_assign_room_hangar(room, hangar_for_phase("range"))') != 1:
        _fail("only ENTER RANGE / start() may write match_live")
    if "_assign_room_hangar" in src[src.find("def _mark_warmup") : src.find("def warmup")]:
        _fail("warmup wrote hangar — practice never promotes the room")
    a = lobby.create("HOST")
    b = lobby.join(a["code"], "P2")
    lobby.warmup(a["code"], a["player"])
    lobby.warmup(a["code"], b["player"])
    g = lobby.get(a["code"])
    if g.get("hangar") != "wait_practice" or g.get("phase") != "wait":
        _fail(f"practice promoted the room {g.get('hangar')} {g.get('phase')}")
    if g.get("seed") or g.get("plates") or g.get("scores"):
        _fail("practice opened the shared sim")
    late = lobby.warmup(a["code"], a["player"])
    if late.get("hangar") != "wait_practice":
        _fail("second WARM UP promoted hangar")


def test_client_apply_and_hid() -> None:
    js = proto_js()
    apply = _js_fn(js, "applyRoomHangar")
    if "assignHangar" not in apply or "data.hangar" not in apply:
        _fail("applyRoomHangar must write data.hangar onto S.hangar")
    if "room snapshot missing hangar" not in apply:
        _fail("applyRoomHangar must fail loud when hangar is omitted")
    if re.search(r"await\s+", apply) or "fetch(" in apply:
        _fail("applyRoomHangar awaits — hangar wire trapped HID")
    if "aimBus" in apply or "AimSample" in apply or "fire(" in apply:
        _fail("applyRoomHangar touched AimBus / AimSample / fire")
    paint = _js_fn(js, "paintLobby")
    if "applyRoomHangar(data)" not in paint:
        _fail("paintLobby must apply room-owned hangar")
    if "!S.warmup" not in paint:
        _fail("paintLobby must not wire-gate WARM UP on hangar")
    poll = _js_fn(js, "lobbyPoll")
    if poll.count("applyRoomHangar(data)") < 1:
        _fail("lobbyPoll must apply the hangar view")
    fire = _js_fn(js, "fire")
    if "applyRoomHangar" in fire or "S.hangar" in fire or "hangar_for_phase" in fire:
        _fail("fire() gated on hangar wire — Fire = AimBus HID peek")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if re.search(r"await\s+", fire):
        _fail("fire() awaits — hangar wire trapped HID")
    warm = _js_fn(js, "lobbyWarmup")
    if 'assignHangar("wait_practice")' not in warm:
        _fail("WARM UP must mark wait_practice locally")
    if "applyRoomHangar" in warm:
        _fail("WARM UP applied room hangar — client-local park")
    if re.search(r"await\s+", warm):
        _fail("WARM UP awaits — waiting room blocked practice")
    if "/api/lobby/start" in warm:
        _fail("WARM UP started the shared house")
    if "/api/lobby/hit" in warm:
        _fail("WARM UP talked to the room hit path")
    offline = re.search(
        r'\$\("btn-play"\)\.addEventListener\("click", \(\) => \{[\s\S]*?play\("range"\)',
        js,
    )
    if not offline or 'assignHangar("hangar")' not in offline.group(0):
        _fail("OFFLINE must mark hangar in one click")
    if "applyRoomHangar" in offline.group(0) or "fetch(" in offline.group(0):
        _fail("OFFLINE waited on room hangar")
    if "/api/lobby" in offline.group(0):
        _fail("OFFLINE talked to the room")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")


def test_docs_own_hangar() -> None:
    modes = (ROOT / "docs/modes.md").read_text(encoding="utf-8")
    bible = (ROOT / "docs/PRODUCTION.md").read_text(encoding="utf-8")
    if "SableNet hangar lock" not in modes:
        _fail("docs/modes.md must name the SableNet hangar lock")
    if "room snapshot owns hangar" not in modes and "owns that session class" not in modes:
        _fail("docs/modes.md must note the room owns hangar")
    if "Practice never promotes" not in modes and "practice never promotes" not in modes:
        _fail("docs/modes.md must lock practice off match_live")
    if "wait_practice" not in modes or "match_live" not in modes:
        _fail("docs/modes.md must keep hangar | wait_practice | match_live")
    if "S.hangar" not in modes:
        _fail("docs/modes.md must keep HUD on S.hangar")
    if "SableNet hangar lock" not in bible and "owns hangar" not in bible:
        _fail("PRODUCTION.md must name the SableNet hangar lock")
    if "test_hangar_wire.py" not in bible:
        _fail("PRODUCTION.md must fail loud through test_hangar_wire.py")
    ci = (ROOT / "tools/ci.sh").read_text(encoding="utf-8")
    if "test_hangar_wire.py" not in ci:
        _fail("ci.sh must run the hangar wire gate")


def main() -> int:
    try:
        test_round_trip()
        test_fail_loud()
        test_practice_never_promotes()
        test_client_apply_and_hid()
        test_docs_own_hangar()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("hangar wire ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
