#!/usr/bin/env python3
"""SableYard lock: sole map, few/low charcoal-rust bunkers, bone plates read.

Fail loud if Yard bunkers take bone/mint fill, grow tall clutter, move
YARD_PEEKS, Bay returns to player chrome, Offline / WARM UP die, or
Valve / Epic DNA lands in the Yard sheet.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from foreign_dna import FOREIGN_DNA  # noqa: E402
from proto_src import proto_js  # noqa: E402

YARD_PEEKS = (
    "[-3.4, -0.7, -3.9]",
    "[3.4, -0.7, -3.9]",
    "[-0.5, 0.35, -6.6]",
    "[2.4, 0.55, -8.1]",
    "[-2.6, 0.05, -10.5]",
    "[0.8, -0.15, -12.0]",
    "[3.1, 0.15, -13.5]",
    "[-3.0, 0.25, -14.1]",
)


def _fail(msg: str) -> None:
    raise AssertionError(f"SABLEYARD FAIL: {msg}")


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"(?:async )?function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        _fail(f"missing function {name}")
    return m.group(0)


def _yard_builder() -> str:
    house = (ROOT / "proto/house.js").read_text(encoding="utf-8")
    start = house.find("function buildYardBunkers")
    end = house.find("const YARD_PEEKS")
    if start < 0 or end < 0 or end <= start:
        _fail("buildYardBunkers / YARD_PEEKS left house.js")
    return house[start:end]


def test_few_low_charcoal_rust() -> None:
    yard = _yard_builder()
    if "boneHex" in yard:
        _fail("bunker fill took bone — plates would hide")
    if "mintHex" in yard:
        _fail("yard mint must not compete with the centerline / plates")
    if "0x1a222c" not in yard:
        _fail("bunker mass must stay rib charcoal 0x1a222c")
    if "rustHex" not in yard:
        _fail("bunkers lost rust rims / pad / drum")
    if yard.count("sausageX") != 2:
        _fail("Yard must keep exactly two low beams")
    if yard.count("ConeGeometry") != 1:
        _fail("Yard must keep exactly one low peak")
    if "ConeGeometry(0.98, 0.92" not in yard:
        _fail("peak must stay low (0.92 m)")
    if "ConeGeometry(0.92, 1.85" in yard or "z: -11.0" in yard:
        _fail("tall clutter bunkers must stay culled")
    if "sausageX(0.38, 2.8" not in yard:
        _fail("beams must stay low (0.38 r × 2.8)")
    if "-3.4" not in yard or "3.4" not in yard or "-4.2" not in yard:
        _fail("beam coords left the firing-line kit")
    if "-1.6" not in yard or "-7.0" not in yard:
        _fail("drum left the firing-line kit")
    if "2.2" not in yard or "-8.5" not in yard:
        _fail("peak left the firing-line kit")
    if "CylinderGeometry(0.72, 0.72, 0.08" not in yard:
        _fail("peak rust rim left the low tell")
    if "wireframe" in yard:
        _fail("wireframe net muddies plate silhouettes")
    if "0x2a2c28" in yard:
        _fail("mud green must not paint the Yard")
    spec = (ROOT / "docs/yard.md").read_text(encoding="utf-8")
    if "low charcoal crawler" not in spec or "low charcoal pyramid" not in spec:
        _fail("docs/yard.md must name charcoal bunkers")
    if "rust caps" not in spec or "rust rim" not in spec:
        _fail("docs/yard.md must keep rust rims")
    if "few, low" not in spec and "few and low" not in spec:
        _fail("docs/yard.md must keep bunkers few / low")
    if "bone crawler" in spec or "bone pyramid" in spec:
        _fail("docs/yard.md still paints bone bunker fill")


def test_peeks_and_first_plate() -> None:
    house = (ROOT / "proto/house.js").read_text(encoding="utf-8")
    peeks = house[house.find("const YARD_PEEKS") : house.find("function applyLockerLook")]
    for coord in YARD_PEEKS:
        if coord not in peeks:
            _fail(f"YARD_PEEKS moved — playlist coords must stay ({coord})")
    js = proto_js()
    start = _js_fn(js, "startRange")
    if "sharedMatch()" not in start or "spawnOrb3D" not in start:
        _fail("startRange must still branch shared vs local")
    if "0.2" not in start or "-6.6" not in start:
        _fail("local first plate left the pad")
    wait = _js_fn(js, "startWaitingYard")
    if "spawnOrb3D" not in wait:
        _fail("waiting arena lost local Yard plates")
    if "0.2" not in wait or "-6.6" not in wait:
        _fail("waiting-arena first plate left the pad")


def test_sole_map_and_one_click() -> None:
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    js = proto_js()
    if 'id="btn-play"' not in html or ">OFFLINE<" not in html:
        _fail("boot lost one-click OFFLINE")
    if 'id="btn-bay"' in html or re.search(r">\s*BAY\s*<", html):
        _fail("boot still offers BAY — Yard is the sole active map")
    if 'id="btn-lobby-bay"' in html or "ENTER BAY" in html:
        _fail("lobby still offers ENTER BAY — Bay is parked")
    if "WARM UP" not in html or "ENTER RANGE" not in html:
        _fail("playlist lost a Yard path")
    offline = re.search(
        r'\$\("btn-play"\)\.addEventListener\("click", \(\) => \{[\s\S]*?play\("range"\)',
        js,
    )
    if not offline:
        _fail("OFFLINE must still call play(range) in one click")
    if "S.online = false" not in offline.group(0):
        _fail("OFFLINE must stay local")
    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/start" in warm or re.search(r"await\s+", warm):
        _fail("WARM UP trapped behind net")
    if 'setPhase("range")' not in warm and 'play("range")' not in warm:
        _fail("WARM UP no longer drops into the Yard")
    fire = _js_fn(js, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")
    modes = (ROOT / "docs/modes.md").read_text(encoding="utf-8")
    if "sole active" not in modes.lower():
        _fail("docs/modes.md must keep Yard as the sole active map")
    if "charcoal / rust" not in modes.lower() and "charcoal / rust" not in modes:
        _fail("docs/modes.md must keep charcoal / rust Yard bunkers")


def test_yard_sheet_and_dna() -> None:
    sheet = ROOT / "art/concepts/yard.svg"
    if not sheet.is_file():
        _fail("art/concepts/yard.svg missing — Yard paint sheet died")
    svg = sheet.read_text(encoding="utf-8")
    if "#1a222c" not in svg or "#8C472E" not in svg:
        _fail("Yard sheet lost charcoal / rust bunkers")
    if "#E6E0D1" not in svg or "#59F2C7" not in svg:
        _fail("Yard sheet lost the bone plate / mint core")
    if "#2a2c28" in svg:
        _fail("Yard sheet picked up mud green")
    hall = (ROOT / "art/concepts/hall.svg").read_text(encoding="utf-8")
    if "#1a222c" not in hall or "#E6E0D1" not in hall:
        _fail("hall sheet must keep charcoal mass behind the bone plate")
    files = (
        ROOT / "proto/house.js",
        ROOT / "docs/yard.md",
        ROOT / "art/concepts/yard.svg",
        ROOT / "art/concepts/hall.svg",
        ROOT / "art/blender/build_sable_kit.py",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        low = text.lower()
        for needle in FOREIGN_DNA:
            if needle.lower() in low:
                _fail(f"Valve/Epic asset DNA in {path.relative_to(ROOT)} ({needle})")


def test_bible_and_ci() -> None:
    bible = (ROOT / "docs/PRODUCTION.md").read_text(encoding="utf-8")
    if "test_sableyard.py" not in bible:
        _fail("PRODUCTION.md must keep the SableYard gate")
    if "yard bunkers charcoal / rust" not in bible.lower():
        _fail("PRODUCTION.md must keep charcoal / rust Yard bunkers")
    ci = (ROOT / "tools/ci.sh").read_text(encoding="utf-8")
    if "test_sableyard.py" not in ci:
        _fail("ci.sh must run SableYard")
    art = (ROOT / "art/README.md").read_text(encoding="utf-8")
    if "charcoal / rust" not in art:
        _fail("art/README.md must keep charcoal / rust Yard bunkers")


def main() -> int:
    try:
        test_few_low_charcoal_rust()
        test_peeks_and_first_plate()
        test_sole_map_and_one_click()
        test_yard_sheet_and_dna()
        test_bible_and_ci()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("sableyard ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
