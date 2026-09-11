#!/usr/bin/env python3
"""SablePort path skeleton: docs + thin host seams, zero foreign DNA.

Fail loud if the Chromium / MacBook Pro ship floor dies, if host id
leaves sable, if root README Requirements re-sell Safari / Firefox as
first-class ship browsers without that floor, if docs/port claim a
desktop-only / Godot-first product host, if the verb leaves
aimbus-hand-gesture, if the port notes drift
off the locked bars (hand point + shark-fin → AimBus peek, charger-plug
reload, DESKTOP HID honesty fallback, 128 Hz tick, Look bible, modes),
if runtime art grows Valve/Epic DNA, or if Offline / WARM UP trap,
player-facing Bay chrome, AimSample / fire peek / R6 / Worker / HUD /
audio soft-locks move. Port docs may name BAY / ENTER BAY as playlist
seams — that is architecture, not a live gun. Gallery already scans a
subset; this owns the full walk.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from foreign_dna import FOREIGN_DNA, REQUIRED_DNA, dna_hits, scan_runtime_art  # noqa: E402
from proto_src import proto_js  # noqa: E402

PORT_JS = ROOT / "proto" / "port.js"
PORT_DOC = ROOT / "docs" / "port.md"


def _fail(msg: str) -> None:
    raise AssertionError(f"SABLEPORT FAIL: {msg}")


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"(?:async )?function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        _fail(f"missing function {name}")
    return m.group(0)


def _js_const(src: str, name: str) -> str:
    m = re.search(rf"(?:export )?const {name} = ([^;\n]+)", src)
    if not m:
        _fail(f"missing const {name}")
    return m.group(1).strip()


_ENGINEERING_OK = (
    "engineering path",
    "engineering-only",
    "engineering only",
    "non-product",
    "not a second product",
    "not the product",
    "not a product",
)


def _godot_first_product_claim(text: str) -> bool:
    """True when a doc claims Godot/native as the product host."""
    low = text.lower()
    if "godot-first" in low:
        return True
    if re.search(r"desktop-only product", low):
        return True
    if re.search(r"product host is (godot|native|desktop)\b", low):
        return True
    if re.search(
        r"\b(godot|native) (is|as) the (primary |playable )?(product|ship) (host|surface|floor)",
        low,
    ):
        return True
    for sent in re.split(r"[.\n]+", text):
        sl = sent.lower()
        if "godot" not in sl:
            continue
        if any(ok in sl for ok in _ENGINEERING_OK):
            continue
        if re.search(
            r"\b(product host|primary (playable|surface|host)|ship (host|surface|floor)|playable surface)\b",
            sl,
        ):
            return True
    return False


def test_godot_first_detector() -> None:
    if not _godot_first_product_claim("The product host is Godot."):
        _fail("Godot-first detector died — a Godot product host must fail CI")
    if not _godot_first_product_claim("Godot is the primary playable surface."):
        _fail("Godot-first detector died — a Godot playable surface must fail CI")
    if not _godot_first_product_claim("Ship a desktop-only product host."):
        _fail("Godot-first detector died — desktop-only product host must fail CI")
    ok = (
        "Godot / native work is an engineering path only. "
        "It is not a second product and not the product host."
    )
    if _godot_first_product_claim(ok):
        _fail("engineering-only Godot must not trip the Godot-first detector")


def test_port_doc_boundaries() -> None:
    if not PORT_DOC.is_file():
        _fail("docs/port.md missing — port path notes died")
    text = PORT_DOC.read_text(encoding="utf-8")
    if "SablePort" not in text:
        _fail("docs/port.md must name SablePort ownership")
    if "AimBus" not in text or "HID" not in text:
        _fail("docs/port.md must keep AimBus peek and HID as honesty fallback")
    if "aimbus-hand-gesture" not in text:
        _fail("docs/port.md must name the aimbus-hand-gesture verb")
    if "shark-fin" not in text.lower() and "shark fin" not in text.lower():
        _fail("docs/port.md must lock shark-fin as the product shoot")
    if "charger-plug" not in text.lower() and "charger plug" not in text.lower():
        _fail("docs/port.md must keep charger-plug reload")
    if "hand point" not in text.lower() and "hand pointing" not in text.lower():
        _fail("docs/port.md must lock hand point as product aim")
    if "honesty fallback" not in text.lower():
        _fail("docs/port.md must keep DESKTOP HID as honesty fallback, not the product verb")
    if "chromium" not in text.lower() or "macbook pro" not in text.lower():
        _fail("docs/port.md must lock Chromium on MacBook Pro as the ship floor")
    if "not optional" not in text.lower():
        _fail("docs/port.md must say the Chromium / MacBook floor is not optional")
    if "chromium-macbook" not in text:
        _fail("docs/port.md must name the chromium-macbook surface")
    if "godot" not in text.lower() or "engineering path" not in text.lower():
        _fail("docs/port.md must keep Godot/native as engineering path only")
    if "second product" not in text.lower():
        _fail("docs/port.md must refuse a second product")
    if _godot_first_product_claim(text):
        _fail("docs/port.md claimed a Godot-first / desktop-only product host")
    if "sablehostfeel" not in text.lower():
        _fail("docs/port.md must keep CS2/UEFN literacy behind sableHostFeel()")
    if "128 Hz" not in text:
        _fail("docs/port.md must lock the 128 Hz sim tick")
    if "Look bible" not in text and "Look bible" not in text.lower():
        _fail("docs/port.md must name the Look bible")
    if "charcoal" not in text.lower() or "mint" not in text.lower():
        _fail("docs/port.md must keep the Look palette")
    if "GALLERY" not in text or "BAY" not in text or "WARM UP" not in text:
        _fail("docs/port.md must keep the SABLE playlist")
    if "ENTER BAY" not in text:
        _fail("docs/port.md must keep ENTER BAY as a playlist / port architecture seam")
    if "architecture" not in text.lower():
        _fail("foreign-title literacy must stay architecture notes")
    if 'play("range")' not in text:
        _fail("docs/port.md must keep play(range) as gallery entry")
    if "AimSample" not in text:
        _fail("docs/port.md must keep AimSample locked")
    if "Valve" not in text or "Epic" not in text:
        _fail("docs/port.md must refuse Valve / Epic asset DNA")
    if "Mint. Lift." not in text:
        _fail("docs/port.md must keep the mint-tell soft-lock")
    if "SableHUD" not in text or "SableAudio" not in text:
        _fail("docs/port.md must leave HUD / audio behavior locked")
    if "hide the gun" not in text.lower() and "paint VO" not in text:
        _fail("docs/port.md must keep mint-tell as audio only — no VO over the cuff")
    if "silhouette literacy" not in text.lower():
        _fail("docs/port.md must keep Fortnite-class as silhouette literacy only")
    if "Ship addendum" not in text:
        _fail("docs/port.md must keep the Ship addendum on this Look cut")
    if "Epic / UEFN / Valve" not in text and "Epic / UEFN / Valve DNA" not in text:
        _fail("docs/port.md must fail loud on Epic / UEFN / Valve DNA in proto/art")


def test_host_seam() -> None:
    if not PORT_JS.is_file():
        _fail("proto/port.js missing — host seam died")
    src = PORT_JS.read_text(encoding="utf-8")
    if _js_const(src, "SABLE_PORT_HOST") != '"sable"':
        _fail("runtime host id must stay sable — no foreign title")
    if _js_const(src, "SABLE_PORT_SURFACE") != '"chromium-macbook"':
        _fail("ship surface must stay chromium-macbook")
    if _js_const(src, "SABLE_PORT_VERB") != '"aimbus-hand-gesture"':
        _fail("verb seam must stay aimbus-hand-gesture")
    if _js_const(src, "SABLE_PORT_SIM_HZ") != "128":
        _fail("tick seam must stay 128")
    if "charcoal-bone-mint-rust" not in src:
        _fail("Look seam must stay charcoal-bone-mint-rust")
    if '"gallery"' not in src or '"bay"' not in src or '"warmup"' not in src:
        _fail("mode seam lost a SABLE playlist id")
    if "function sableHostId" not in src or "function sableHostFeel" not in src:
        _fail("host adapter stubs must stay real functions")
    feel = _js_fn(src, "sableHostFeel")
    if "surface:" not in feel and "surface :" not in feel:
        _fail("sableHostFeel must publish surface so adapters can assert the web floor")
    if "SABLE_PORT_SURFACE" not in feel and '"chromium-macbook"' not in feel:
        _fail("chromium-macbook surface must be assertable from SablePort.feel()")
    if "SablePort" in src and "surface: SABLE_PORT_SURFACE" not in src and "surface: \"chromium-macbook\"" not in src:
        _fail("SablePort must publish the chromium-macbook surface")
    if "window.SablePort" not in src:
        _fail("SablePort must publish the host identity")
    for needle in dna_hits(src):
        _fail(f"Valve/Epic DNA in proto/port.js ({needle})")
    game = (ROOT / "proto" / "game.js").read_text(encoding="utf-8")
    if 'import "./port.js"' not in game:
        _fail("game.js must load the SablePort seam")
    if "play(" in src or "fire(" in src or "drawHUD" in src or "liftMint" in src:
        _fail("port.js must not own play / fire / HUD / audio")


def test_runtime_art_forbids_foreign_dna() -> None:
    hits = scan_runtime_art(ROOT)
    if hits:
        _fail("Valve/Epic/UEFN asset DNA in runtime art (" + "; ".join(hits) + ")")
    for needle in REQUIRED_DNA:
        if needle not in FOREIGN_DNA:
            _fail(f"DNA needle list must keep {needle}")
    if "CS2" not in FOREIGN_DNA or "UEFN" not in FOREIGN_DNA:
        _fail("DNA needle list must keep CS2 / UEFN")
    if "Fortnite" not in dna_hits("Fortnite-class CANCHO"):
        _fail("dna_hits must catch Fortnite even as Fortnite-class")
    if dna_hits("charcoal bone mint rust silhouette"):
        _fail("CANCHO palette is not foreign DNA")
    modes = (ROOT / "docs" / "modes.md").read_text(encoding="utf-8")
    if "architecture notes" not in modes.lower():
        _fail("docs/modes.md must keep CS map literacy as architecture notes")
    if "silhouette literacy" not in modes.lower():
        _fail("docs/modes.md must keep Fortnite-class as silhouette literacy only")
    if "Valve" not in modes or "Epic" not in modes:
        _fail("docs/modes.md must refuse Valve / Epic asset DNA")
    if "UEFN" not in modes:
        _fail("docs/modes.md must refuse UEFN asset DNA")
    if "docs/port.md" not in modes and "SablePort" not in modes:
        _fail("docs/modes.md must point at the SablePort path")


def test_soft_locks_hold() -> None:
    js = proto_js()
    html = (ROOT / "proto" / "index.html").read_text(encoding="utf-8")
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
    if 'play("bay")' in offline.group(0):
        _fail("OFFLINE was rerouted into Bay")
    warm = _js_fn(js, "lobbyWarmup")
    if "/api/lobby/start" in warm or re.search(r"await\s+", warm):
        _fail("WARM UP trapped behind net")
    if 'setPhase("range")' not in warm and 'play("range")' not in warm:
        _fail("WARM UP no longer drops into the Yard gallery")
    if 'play("bay")' in warm or 'setPhase("bay")' in warm:
        _fail("WARM UP dropped into Bay")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")
    fire = _js_fn(js, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if re.search(r"await\s+", fire):
        _fail("fire() awaits — HID is behind a promise")
    if "coastTrack" in fire or "updateAim" in fire:
        _fail("fire() recomputes aim")
    if re.search(r"postMessage|detectForVideo|hands_worker|new Worker", fire):
        _fail("fire() waits on the Hands worker")
    if re.search(r"stepSim\s*\(|simAcc|SIM_DT", fire):
        _fail("fire() waits on the sim tick")
    if "liftMint" in fire or "mintTell" in fire:
        _fail("mint-tell entered fire() — audio/HUD soft-lock moved")
    if _js_const(js, "SIM_HZ") != "128":
        _fail("R6 sim must stay 128 Hz")
    if _js_const(js, "SABLE_HUD_H") != "22":
        _fail("SableHUD bar must stay thin (22px)")
    hud = _js_fn(js, "drawHUD")
    if "drawSableChip" not in hud or '"SCORE "' not in hud:
        _fail("SableHUD chips moved")
    if "Impact" in hud or "RAISE YOUR HAND" in hud:
        _fail("HUD hid the gun")
    if "Mint. Lift." in hud or "SABLE_AUDIO_MINT_TELL" in hud:
        _fail("gallery HUD painted mint-tell VO over the cuff")
    if "Bay.vo(Locker.operator.vo.lift)" in js:
        _fail("lift VO chip hides the gun — mint-tell is audio only")
    audio = (ROOT / "proto" / "audio.js").read_text(encoding="utf-8")
    if '"Mint. Lift."' not in audio or "function liftMint" not in audio:
        _fail("mint-tell / SableAudio behavior left audio.js")
    if "WARM UP" not in html or "ENTER RANGE" not in html:
        _fail("playlist lost a Yard path")
    if 'id="btn-bay"' in html or "ENTER BAY" in html:
        _fail("playlist still offers Bay — Yard is the sole active map")
    paint = _js_fn(js, "paintLobby")
    if "5v5" in paint or "ALPHA" in paint or "BRAVO" in paint:
        _fail("playlist chrome still sells 5v5 / ALPHA-BRAVO")
    start = _js_fn(js, "lobbyStartRange")
    if "enterRangePreserve()" not in start:
        _fail("ENTER RANGE lost phase-preserve — calib/lock would trap HID")
    if re.search(r"await\s+", start):
        _fail("ENTER RANGE awaits net — lift/HID is behind the lobby POST")
    if "ACESFilmicToneMapping" in js:
        _fail("ACES filmic hides aim noise — Look bloomed")
    if "NoToneMapping" not in js:
        _fail("Look lock wants linear / NoToneMapping")
    if "shadowBlur" in hud or "glow" in hud.lower():
        _fail("gallery HUD bloomed over the reticle")
    cross = _js_fn(js, "drawCrosshair")
    if "shadowBlur" in cross or "glow" in cross.lower():
        _fail("reticle bloom is forbidden")
    if "emissiveIntensity: 0.45" in js or "emissiveIntensity:0.45" in js:
        _fail("mint plate bloom must stay dead")


def test_bible_and_ci() -> None:
    bible = (ROOT / "docs" / "PRODUCTION.md").read_text(encoding="utf-8")
    if "SablePort" not in bible or "docs/port.md" not in bible:
        _fail("PRODUCTION.md must name the SablePort path")
    if "chromium" not in bible.lower() or "macbook pro" not in bible.lower():
        _fail("PRODUCTION.md must lock Chromium on MacBook Pro as the ship floor")
    if "godot" not in bible.lower() or "engineering" not in bible.lower():
        _fail("PRODUCTION.md must keep Godot/native as engineering-only")
    if "second product" not in bible.lower():
        _fail("PRODUCTION.md must refuse a second product")
    if _godot_first_product_claim(bible):
        _fail("PRODUCTION.md claimed a Godot-first / desktop-only product host")
    if "v0.20.0" not in bible:
        _fail("do not drop the SableHUD v0.20.0 stand")
    if "SableAudio" not in bible or "Mint. Lift." not in bible:
        _fail("PRODUCTION.md must keep the mint-tell / audio gate")
    if "test_sableaudio.py" not in bible:
        _fail("PRODUCTION.md must keep the mint-tell soft-lock test")
    if "hide the gun" not in bible.lower() and "hides the gun" not in bible.lower():
        _fail("PRODUCTION.md must keep mint-tell VO from hiding the gun")
    if "128 Hz" not in bible:
        _fail("PRODUCTION.md must keep the 128 Hz contract")
    if "silhouette literacy" not in bible.lower():
        _fail("PRODUCTION.md must keep Fortnite-class as silhouette literacy only")
    if "Fortnite-class" in bible and "literacy only" not in bible.lower():
        _fail("PRODUCTION.md Fortnite-class must stay literacy only — not runtime DNA")
    if "test_sableport.py" not in bible:
        _fail("PRODUCTION.md must keep the SablePort DNA gate")
    tick = (ROOT / "docs" / "tick.md").read_text(encoding="utf-8")
    if "SablePort" not in tick and "docs/port.md" not in tick:
        _fail("docs/tick.md must point at the port path")
    aim = (ROOT / "docs" / "aim_pipeline.md").read_text(encoding="utf-8")
    if "SablePort" not in aim and "docs/port.md" not in aim:
        _fail("docs/aim_pipeline.md must point at the port path")
    legal = (ROOT / "docs" / "legal.md").read_text(encoding="utf-8")
    if "docs/port.md" not in legal:
        _fail("docs/legal.md must point at the port path")
    if "silhouette literacy" not in legal.lower():
        _fail("docs/legal.md must keep Fortnite-class as silhouette literacy only")
    if "UEFN" not in legal:
        _fail("docs/legal.md must refuse UEFN DNA in runtime art")
    ci = (ROOT / "tools" / "ci.sh").read_text(encoding="utf-8")
    if "test_sableport.py" not in ci:
        _fail("ci.sh must run the SablePort DNA / seam gate")
    if "test_sablelook.py" not in ci or "test_sableyard.py" not in ci:
        _fail("ci.sh must keep SableLook / SableYard on the Look bible")
    if "proto/port.js" not in ci:
        _fail("ci.sh must syntax-check proto/port.js")
    src_list = (ROOT / "tools" / "proto_src.py").read_text(encoding="utf-8")
    if "port.js" not in src_list:
        _fail("proto_src must concat port.js so contract tests see the seam")


def test_readme_requirements_ship_floor() -> None:
    """Root README Requirements: Chromium / MacBook floor — no Safari/Firefox SKU."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    req = re.search(
        r"^## Requirements\s*\n[\s\S]*?(?=^#{1,3} |\Z)",
        readme,
        re.MULTILINE,
    )
    if not req:
        _fail("README.md lost Requirements")
    block = req.group(0)
    low = block.lower()
    if "chromium" not in low or "macbook" not in low:
        _fail(
            "README Requirements must lock Chromium on MacBook Pro–class "
            "as the ship floor"
        )
    leftover = "modern web browser (chrome, edge, safari, firefox)"
    if leftover in low:
        _fail(
            "README Requirements must not re-sell the multi-browser SKU "
            "(Chrome, Edge, Safari, Firefox) — floor is Chromium / MacBook"
        )
    if re.search(r"\bsafari\b|\bfirefox\b", low):
        framed = (
            "non-floor" in low
            or "not the floor" in low
            or "not first-class" in low
            or "not a first-class" in low
            or "stretch" in low
            or "not the ship" in low
        )
        if not framed:
            _fail(
                "README Requirements must not list Safari/Firefox as "
                "first-class ship browsers"
            )


def main() -> int:
    try:
        test_godot_first_detector()
        test_port_doc_boundaries()
        test_host_seam()
        test_runtime_art_forbids_foreign_dna()
        test_soft_locks_hold()
        test_bible_and_ci()
        test_readme_requirements_ship_floor()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("sableport ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
