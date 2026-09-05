#!/usr/bin/env python3
"""Salt House gallery mode: 60s scored loop, not a leftover Range.

Fail loud if Offline dies, Bay / WARM UP / ENTER RANGE vanish, Look
traps lift/HID, or the gallery loses score / round clock / end state.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402


def _fail(msg: str) -> None:
    raise AssertionError(f"GALLERY FAIL: {msg}")


def _fail_only_gun(msg: str) -> None:
    raise AssertionError(f"GALLERY FAIL: gallery became the only gun — {msg}")


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"(?:async )?function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        _fail(f"missing function {name}")
    return m.group(0)


def _js_const(src: str, name: str) -> float:
    m = re.search(rf"const {name} = (-?[0-9.]+)", src)
    if not m:
        _fail(f"missing const {name}")
    return float(m.group(1))


def test_boot_lobby_labels() -> None:
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    js = proto_js()
    if 'id="btn-play"' not in html or ">OFFLINE<" not in html:
        _fail("boot lost one-click OFFLINE")
    if "60s gallery" not in html and "60s GALLERY" not in html:
        _fail("boot must name the 60s gallery")
    if "GALLERY CLEAR" not in html:
        _fail("results lost the gallery end state")
    if "HOUSE CLEAR" in html:
        _fail("results still says leftover HOUSE CLEAR")
    if 'id="btn-bay"' not in html or ">BAY<" not in html:
        _fail_only_gun("boot lost BAY")
    if 'id="btn-lobby-range"' not in html or "ENTER RANGE" not in html:
        _fail_only_gun("lobby lost ENTER RANGE")
    if 'id="btn-lobby-warmup"' not in html or "WARM UP" not in html:
        _fail_only_gun("lobby lost WARM UP")
    if 'id="btn-lobby-bay"' not in html or "ENTER BAY" not in html:
        _fail_only_gun("lobby lost ENTER BAY")

    offline = re.search(
        r'\$\("btn-play"\)\.addEventListener\("click", \(\) => \{[\s\S]*?play\("range"\)',
        js,
    )
    if not offline:
        _fail("OFFLINE must still call play(range) in one click")
    if "S.online = false" not in offline.group(0):
        _fail("OFFLINE must stay local")
    if "S.warmup = false" not in offline.group(0):
        _fail("OFFLINE must clear WARM UP")
    if 'play("bay")' in offline.group(0):
        _fail_only_gun("OFFLINE was rerouted into Bay")

    play = _js_fn(js, "play")
    if 'target === "bay"' not in play:
        _fail("play() must still honor Bay")
    if 'targetGameMode === "bay"' not in play and 'target === "bay"' not in play:
        _fail("play() must not dump Bay into gallery")
    if '"gallery"' not in play:
        _fail("play(range) must set the gallery playlist")


def test_gallery_rules() -> None:
    js = proto_js()
    if _js_const(js, "RANGE_MS") != 60000:
        _fail("gallery round must stay 60s")
    over = _js_fn(js, "galleryOver")
    if "RANGE_MS" not in over:
        _fail("galleryOver must use RANGE_MS")
    left = _js_fn(js, "galleryLeftMs")
    if "RANGE_MS" not in left:
        _fail("galleryLeftMs must use RANGE_MS")
    sess = _js_fn(js, "gallerySessionLabel")
    if 'return "GALLERY"' not in sess:
        _fail("offline session must read GALLERY")
    if "WARM UP" not in sess:
        _fail("WARM UP must stay a practice label, not a scored lock")
    if "SHARED" not in sess:
        _fail("shared house must keep its own session label")
    ranged = _js_fn(js, "updateRange")
    if "galleryOver" not in ranged:
        _fail("updateRange must end the round through galleryOver")
    if 'setPhase("results")' not in ranged:
        _fail("gallery must still hit the results end state")
    hud = _js_fn(js, "drawHUD")
    if "gallerySessionLabel" not in hud or "galleryLeftMs" not in hud:
        _fail("HUD must paint gallery score + round clock")
    if '"60s GALLERY"' not in hud:
        _fail("HUD must chip 60s GALLERY")
    if '"ROUND"' not in hud:
        _fail("HUD must name the round clock")
    results = _js_fn(js, "showResults")
    if '"ROUND"' not in results or "60s" not in results:
        _fail("results must keep the 60s round")
    if '"SCORE"' not in results:
        _fail("results lost score")


def test_practice_and_bay_survive() -> None:
    js = proto_js()
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/start" in warm:
        _fail_only_gun("WARM UP started the shared house")
    if re.search(r"await\s+", warm):
        _fail("WARM UP awaits net — practice is soft-locked")
    if 'setPhase("range")' not in warm and 'play("range")' not in warm:
        _fail_only_gun("WARM UP no longer drops into the house")
    if 'play("bay")' in warm or 'setPhase("bay")' in warm:
        _fail_only_gun("WARM UP dropped into Bay")
    start_room = _js_fn(js, "lobbyStartRange")
    if 'play("range")' not in start_room:
        _fail_only_gun("ENTER RANGE no longer starts the Salt House")
    if "/api/lobby/start" not in start_room:
        _fail_only_gun("host ENTER RANGE no longer shares the house")
    start_bay = _js_fn(js, "lobbyStartBay")
    if 'play("bay")' not in start_bay and 'setPhase("bay")' not in start_bay:
        _fail_only_gun("ENTER BAY no longer drops into the booth")
    if "/api/lobby/start" in start_bay:
        _fail("ENTER BAY started the shared gallery")
    if "ENTER RANGE" not in html or "WARM UP" not in html or ">BAY<" not in html:
        _fail_only_gun("playlist chrome lost a practice / Bay path")


def test_look_and_hid_not_trapped() -> None:
    js = proto_js()
    fire = _js_fn(js, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if re.search(r"await\s+", fire):
        _fail("fire() awaits — HID is behind a promise")
    if "/api/lobby" in fire or "fetch(" in fire:
        _fail("fire() talks to net — Look/playlist trapped HID")
    if "coastTrack" in fire or "updateAim" in fire:
        _fail("fire() recomputes aim")
    if re.search(r"postMessage|detectForVideo|hands_worker|new Worker", fire):
        _fail("fire() waits on the Hands worker")
    if "ACESFilmicToneMapping" in js:
        _fail("ACES filmic hides aim noise")
    if "NoToneMapping" not in js:
        _fail("Look lock wants linear / NoToneMapping")
    if "emissiveIntensity: 0.45" in js or "emissiveIntensity:0.45" in js:
        _fail("mint plate bloom must stay dead")
    hud = _js_fn(js, "drawHUD")
    if "shadowBlur" in hud or "glow" in hud.lower():
        _fail("gallery HUD must not bloom over the reticle")
    cross = _js_fn(js, "drawCrosshair")
    if "shadowBlur" in cross or "glow" in cross.lower():
        _fail("reticle bloom is forbidden")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")
    start = _js_fn(js, "startRange")
    if "sharedMatch()" not in start or "spawnOrb3D" not in start:
        _fail("startRange must still branch shared vs local")
    if "0.2" not in start or "-6.6" not in start:
        _fail("local first plate left the pad")


def test_modes_doc() -> None:
    modes = (ROOT / "docs/modes.md").read_text(encoding="utf-8")
    if "GALLERY" not in modes or "OFFLINE" not in modes:
        _fail("docs/modes.md must name OFFLINE gallery")
    if "WARM UP" not in modes or "ENTER RANGE" not in modes or "BAY" not in modes:
        _fail("docs/modes.md must keep Bay / WARM UP / ENTER RANGE")
    if 'play("range")' not in modes:
        _fail("docs/modes.md must keep play(range) as the house entry")
    bible = (ROOT / "docs/PRODUCTION.md").read_text(encoding="utf-8")
    if "Salt House / Gallery" not in bible and "gallery mode" not in bible.lower():
        _fail("PRODUCTION.md must name Salt House as gallery mode")


def main() -> int:
    try:
        test_boot_lobby_labels()
        test_gallery_rules()
        test_practice_and_bay_survive()
        test_look_and_hid_not_trapped()
        test_modes_doc()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("gallery mode ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
