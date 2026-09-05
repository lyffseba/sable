#!/usr/bin/env python3
"""Salt House gallery mode: 60s scored loop, not a leftover Range.

Fail loud if Offline dies, WARM UP / ENTER RANGE vanish, Bay reappears
on player chrome, Look traps lift/HID, or the gallery loses score /
round clock / end state.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from foreign_dna import FOREIGN_DNA  # noqa: E402
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
    if 'id="btn-bay"' in html or re.search(r">\s*BAY\s*<", html):
        _fail("boot still offers BAY — Yard is the sole active map")
    if 'id="btn-lobby-range"' not in html or "ENTER RANGE" not in html:
        _fail_only_gun("lobby lost ENTER RANGE")
    if 'id="btn-lobby-warmup"' not in html or "WARM UP" not in html:
        _fail_only_gun("lobby lost WARM UP")
    if 'id="btn-lobby-bay"' in html or "ENTER BAY" in html:
        _fail("lobby still offers ENTER BAY — Bay is parked")

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
    if '"ROUND "' not in hud and '"ROUND"' not in hud:
        _fail("HUD must name the round clock")
    if '"SCORE "' not in hud:
        _fail("HUD must chip SCORE")
    if '"GALLERY CLEAR"' not in hud:
        _fail("HUD must chip the gallery end state")
    if "drawSableChip" not in hud:
        _fail("gallery feedback must stay on the SableHUD chip bar")
    if "Impact" in hud:
        _fail("SableHUD chips must stay thin — no Impact billboard")
    if "RAISE YOUR HAND" in hud or "ESC = miss" in hud:
        _fail("tutorial wall on the gallery HUD")
    if "H * 0.78" in hud or "H*0.78" in hud or "H * 0.5" in hud:
        _fail("HUD hides the gun or the reticle")
    if _js_const(js, "SABLE_HUD_H") != 22:
        _fail("SableHUD bar must stay thin (22px)")
    chip = _js_fn(js, "drawSableChip")
    if "SABLE_HUD_H" not in chip:
        _fail("drawSableChip must use the thin SableHUD height")
    if "shadowBlur" in chip or "glow" in chip.lower():
        _fail("SableHUD chips must not bloom")
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
    if "enterRangePreserve()" not in start_room and 'play("range")' not in start_room:
        _fail_only_gun("ENTER RANGE no longer starts the Salt House")
    if "/api/lobby/start" not in start_room:
        _fail_only_gun("host ENTER RANGE no longer shares the house")
    if re.search(r"await\s+", start_room):
        _fail("ENTER RANGE awaits net — lift/HID is behind the lobby POST")
    start_bay = _js_fn(js, "lobbyStartBay")
    if 'play("bay")' not in start_bay and 'setPhase("bay")' not in start_bay:
        _fail("parked lobbyStartBay lost the booth drop")
    if "/api/lobby/start" in start_bay:
        _fail("parked lobbyStartBay started the shared gallery")
    if "ENTER RANGE" not in html or "WARM UP" not in html:
        _fail_only_gun("playlist chrome lost a Yard path")
    if 'id="btn-bay"' in html or "ENTER BAY" in html:
        _fail("playlist chrome still offers Bay")


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
    if "phase !== \"range\"" not in hud:
        _fail("SableHUD must not thicken the lobby")
    if "setPhase" in hud or "fire(" in hud or "aimBus" in hud:
        _fail("HUD trapped lift/HID")
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


def test_original_geometry() -> None:
    """CS map literacy is architecture notes. Runtime geometry is first-party."""
    modes = (ROOT / "docs/modes.md").read_text(encoding="utf-8")
    if "architecture notes" not in modes.lower():
        _fail("CS map literacy must stay architecture notes only")
    if "Valve" not in modes or "Epic" not in modes:
        _fail("docs/modes.md must refuse Valve / Epic asset DNA")
    lessons = (ROOT / "research/design-lessons.md").read_text(encoding="utf-8")
    if "No Fortnite/CS2" not in lessons and "No Fortnite" not in lessons:
        _fail("design-lessons must keep the refuse-third-party-IP lock")
    files = (
        ROOT / "proto/house.js",
        ROOT / "proto/port.js",
        ROOT / "docs/yard.md",
        ROOT / "docs/maps/bay.md",
        ROOT / "art/concepts/hall.svg",
        ROOT / "art/concepts/gauntlet.svg",
        ROOT / "art/concepts/plate.svg",
        ROOT / "art/blender/build_sable_kit.py",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        low = text.lower()
        for needle in FOREIGN_DNA:
            if needle.lower() in low:
                _fail(f"Valve/Epic asset DNA in {path.relative_to(ROOT)} ({needle})")
    house = (ROOT / "proto/house.js").read_text(encoding="utf-8")
    if "[-3.4, -0.7, -3.9]" not in house or "YARD_PEEKS" not in house:
        _fail("Salt House peek coords left original SABLE geometry")


def test_modes_doc() -> None:
    modes = (ROOT / "docs/modes.md").read_text(encoding="utf-8")
    if "GALLERY" not in modes or "OFFLINE" not in modes:
        _fail("docs/modes.md must name OFFLINE gallery")
    if "WARM UP" not in modes or "ENTER RANGE" not in modes:
        _fail("docs/modes.md must keep WARM UP / ENTER RANGE")
    if "sole active" not in modes.lower() and "parked" not in modes.lower():
        _fail("docs/modes.md must park Bay / name Yard as the sole active map")
    if 'play("range")' not in modes:
        _fail("docs/modes.md must keep play(range) as the house entry")
    bible = (ROOT / "docs/PRODUCTION.md").read_text(encoding="utf-8")
    if "Salt House / Gallery" not in bible and "gallery mode" not in bible.lower():
        _fail("PRODUCTION.md must name Salt House as gallery mode")
    if "SableHUD" not in modes:
        _fail("docs/modes.md must name the thin SableHUD bar")
    if "SablePort" not in modes and "docs/port.md" not in modes:
        _fail("docs/modes.md must point at the SablePort path")
    if "v0.20.0" not in bible:
        _fail("PRODUCTION.md must stand v0.20.0 until Build tags this gallery HUD tip")


def main() -> int:
    try:
        test_boot_lobby_labels()
        test_gallery_rules()
        test_practice_and_bay_survive()
        test_look_and_hid_not_trapped()
        test_original_geometry()
        test_modes_doc()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("gallery mode ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
