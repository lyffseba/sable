#!/usr/bin/env python3
"""SableQA product gate: fail LOUD if Offline / WARM UP die, HID waits, or Bay is the only gun."""

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


def _fail_only_gun(msg: str) -> None:
    raise AssertionError(f"SABLEQA FAIL: Bay became the only gun — {msg}")


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
        fields = re.findall(r"this\.(\w+)", sample.group(0))
        if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
            _fail("AimSample fields changed — keep the locked struct")

        css = (ROOT / "proto/style.css").read_text(encoding="utf-8")
        if "#game.nocursor" not in css or "cursor: none" not in css:
            _fail("lock-never-cursor lost the CSS hide")
        move = re.search(r"pointermove[\s\S]{0,280}", js)
        if not move or "if (S.desktop)" not in move.group(0):
            _fail("OS pointer writes aim outside DESKTOP — lock-never-cursor died")
        sync = _js_fn(js, "syncCursor")
        if 'phase === "lock"' not in sync or "nocursor" not in sync:
            _fail("lock phase must hide the OS cursor")

        fire = _js_fn(js, "fire")
        if re.search(r"await\s+", fire):
            _fail("fire() awaits — HID is soft-locked behind a promise")
        if "/api/lobby" in fire or "fetch(" in fire:
            _fail("fire() talks to net — lift/HID is behind the lobby")
        if "aimBus.fire" not in fire:
            _fail("fire() no longer peeks AimBus")
        if "coastTrack" in fire or "updateAim" in fire:
            _fail("fire() recomputes aim")
        if re.search(r"postMessage|createImageBitmap|detectForVideo|hands_worker|new Worker", fire):
            _fail("fire() waits on the Hands worker")
        if re.search(r"requestAnimationFrame|stepSim\s*\(|simAcc|SIM_DT|SIM_HZ", fire):
            _fail("fire() waits on the sim/rAF tick")
        if "performance.now() - S.rangeStart" in fire:
            _fail("fire() couples to present")
        if "intersectObjects" not in fire:
            _fail("local hitscan gone")
        hid_at = fire.find("SablePerf.markHid")
        report_at = fire.find("reportSharedFire")
        if hid_at < 0 or report_at < 0 or hid_at > report_at:
            _fail("shared report must run after local hitscan, never instead of it")
        begin_at = fire.find("SablePerf.begin")
        bang_at = fire.find("bang();")
        if begin_at < 0 or bang_at < 0 or begin_at > bang_at:
            _fail("SablePerf t0 must be before bang — HID→hitscan bar is unordered")
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
        if re.search(r"setTimeout|stepSim|simAcc", warm):
            _fail("WARM UP grew a tick tax")
        if 'setPhase("range")' not in warm and 'play("range")' not in warm:
            _fail("WARM UP no longer drops into Range")

        if 'id="btn-lobby-warmup"' not in html or "WARM UP" not in html:
            _fail("waiting room lost WARM UP — shared house would be the only way to shoot")
        if 'play("bay")' in warm or 'setPhase("bay")' in warm:
            _fail_only_gun("WARM UP dropped into Bay instead of local Range")

        if 'id="btn-lobby-range"' not in html or "ENTER RANGE" not in html:
            _fail_only_gun("lobby lost ENTER RANGE")
        start_room = _js_fn(js, "lobbyStartRange")
        if 'play("range")' not in start_room:
            _fail_only_gun("ENTER RANGE no longer starts the Salt House")
        if "/api/lobby/start" not in start_room:
            _fail_only_gun("host ENTER RANGE no longer shares the house")

        if 'play("bay")' in play.group(0):
            _fail_only_gun("OFFLINE was rerouted into Bay")

        if "GALLERY CLEAR" not in html:
            _fail("gallery lost its end state — Salt House is leftover Range again")
        if "gallerySessionLabel" not in js or "galleryOver" not in js:
            _fail("gallery mode rules left house.js")
        sess = _js_fn(js, "gallerySessionLabel")
        if 'return "GALLERY"' not in sess:
            _fail("OFFLINE gallery session label died")
        if "WARM UP" not in sess:
            _fail("WARM UP must stay a practice label")
        hud = _js_fn(js, "drawHUD")
        if "shadowBlur" in hud or "shadowBlur" in _js_fn(js, "drawCrosshair"):
            _fail("Look bloomed over the reticle")
        if "ACESFilmicToneMapping" in js:
            _fail("Look trapped aim noise with ACES")

        to_win = re.search(r"const BAY_TO_WIN = ([0-9.]+)", js)
        if not to_win or float(to_win.group(1)) != 5:
            _fail("Bay first-to-5 peek rule left the booth")
        if "fireBay3D" not in fire:
            _fail("Bay fire no longer peeks through fire() → fireBay3D")
        bay_fire = _js_fn(js, "fireBay3D")
        if "fetch(" in bay_fire or "/api/lobby" in bay_fire:
            _fail("Bay fire talks to net — lift/HID is behind the lobby")
        start_bay = _js_fn(js, "lobbyStartBay")
        if "/api/lobby/start" in start_bay:
            _fail("ENTER BAY started the shared house")
        if re.search(r"await\s+", start_bay):
            _fail("ENTER BAY awaits net — lift/HID is behind the lobby")
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("sableqa offline shoot ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
