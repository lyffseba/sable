#!/usr/bin/env python3
"""SableLook lock: unshaded/baked CANCHO, readable plates, no reticle bloom.

Fail loud if ACES / mint emissive return, plates leave bone+mint bayUnshaded,
Yard bunkers take bone fill, Offline / WARM UP die, AimSample moves, or
fire() stops peeking AimBus.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402

BONE = 0xE6E0D1
CHAR = 0x1A222C
RUST = 0x8C472E


def _fail(msg: str) -> None:
    raise AssertionError(f"SABLELOOK FAIL: {msg}")


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"(?:async )?function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        _fail(f"missing function {name}")
    return m.group(0)


def _luma(hex_rgb: int) -> float:
    r = ((hex_rgb >> 16) & 0xFF) / 255.0
    g = ((hex_rgb >> 8) & 0xFF) / 255.0
    b = (hex_rgb & 0xFF) / 255.0
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def test_unshaded_cancho_bible() -> None:
    js = proto_js()
    house = (ROOT / "proto/house.js").read_text(encoding="utf-8")
    if "ACESFilmicToneMapping" in js:
        _fail("ACES filmic hides aim noise")
    if "NoToneMapping" not in js:
        _fail("Look lock wants linear / NoToneMapping")
    if "emissiveIntensity: 0.45" in js or "emissiveIntensity:0.45" in js:
        _fail("mint plate bloom must stay dead")
    if "function bayUnshaded" not in house:
        _fail("unshaded helper must stay the shared paint")
    if "MeshBasicMaterial" not in house:
        _fail("Look must stay MeshBasic / baked")
    if "0x151c22" in house or "0x8aa8b8" in house:
        _fail("cool milsim steel must not return")
    if "0x0a0c10" not in house or "0x101214" not in house:
        _fail("scene + fog must stay charcoal")
    inflate = _js_fn(house, "inflateMat")
    if "bayUnshaded" not in inflate:
        _fail("yard props must match bayUnshaded")
    if "flatShading: false" in inflate or "roughness: 0.22" in inflate:
        _fail("inflateMat must not be milsim plastic")
    look = _js_fn(house, "applyLockerLook")
    if "bodyHex" not in look or "mintHex" not in look or "rustHex" not in look:
        _fail("CANCHO tell (charcoal / mint / rust) must stay on applyLockerLook")
    if "emissive" in look.lower():
        _fail("locker look must not emit")


def test_plate_vs_bunker_contrast() -> None:
    house = (ROOT / "proto/house.js").read_text(encoding="utf-8")
    plates = _js_fn(house, "createTargetMesh")
    if "emissiveIntensity" in plates:
        _fail("plates must not emit")
    if "bayUnshaded" not in plates:
        _fail("plates must stay unshaded")
    if "boneHex" not in plates or "mintHex" not in plates:
        _fail("plates must stay bone + mint")
    yard = house[house.find("function buildYardBunkers") : house.find("const YARD_PEEKS")]
    if "function buildYardBunkers" not in yard:
        _fail("Yard bunker builder left house.js")
    if "boneHex" in yard:
        _fail("Yard bunker fill took bone — plates would hide")
    if "mintHex" in yard:
        _fail("Yard mint must not compete with plate cores")
    if "0x1a222c" not in yard:
        _fail("Yard bunker mass must stay rib charcoal")
    if "rustHex" not in yard:
        _fail("Yard bunkers lost the rust rim")
    if _luma(BONE) - _luma(CHAR) < 0.5:
        _fail("bone vs charcoal contrast died")
    if _luma(BONE) - _luma(RUST) < 0.35:
        _fail("bone vs rust contrast died")
    shatter = _js_fn(house, "shatterTarget3D")
    if "hsl(" in shatter:
        _fail("shards must stay bone/mint, not neon hsl")
    if "boneHex" not in shatter or "mintHex" not in shatter:
        _fail("shatter shards must stay readable bone/mint")


def test_no_reticle_bloom() -> None:
    js = proto_js()
    hud = _js_fn(js, "drawHUD")
    if "shadowBlur" in hud or "glow" in hud.lower():
        _fail("gallery HUD bloomed over the reticle")
    cross = _js_fn(js, "drawCrosshair")
    if "shadowBlur" in cross or "glow" in cross.lower():
        _fail("reticle bloom is forbidden")
    chip = _js_fn(js, "drawSableChip")
    if "shadowBlur" in chip or "glow" in chip.lower():
        _fail("SableHUD chips bloomed")


def test_look_does_not_trap_hid() -> None:
    js = proto_js()
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    if 'id="btn-play"' not in html or ">OFFLINE<" not in html:
        _fail("OFFLINE one-click died")
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
    fire = _js_fn(js, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if re.search(r"await\s+", fire):
        _fail("fire() awaits — HID is behind a promise")
    if "coastTrack" in fire or "updateAim" in fire:
        _fail("fire() recomputes aim")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")


def test_bible_names_look_lock() -> None:
    bible = (ROOT / "docs/PRODUCTION.md").read_text(encoding="utf-8")
    if "test_sablelook.py" not in bible:
        _fail("PRODUCTION.md must keep the SableLook gate")
    if "No ACES" not in bible and "no ACES" not in bible:
        _fail("PRODUCTION.md must keep the unshaded / no-ACES bible")
    if "bone plates stay readable" not in bible.lower():
        _fail("PRODUCTION.md must keep plate/bunker readability")
    if "silhouette literacy" not in bible.lower():
        _fail("PRODUCTION.md must keep Fortnite-class as silhouette literacy only")
    ci = (ROOT / "tools/ci.sh").read_text(encoding="utf-8")
    if "test_sablelook.py" not in ci:
        _fail("ci.sh must run SableLook")
    port = (ROOT / "docs/port.md").read_text(encoding="utf-8")
    if "Look bible" not in port:
        _fail("docs/port.md must name the Look bible")
    if "charcoal / rust" not in port.lower() and "charcoal / rust" not in port:
        _fail("docs/port.md must keep charcoal / rust Yard bunkers")


def main() -> int:
    try:
        test_unshaded_cancho_bible()
        test_plate_vs_bunker_contrast()
        test_no_reticle_bloom()
        test_look_does_not_trap_hid()
        test_bible_names_look_lock()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("sablelook ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
