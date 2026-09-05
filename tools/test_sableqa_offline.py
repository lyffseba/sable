#!/usr/bin/env python3
"""SableQA product gate: fail LOUD if Offline / WARM UP shoot dies or waits on net."""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"(?:async )?function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        raise AssertionError(f"missing function {name}")
    return m.group(0)


def _fail(msg: str) -> None:
    raise AssertionError(f"SABLEQA FAIL: offline shoot died — {msg}")


def main() -> int:
    try:
        html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
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

        sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
        if not sample:
            _fail("AimSample class missing")
        for field in ("uv", "valid", "lifted", "confidence", "t_hw"):
            if f"this.{field}" not in sample.group(0):
                _fail(f"AimSample field {field} changed")

        fire = _js_fn(js, "fire")
        if re.search(r"await\s+", fire):
            _fail("fire() awaits — HID is soft-locked behind a promise")
        if "/api/lobby" in fire or "fetch(" in fire:
            _fail("fire() talks to net — lift/HID is behind the lobby")
        if "aimBus.fire" not in fire:
            _fail("fire() no longer peeks AimBus")
        if "coastTrack" in fire or "updateAim" in fire:
            _fail("fire() recomputes aim")
        if "intersectObjects" not in fire:
            _fail("local hitscan gone")
        hid_at = fire.find("SablePerf.markHid")
        report_at = fire.find("reportSharedFire")
        if hid_at < 0 or report_at < 0 or hid_at > report_at:
            _fail("shared report must run after local hitscan, never instead of it")
        if "sharedMatch()" not in fire:
            _fail("shared report must be gated — Offline/WARM UP must shoot without a room")

        match = _js_fn(js, "sharedMatch")
        if "!S.warmup" not in match or "S.online" not in match:
            _fail("sharedMatch() must exclude WARM UP and Offline")

        start = _js_fn(js, "startRange")
        guard = start.find("sharedMatch()")
        local = start.find("spawnOrb3D")
        if guard < 0 or local < 0 or local < guard:
            _fail("startRange must spawn a local first plate unless sharedMatch")
        if "0.2" not in start or "-6.6" not in start:
            _fail("local first plate left the pad")

        warm = _js_fn(js, "lobbyWarmup")
        if "S.warmup = true" not in warm:
            _fail("WARM UP flag missing")
        if "/api/lobby/start" in warm:
            _fail("WARM UP started the shared house")
        if re.search(r"await\s+", warm):
            _fail("WARM UP awaits net — not one-click local practice")
        if 'setPhase("range")' not in warm and 'play("range")' not in warm:
            _fail("WARM UP no longer drops into Range")

        if 'id="btn-lobby-warmup"' not in html or "WARM UP" not in html:
            _fail("waiting room lost WARM UP — shared house would be the only way to shoot")
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("sableqa offline shoot ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
