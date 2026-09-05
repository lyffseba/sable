#!/usr/bin/env python3
"""UI-flow: waiting-room warm-up one click, return one click, OFFLINE stays one click."""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        raise AssertionError(f"missing function {name}")
    return m.group(0)


def main() -> int:
    try:
        html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
        css = (ROOT / "proto/style.css").read_text(encoding="utf-8")
        js = proto_js()
        if ".range-bar[hidden]" not in css:
            raise AssertionError("range-bar hidden must beat display:flex so OFFLINE has no RETURN TO LOBBY")

        if 'id="btn-play"' not in html or ">OFFLINE<" not in html:
            raise AssertionError("boot must keep one-click OFFLINE")
        play = re.search(
            r'\$\("btn-play"\)\.addEventListener\("click", \(\) => \{[\s\S]*?play\("range"\)',
            js,
        )
        if not play:
            raise AssertionError("OFFLINE must still call play(range) in one click")
        if "S.online = false" not in play.group(0):
            raise AssertionError("OFFLINE must not stay in the lobby")

        if 'id="btn-lobby-warmup"' not in html or "WARM UP" not in html:
            raise AssertionError("waiting room needs a WARM UP control")
        if 'id="btn-return-lobby"' not in html or "RETURN TO LOBBY" not in html:
            raise AssertionError("warm-up range needs RETURN TO LOBBY")
        if 'id="btn-results-lobby"' not in html:
            raise AssertionError("warm-up results need RETURN TO LOBBY")

        warm = _js_fn(js, "lobbyWarmup")
        if "/api/lobby/leave" in warm:
            raise AssertionError("warm-up must not leave the room")
        if "/api/lobby/warmup" not in warm:
            raise AssertionError("warm-up must mark the seat, not start the match")
        if "/api/lobby/start" in warm:
            raise AssertionError("WARM UP must not start the room Range")
        if 'setPhase("range")' not in warm and 'play("range")' not in warm:
            raise AssertionError("warm-up must drop into the same Range")

        ret = _js_fn(js, "returnToLobby")
        if "/api/lobby/leave" in ret:
            raise AssertionError("RETURN TO LOBBY must keep membership")
        if "/api/lobby/resume" not in ret:
            raise AssertionError("return must clear warmup without destroying the room")
        if 'setPhase("lobby")' not in ret:
            raise AssertionError("return must be one click back to the waiting room")

        fire = _js_fn(js, "fire")
        if "coastTrack" in fire or "updateAim" in fire:
            raise AssertionError("warm-up range must keep the stripped fire verb")
        if "aimBus.fire" not in fire or "shot.lifted" not in fire:
            raise AssertionError("sticky lift peek must stay on the fire verb")
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("warmup flow ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
