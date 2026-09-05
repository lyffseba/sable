#!/usr/bin/env python3
"""SableAudio contract: sparse gallery dry-tick miss + hit punch + lift mint.

Fail loud on silence (verbs gone), a music/ambience bed, third-party
audio packs, audio that gates HID fire, or mint-tell VO that hides the
gun. Lift mint-tell must stay a short cue quieter than miss/hit/HUD.
Does not change SableQA floors.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402

AUDIO = ROOT / "proto" / "audio.js"

_THIRD_PARTY = (
    "freesound",
    "mixkit",
    "epidemic sound",
    "pixabay",
    "opengameart",
    "sonniss",
    "unreal marketplace",
    "unity asset store",
    "bbc sound",
    "zapslat",
    "zapsplat",
    "audiojungle",
    "pond5",
    "artlist",
    "epidemic-sound",
)

_BED = (
    "createconvolver",
    "createdynamicscompressor",
    "createperiodicwave",
    ".loop = true",
    ".loop=true",
    "loopstart",
    "createbuffersource",
)

_AUDIO_SUFFIX = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aiff", ".aac"}


def _fail(msg: str) -> None:
    raise AssertionError(f"SABLEAUDIO FAIL: {msg}")


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"(?:async )?function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        _fail(f"missing function {name}")
    return m.group(0)


def _js_const(src: str, name: str) -> float:
    m = re.search(rf"(?:export )?const {name} = (-?[0-9.]+)", src)
    if not m:
        _fail(f"missing const {name}")
    return float(m.group(1))


def test_module_and_bar() -> None:
    if not AUDIO.is_file():
        _fail("proto/audio.js missing — gallery audio path died")
    src = AUDIO.read_text(encoding="utf-8")
    if "SableAudio" not in src:
        _fail("SableAudio name missing")
    if _js_const(src, "SABLE_AUDIO_MISS_HZ") != 1850:
        _fail("dry-tick miss must stay 1850 Hz")
    if _js_const(src, "SABLE_AUDIO_MISS_MS") != 28:
        _fail("dry-tick miss must stay 28 ms")
    if _js_const(src, "SABLE_AUDIO_GAIN_CAP") > 0.12:
        _fail("SableAudio must stay quieter than SableHUD chips (gain cap 0.12)")
    miss = _js_fn(src, "missTick")
    hit = _js_fn(src, "hitBlip")
    lift = _js_fn(src, "liftMint")
    tell = _js_fn(src, "mintTell")
    tap = _js_fn(src, "tap")
    if "createOscillator" not in tap:
        _fail("SableAudio tap silenced — original oscillators died")
    if "tap(" not in miss and "createOscillator" not in miss:
        _fail("missTick silenced — dry tick died")
    if "tap(" not in hit and "createOscillator" not in hit:
        _fail("hitBlip silenced — hit punch died")
    if "tap(" not in lift and "createOscillator" not in lift:
        _fail("liftMint silenced — mint-tell chirp died")
    if "liftMint" not in tell:
        _fail("mintTell hook must call liftMint")
    if "SABLE_AUDIO_MISS_HZ" not in miss:
        _fail("missTick must use the 1850 Hz dry-tick const")
    if "SABLE_AUDIO_LIFT_GAIN" not in lift:
        _fail("liftMint must use the dedicated lift gain")
    if _js_const(src, "SABLE_AUDIO_LIFT_MS") > 28:
        _fail("lift mint must stay a short cue — not longer than the dry-tick")
    if '"Mint. Lift."' not in src or "SABLE_AUDIO_MINT_TELL" not in src:
        _fail("locked SableCancho mint-tell line Mint. Lift. must live in audio.js")
    if "Math.random" in src:
        _fail("SableAudio must not hide aim noise with RNG")
    if "speechSynthesis" in src:
        _fail("mint-tell must not use speechSynthesis / third-party voices")
    bang = _js_fn(src, "bang")
    if "createOscillator" in bang or "createGain" in bang:
        _fail("bang() must stay a silent SablePerf hook — shot verbs are after resolve")
    whistle = _js_fn(src, "pullWhistle")
    if "createOscillator" in whistle or "createGain" in whistle:
        _fail("pullWhistle must stay silent — lift mint is liftMint, not a spawn whistle")


def test_no_bed_or_third_party() -> None:
    audio = AUDIO.read_text(encoding="utf-8")
    low = audio.lower()
    for needle in _BED:
        if needle in low:
            _fail(f"ambience / bed / bloom processing ({needle})")
    proto = ROOT / "proto"
    for path in proto.rglob("*"):
        if not path.is_file():
            continue
        if "vendor" in path.parts:
            continue
        if path.suffix.lower() in _AUDIO_SUFFIX:
            _fail(f"binary audio asset {path.relative_to(ROOT)} — oscillators only")
        if path.suffix.lower() not in {".js", ".html", ".css", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for needle in _THIRD_PARTY:
            if needle in text:
                _fail(f"third-party audio pack in {path.relative_to(ROOT)} ({needle})")


def test_gains_stay_thin() -> None:
    src = AUDIO.read_text(encoding="utf-8")
    for raw in re.findall(r"gain\.gain\.setValueAtTime\(([0-9.]+)", src):
        if float(raw) > 0.12:
            _fail(f"gain {raw} louder than SableHUD chips")
    lift_g = _js_const(src, "SABLE_AUDIO_LIFT_GAIN")
    miss_g = _js_const(src, "SABLE_AUDIO_MISS_GAIN")
    hit_g = _js_const(src, "SABLE_AUDIO_HIT_GAIN")
    cap = _js_const(src, "SABLE_AUDIO_GAIN_CAP")
    if lift_g >= miss_g or lift_g >= hit_g:
        _fail("lift mint must stay quieter than dry-tick miss and hit punch")
    if lift_g > cap or miss_g > cap or hit_g > cap:
        _fail("SableAudio gains must stay under SABLE_AUDIO_GAIN_CAP")
    js = proto_js()
    house = (ROOT / "proto" / "house.js").read_text(encoding="utf-8")
    if "gain.gain.setValueAtTime(0.42" in js or "setValueAtTime(0.42" in house:
        _fail("loud pre-resolve bang returned")
    if "setValueAtTime(0.3" in house:
        _fail("loud combo hitBlip returned in house.js")


def test_after_resolve_not_a_gate() -> None:
    js = proto_js()
    fire = _js_fn(js, "fire")
    if "aimBus.fire" not in fire:
        _fail("fire() no longer peeks AimBus")
    if re.search(r"await\s+", fire):
        _fail("fire() awaits — audio must not gate HID")
    if "decodeAudioData" in fire or "AudioBuffer" in fire:
        _fail("fire() decodes audio — that is a gate")
    if "coastTrack" in fire or "updateAim" in fire:
        _fail("fire() recomputes aim")
    begin_at = fire.find("SablePerf.begin")
    bang_at = fire.find("bang();")
    if begin_at < 0 or bang_at < 0 or begin_at > bang_at:
        _fail("SablePerf t0 must stay before bang()")
    intersect = fire.find("intersectObjects")
    if intersect < 0:
        _fail("gallery hitscan left fire()")
    hit_at = fire.find("hitBlip", intersect)
    miss_at = fire.find("missTick", intersect)
    mark_at = fire.find("SablePerf.markHid", intersect)
    if hit_at < 0 or miss_at < 0:
        _fail("gallery hit punch / dry-tick miss left fire() after hitscan")
    if mark_at < 0 or hit_at < mark_at or miss_at < mark_at:
        _fail("hit/miss audio must stay after shot resolve (markHid / hitscan)")
    if "liftMint" in fire or "mintTell" in fire or "afterLiftState" in fire:
        _fail("lift mint must not enter fire() — never a fire gate")
    ranged = _js_fn(js, "updateRange")
    if "missTick" not in ranged:
        _fail("escape / dry miss must still play the dry tick")
    if "hitBlip" not in _js_fn(js, "shatterTarget3D"):
        # shatter is visual; punch lives on the fire resolve — require the fire path.
        if "shatterTarget3D" not in fire or "hitBlip" not in fire:
            _fail("plate hit/shatter lost the hit punch")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")


def test_playlist_untouched() -> None:
    html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
    js = proto_js()
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
    if 'id="btn-bay"' not in html or "WARM UP" not in html or "ENTER RANGE" not in html:
        _fail("playlist chrome lost a practice / Bay path")


def test_lift_mint_after_state() -> None:
    js = proto_js()
    after = _js_fn(js, "afterLiftState")
    if "mintTell" not in after and "liftMint" not in after:
        _fail("afterLiftState must play the mint-tell after lift")
    frame_at = js.find("function frame(")
    if frame_at < 0:
        _fail("frame() missing")
    mode_at = js.find("updateMode", frame_at)
    tell_at = js.find("afterLiftState", frame_at)
    if tell_at < 0:
        _fail("frame must cue lift mint after lift state")
    if mode_at >= 0 and tell_at < mode_at:
        _fail("lift mint must run after updateMode writes lift, never before")
    if "afterLiftState();" not in js:
        _fail("lift mint rising-edge helper left the client")
    keys = js[js.find('addEventListener("keydown"') : js.find('addEventListener("keyup"')]
    if "afterLiftState" not in keys:
        _fail("Space / T lift must still cue mint-tell (DESKTOP / force GUN)")
    fire = _js_fn(js, "fire")
    if re.search(r"await\s+", fire):
        _fail("fire() awaits — audio must not gate HID")
    after = _js_fn(js, "afterLiftState")
    if re.search(r"await\s+", after) or "async function afterLiftState" in js:
        _fail("afterLiftState awaits — lift mint must not stall Offline/HID")
    play = _js_fn(js, "play")
    if "mintTell" in play or "liftMint" in play or "afterLiftState" in play:
        _fail("play() must not wait on the mint-tell — Offline stays one-click")


def test_vo_does_not_hide_the_gun() -> None:
    js = proto_js()
    hud = _js_fn(js, "drawHUD")
    if "Mint. Lift." in hud or "SABLE_AUDIO_MINT_TELL" in hud or "voText" in hud:
        _fail("gallery HUD painted mint-tell VO over the cuff")
    if "Impact" in hud or "H * 0.78" in hud or "H*0.78" in hud:
        _fail("VO/HUD hides the gun")
    after = _js_fn(js, "afterLiftState")
    if "fillText" in after or "fillRect" in after or "Bay.vo" in after:
        _fail("afterLiftState painted VO over the gun")
    for name in ("liftMint", "mintTell"):
        body = _js_fn(js, name)
        if "fillText" in body or "fillRect" in body:
            _fail(f"{name} drew VO over the cuff")
    if "Bay.vo(Locker.operator.vo.lift)" in js:
        _fail("lift VO chip hides the gun — mint-tell is the short audio cue only")
    bay_at = js.find("function drawBayHUD")
    if bay_at < 0:
        _fail("drawBayHUD missing")
    bay = js[bay_at : bay_at + 2800]
    if "Impact" in bay:
        _fail("Bay VO billboard hides the gun")
    if "H * 0.5" in bay or "H*0.5" in bay or "H * 0.78" in bay:
        _fail("Bay VO painted over the reticle / cuff")
    if re.search(r"(?:italic )?700 (?:3[0-9]|[4-9][0-9]|[1-9][0-9]{2,})px", bay):
        _fail("Bay VO type grew over the cuff")
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample fields changed — keep the locked struct")


def test_docs() -> None:
    bible = (ROOT / "docs/PRODUCTION.md").read_text(encoding="utf-8")
    if "SableAudio" not in bible:
        _fail("PRODUCTION.md must name the SableAudio bar")
    if "dry-tick" not in bible.lower() and "dry tick" not in bible.lower():
        _fail("PRODUCTION.md must name the dry-tick miss")
    if "hit punch" not in bible.lower():
        _fail("PRODUCTION.md must name the hit punch")
    if "mint-tell" not in bible.lower() and "mint tell" not in bible.lower():
        _fail("PRODUCTION.md must name the mint-tell lift cue")
    if "Mint. Lift." not in bible:
        _fail("PRODUCTION.md must lock the SableCancho mint-tell line")
    if "test_sableaudio.py" not in bible:
        _fail("PRODUCTION.md must fail loud through test_sableaudio.py")
    if "hide the gun" not in bible.lower() and "hides the gun" not in bible.lower():
        _fail("PRODUCTION.md must fail loud if mint-tell VO hides the gun")
    if "v0.20.0" not in bible:
        _fail("do not drop the SableHUD v0.20.0 stand")
    modes = (ROOT / "docs/modes.md").read_text(encoding="utf-8")
    if "SableAudio" not in modes:
        _fail("docs/modes.md must note sparse gallery audio")
    if "Mint. Lift." not in modes:
        _fail("docs/modes.md must lock the mint-tell line")
    if "cuff" not in modes.lower() and "hide the gun" not in modes.lower():
        _fail("docs/modes.md must refuse mint-tell VO over the cuff")
    cancho = (ROOT / "docs/operators/cancho.md").read_text(encoding="utf-8")
    if "Mint. Lift." not in cancho:
        _fail("cancho.md must record the locked mint-tell VO copy")
    if "cuff" not in cancho.lower() and "hide" not in cancho.lower():
        _fail("cancho.md must refuse painting mint-tell over the cuff")


def test_ci_wires_the_lock() -> None:
    ci = (ROOT / "tools/ci.sh").read_text(encoding="utf-8")
    if "test_sableaudio.py" not in ci:
        _fail("ci.sh must run the SableAudio contract")
    if "proto/audio.js" not in ci:
        _fail("ci.sh must syntax-check proto/audio.js")
    src_list = (ROOT / "tools/proto_src.py").read_text(encoding="utf-8")
    if "audio.js" not in src_list:
        _fail("proto_src must concat audio.js so contract tests see the verbs")


def main() -> int:
    try:
        test_module_and_bar()
        test_no_bed_or_third_party()
        test_gains_stay_thin()
        test_after_resolve_not_a_gate()
        test_lift_mint_after_state()
        test_vo_does_not_hide_the_gun()
        test_playlist_untouched()
        test_docs()
        test_ci_wires_the_lock()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("sableaudio ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
