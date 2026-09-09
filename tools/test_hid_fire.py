#!/usr/bin/env python3
"""HID fire uses the last AimSample even if the current camera frame is missing."""

from __future__ import annotations

import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402


class AimSample:
    def __init__(self, uv=(0.5, 0.5), valid=False, lifted=False, confidence=0.0, t_hw=0):
        self.uv = uv
        self.valid = valid
        self.lifted = lifted
        self.confidence = confidence
        self.t_hw = t_hw

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AimSample) and vars(self) == vars(other)


class AimBus:
    def __init__(self) -> None:
        self._latest = AimSample()

    def publish(self, sample: AimSample) -> None:
        self._latest = sample

    def peek(self) -> AimSample:
        return self._latest

    def fire(self) -> AimSample:
        # Never wait. Never poll a camera. Peek only.
        return self._latest


def test_python_mailbox() -> None:
    bus = AimBus()
    first = AimSample(uv=(0.41, 0.62), valid=True, confidence=0.8, t_hw=42)
    bus.publish(first)
    # Current camera frame is missing — no publish.
    shot = bus.fire()
    assert shot == first, "fire must return the last sample"
    again = bus.fire()
    assert again.t_hw == 42, "second fire without a frame still uses last sample"
    assert shot.uv != (0.0, 0.0), "must not snap to 0,0"


def test_desktop_first_click_uv() -> None:
    """DESKTOP first pad publishes click UV — default mailbox is screen-center."""
    bus = AimBus()
    assert bus.peek().uv == (0.5, 0.5), "AimBus default must stay screen-center"
    click = AimSample(uv=(0.22, 0.81), valid=True, lifted=True, confidence=1.0, t_hw=7)
    bus.publish(click)
    shot = bus.fire()
    assert shot.uv == (0.22, 0.81), "DESKTOP first pad must peek the click UV"
    assert shot.uv != (0.5, 0.5), "DESKTOP first pad must not peek screen-center"
    assert shot.valid is True and shot.lifted is True, "DESKTOP first pad must be a live gun"


def desktop_publish(seeking: bool, lifted: bool, locked: bool, desktop: bool) -> tuple[bool, bool]:
    """publishAim valid/lifted bits. AimSample schema stays five fields."""
    valid = (not seeking) and (locked or desktop)
    return valid, lifted


def desktop_confidence(desktop: bool, quality: float) -> float:
    """publishAim confidence. DESKTOP is 1; cam keeps S.quality. Five fields."""
    if desktop:
        return 1.0
    return max(0.0, min(1.0, quality / 100.0))


def test_desktop_mailbox_truth() -> None:
    """Cam-deny DESKTOP must not publish seeking+unlifted. Q4 stays SEEKING."""
    # The lie: desktop+mode set, seeking/lifted never armed.
    valid, lifted = desktop_publish(True, False, False, True)
    if valid or lifted:
        raise AssertionError("fixture: unarmed DESKTOP must show the mailbox lie")
    # After updateMode DESKTOP truth.
    valid, lifted = desktop_publish(False, True, False, True)
    if not valid or not lifted:
        raise AssertionError("DESKTOP publishAim must be valid+lifted for a live gun")
    # Q4: camReady fail-to-lock is SEEKING — never a live desktop sample.
    valid, lifted = desktop_publish(True, False, False, False)
    if valid or lifted:
        raise AssertionError("Q4 SEEKING must not look like a live DESKTOP gun")


def test_desktop_confidence() -> None:
    """Cam-deny DESKTOP must not publish leftover tracker quality as confidence."""
    # The lie: S.quality stays ~0 from the hand tracker while DESKTOP owns aim.
    if desktop_confidence(True, 0) != 1.0:
        raise AssertionError("DESKTOP publishAim confidence must be 1 independent of S.quality")
    if desktop_confidence(True, 37) != 1.0:
        raise AssertionError("DESKTOP publishAim confidence must ignore leftover tracker quality")
    if desktop_confidence(False, 0) != 0.0:
        raise AssertionError("non-DESKTOP must still use S.quality")
    if abs(desktop_confidence(False, 80) - 0.8) > 1e-9:
        raise AssertionError("non-DESKTOP must still scale S.quality / 100")
    # Q4: camReady fail-to-lock is SEEKING — leftover quality stays cam, not 1.
    if desktop_confidence(False, 12) == 1.0:
        raise AssertionError("Q4 SEEKING must not invent DESKTOP confidence 1")
    pub = _js_fn(proto_js(), "publishAim")
    if "S.desktop ? 1" not in pub:
        raise AssertionError("publishAim must write confidence 1 when S.desktop")
    if "S.quality / 100" not in pub:
        raise AssertionError("non-DESKTOP publishAim must still use S.quality")


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        raise AssertionError(f"missing function {name}")
    return m.group(0)


HID_CLICK_UV = r"if \(S\.desktop \|\| S\.forceGun\) publishAim\(e\.clientX, e\.clientY\)"
HID_FIRE_GATE = r"if \(S\.desktop \|\| S\.forceGun \|\| productGunHidFire\(\)\)"
FORCEGUN_LOCK = (
    "`forceGun` re-arms pad as Q4 emergency only; Space is not a shot; "
    "`productGunHidFire` stays false."
)


def _hid_click_uv(hid: str) -> bool:
    return bool(re.search(HID_CLICK_UV, hid))


def _hid_fire_gate(body: str) -> bool:
    return bool(re.search(HID_FIRE_GATE, body))


def _space_keydown(src: str) -> str:
    keys = src[src.find('addEventListener("keydown"') : src.find('addEventListener("keyup"')]
    space = re.search(r'if \(e\.code === "Space"\) \{([^}]+)\}', keys)
    if not space:
        raise AssertionError("Space forceGun handler missing")
    return space.group(1)


def test_client_does_not_wait() -> None:
    src = proto_js()
    fire_src = _js_fn(src, "fire")
    banned = (
        r"await\s+",
        r"wait_for",
        r"poll_capture",
        r"requestVideoFrameCallback",
        r"requestAnimationFrame",
        r"stepSim\s*\(",
        r"simAcc",
        r"SIM_DT",
        r"SIM_HZ",
    )
    for pat in banned:
        if re.search(pat, fire_src):
            raise AssertionError(f"fire() gates fire on a camera wait ({pat})")
    if "class AimBus" not in src:
        raise AssertionError("proto client must define class AimBus")
    if "return this._latest" not in src:
        raise AssertionError("AimBus fire/peek must return this._latest")
    if "aimBus.fire" not in fire_src and "aimBus.peek" not in fire_src:
        raise AssertionError("fire must peek the AimBus mailbox")
    if "coastTrack" in fire_src or "updateAim" in fire_src:
        raise AssertionError("fire must not recompute aim — peek the last committed sample")
    if "publishAim" in fire_src:
        raise AssertionError("fire() must peek — DESKTOP publish lives on onHidPointerDown")
    fin = _js_fn(src, "maybeSharkFinFire")
    if "fire()" not in fin:
        raise AssertionError("shark-fin must peek through fire()")
    if "updateAim(" in fin or "publishAim(" in fin:
        raise AssertionError("shark-fin must not rewrite aim")
    if 'phase === "range"' in fin or 'phase === "bay"' in fin:
        raise AssertionError("maybeSharkFinFire must not re-gate the verb — waiting Yard would mute")
    if "function maybePinchFire" in src or "maybePinchFire(" in src:
        raise AssertionError("pinch must not peek -- maybePinchFire is retired")
    if "pinchHeld" in src:
        raise AssertionError("S.pinchHeld died with the pinch verb")
    frame = _js_fn(src, "frame")
    if "maybePinchFire" in frame:
        raise AssertionError("frame must not run pinch -- pinch is not a trigger")
    if frame.find("maybeSharkFinFire") > frame.find("maybeReloadGesture"):
        raise AssertionError("shark-fin must run before reload -- product shoot first")
    if frame.find("maybeReloadGesture") > frame.find("updateAim"):
        raise AssertionError("reload must run before updateAim")
    if frame.find("maybeSharkFinFire") > frame.find("updateAim"):
        raise AssertionError("shark-fin must peek last pointing UV before updateAim")
    if "S.aim" not in fire_src:
        raise AssertionError("hitscan must use last committed S.aim")
    if "shot.uv" not in fire_src:
        raise AssertionError("hitscan must peek AimBus UV")
    if "hitscanRange" not in fire_src:
        raise AssertionError("Range hitscan must be the house sphere")
    if "intersectObjects" in fire_src:
        raise AssertionError("Range hitscan must not mesh-test the spun hex")
    if "SablePerf.begin" not in fire_src or "SablePerf.markHid" not in fire_src:
        raise AssertionError("HID→hitscan must be wrapped by the optional SablePerf probe")
    begin_at = fire_src.find("SablePerf.begin")
    bang_at = fire_src.find("bang();")
    mark_at = fire_src.find("SablePerf.markHid")
    if begin_at < 0 or bang_at < 0:
        raise AssertionError("fire() must call SablePerf.begin and bang()")
    if begin_at > bang_at:
        raise AssertionError(
            "SablePerf.begin must start after the lift/desktop gate and before bang()"
        )
    if mark_at >= 0 and mark_at < bang_at:
        raise AssertionError("SablePerf.markHid must stay at first hitscan intersect")
    intersect = fire_src.find("hitscanRange(")
    mark_range = fire_src.find("SablePerf.markHid", intersect) if intersect >= 0 else -1
    if intersect < 0 or mark_range < 0:
        raise AssertionError("Range HID→hitscan must mark at the house sphere")
    probe = fire_src[intersect:mark_range]
    if "applyGunKick" in probe or "peekMuzzleWorld" in probe or "getWorldPosition" in probe:
        raise AssertionError("Look (gun kick / muzzle world) landed inside the HID→hitscan probe")
    bay = fire_src.find('phase === "bay"')
    bay_mark = fire_src.find("SablePerf.markHid", bay) if bay >= 0 else -1
    if bay < 0 or bay_mark < 0:
        raise AssertionError("Bay HID→hitscan must still mark")
    if "peekMuzzleWorld" in fire_src[bay:bay_mark] or "getWorldPosition" in fire_src[bay:bay_mark]:
        raise AssertionError("Bay peekMuzzleWorld landed inside the HID→hitscan probe")


def test_product_gun_mutes_hid_fire() -> None:
    """Product GUN pad must not peek/fire. DESKTOP / cam-deny still does."""
    src = proto_js()
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", src)
    if not sample:
        raise AssertionError("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        raise AssertionError("AimSample must stay five fields — do not invent a sixth")
    gate = _js_fn(src, "productGunHidFire")
    if "return true" in gate:
        raise AssertionError("productGunHidFire must stay false — HID is not product GUN shoot")
    if "return false" not in gate:
        raise AssertionError("productGunHidFire must return false")
    if "fire(" in gate:
        raise AssertionError("productGunHidFire must not peek — it only answers the gate")
    hid = _js_fn(src, "onHidPointerDown")
    if not _hid_click_uv(hid):
        raise AssertionError("DESKTOP / forceGun HID must still publish click UV before fire()")
    if "hidChromeTarget" not in hid:
        raise AssertionError("window HID must still spare chrome (button/input)")
    if 'window.addEventListener("pointerdown", onHidPointerDown)' not in src:
        raise AssertionError("HID click must still live on window — Fire is HID")
    live = re.search(
        r'if \(phase === "range" \|\| phase === "bay" \|\| phase === "lobby"\) \{([\s\S]*?)\n  \}',
        hid,
    )
    if not live:
        raise AssertionError("onHidPointerDown must still see range/bay/lobby")
    body = live.group(1)
    if re.search(r"^\s*fire\(\);\s*$", body, re.M):
        raise AssertionError(
            "range/lobby HID must not fire() when !S.desktop && !S.forceGun — product GUN is shark-fin"
        )
    if "S.desktop" not in body or "S.forceGun" not in body or "productGunHidFire()" not in body:
        raise AssertionError(
            "range/lobby HID fire must be S.desktop || S.forceGun || productGunHidFire()"
        )
    if "fire()" not in body:
        raise AssertionError("DESKTOP / forceGun pad must still peek through fire()")
    if not _hid_fire_gate(body):
        raise AssertionError(
            "range/lobby HID must gate fire() on S.desktop || S.forceGun || productGunHidFire()"
        )
    chrome = _js_fn(src, "hidChromeTarget")
    if "join-mute" not in chrome or "lobby-join" not in chrome:
        raise AssertionError("chrome spare must still release leftover JOIN/CODE after join")


def test_forcegun_rearms_pad() -> None:
    """Q4 Space re-arms pad peek. Space itself is not a shot. productGunHidFire stays false."""
    src = proto_js()
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", src)
    if not sample:
        raise AssertionError("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        raise AssertionError("AimSample must stay five fields — do not invent a sixth")
    gate = _js_fn(src, "productGunHidFire")
    if "return true" in gate:
        raise AssertionError("productGunHidFire must stay false — HID is not product GUN shoot")
    if "return false" not in gate:
        raise AssertionError("productGunHidFire must return false")
    hid = _js_fn(src, "onHidPointerDown")
    if "S.desktop = true" in hid or "armPracticeDesktop" in hid or "goDesktopRange" in hid:
        raise AssertionError("forceGun pad must not auto-desktop — Q4 forbids S.desktop=true")
    if not _hid_click_uv(hid):
        raise AssertionError("forceGun pad must publish OS cursor UV like DESKTOP")
    live = re.search(
        r'if \(phase === "range" \|\| phase === "bay" \|\| phase === "lobby"\) \{([\s\S]*?)\n  \}',
        hid,
    )
    if not live:
        raise AssertionError("onHidPointerDown must still see range/bay/lobby")
    body = live.group(1)
    if "S.forceGun" not in body:
        raise AssertionError("forceGun + pad must peek fire() — GUN chip with no legal fire() is a lie")
    if not _hid_fire_gate(body):
        raise AssertionError(
            "range/lobby HID must gate fire() on S.desktop || S.forceGun || productGunHidFire()"
        )
    if re.search(r"^\s*fire\(\);\s*$", body, re.M):
        raise AssertionError(
            "!desktop && !forceGun pad must not fire() on product GUN — shark-fin owns shoot"
        )
    space = _space_keydown(src)
    if "S.forceGun = true" not in space:
        raise AssertionError("Space must stay the Q4 forceGun escape")
    if "fire(" in space:
        raise AssertionError("Space must not peek fire() — Q4 escape is not a shot")
    if "updateMode(" not in space or "afterLiftState()" not in space:
        raise AssertionError("Space still only forceGun + updateMode + afterLiftState")
    if "S.desktop" in space or "goDesktopRange" in space or "armPracticeDesktop" in space:
        raise AssertionError("Space must not invent desktop")
    move = re.search(r'addEventListener\("pointermove", \(e\) => \{([\s\S]*?)\n\}\);', src)
    if not move:
        raise AssertionError("pointermove handler missing")
    if "S.forceGun" in move.group(1):
        raise AssertionError("pointermove must not publish forceGun UV — pad click only, not OS-cursor aim")
    chip = _js_fn(src, "drawModeChip")
    label = re.search(r"const label = ([^;]+);", chip)
    if not label:
        raise AssertionError("drawModeChip lost the MODE label")
    cond = label.group(1)
    seek_at = cond.find('"SEEKING"')
    if seek_at < 0 or "S.forceGun" not in cond[:seek_at]:
        raise AssertionError("chip must stay GUN on forceGun — do not leave SEEKING")
    for rel in (
        "docs/PRODUCTION.md",
        "docs/aim_pipeline.md",
        "research/TRACKING.md",
        "docs/modes.md",
    ):
        if FORCEGUN_LOCK not in _read(rel):
            raise AssertionError(f"{rel} must lock forceGun pad re-arm")


def test_hid_lives_on_window() -> None:
    """#hud is pointer-events: none. A canvasHUD listener never sees a real tap."""
    src = proto_js()
    css = (ROOT / "proto/style.css").read_text(encoding="utf-8")
    if 'canvasHUD.addEventListener("pointerdown"' in src:
        raise AssertionError(
            "HID click must not live on canvasHUD — #hud pointer-events: none mutes the pad"
        )
    if 'window.addEventListener("pointerdown", onHidPointerDown)' not in src:
        raise AssertionError("HID click must live on window — Fire is HID")
    hid = _js_fn(src, "onHidPointerDown")
    if "hidChromeTarget" not in hid:
        raise AssertionError("window HID must spare chrome (button/input)")
    if "fire()" not in hid:
        raise AssertionError("window HID must peek through fire()")
    if "updateAim" in hid or "coastTrack" in hid:
        raise AssertionError("window HID must not recompute aim — fire() peeks")
    if "aimBus" in hid:
        raise AssertionError("window HID must use publishAim / fire() — not touch AimBus")
    if not _hid_click_uv(hid):
        raise AssertionError(
            "DESKTOP / forceGun HID must publish click UV before fire() — first pad must not peek {0.5,0.5}"
        )
    pub = re.search(HID_CLICK_UV, hid)
    fire_at = hid.find("fire()")
    if not pub or fire_at < 0 or pub.start() > fire_at:
        raise AssertionError("DESKTOP / forceGun publishAim must land before fire() peek")
    for m in re.finditer(r"publishAim\s*\(", hid):
        window = hid[max(0, m.start() - 80) : m.start()]
        if "S.desktop" not in window and "S.forceGun" not in window:
            raise AssertionError(
                "HID must not publishAim unless DESKTOP or forceGun owns the mailbox"
            )
    if re.search(r"await\s+", hid):
        raise AssertionError("window HID awaits — shot never waits on a camera")
    chrome = _js_fn(src, "hidChromeTarget")
    if "button" not in chrome or "input" not in chrome:
        raise AssertionError("chrome spare must keep WARM UP / ENTER RANGE / join")
    if "join-mute" not in chrome or "lobby-join" not in chrome:
        raise AssertionError("chrome spare must release leftover JOIN/CODE after join")
    if "aimBus" in chrome or "fire(" in chrome:
        raise AssertionError("chrome spare must not gate the peek")
    mute = _js_fn(src, "muteJoinPad")
    if "join-mute" not in mute or "blur" not in mute:
        raise AssertionError("muteJoinPad must blur leftover CODE and drop join-mute")
    if "aimBus" in mute or "fire(" in mute:
        raise AssertionError("join-mute must not gate the peek")
    join = _js_fn(src, "lobbyJoin")
    if "muteJoinPad()" not in join:
        raise AssertionError("lobbyJoin must release leftover JOIN/CODE so the pad peeks")
    if join.find("muteJoinPad()") > join.find('setPhase("lobby")'):
        raise AssertionError("muteJoinPad must release leftover JOIN/CODE before setPhase Look")
    create = _js_fn(src, "lobbyCreate")
    leave = _js_fn(src, "lobbyLeave")
    if "clearJoinMute()" not in create or "clearJoinMute()" not in leave:
        raise AssertionError("create/leave must re-arm JOIN/CODE for the next session")
    hud = re.search(r"#hud\s*\{([^}]+)\}", css)
    if not hud or "pointer-events: none" not in hud.group(1):
        raise AssertionError("#hud must stay pointer-events none — window owns HID")
    if "join-mute" not in css or "#btn-lobby-join" not in css:
        raise AssertionError("leftover JOIN/CODE must be pointer-events none after join")


def _pct(samples: list[float], p: float) -> float:
    s = sorted(samples)
    if not s:
        return 0.0
    i = min(len(s) - 1, math.ceil(p * len(s)) - 1)
    return s[i]


def test_sableperf_budget() -> None:
    src = proto_js()
    if "const SablePerf" not in src:
        raise AssertionError("SablePerf probe must exist")
    if "budgetMs: 8" not in src:
        raise AssertionError("SablePerf must prove HID→hitscan under 8 ms")
    if "sableperf=1" not in src:
        raise AssertionError("SablePerf must be flag-gated, not a HUD")
    if "drawModeChip" in src[src.find("const SablePerf") : src.find("const SablePerf") + 800]:
        raise AssertionError("SablePerf must not paint a HUD")
    # p50/p99 on a series that stays under budget.
    samples = [0.4, 0.5, 0.6, 0.7, 0.8, 1.1, 1.2, 2.0, 3.1, 4.5]
    p50 = _pct(samples, 0.5)
    p99 = _pct(samples, 0.99)
    if p50 > p99:
        raise AssertionError("p50 must be <= p99")
    if p99 >= 8:
        raise AssertionError("fixture p99 must stay under the 8 ms bar")
    over = samples + [12.0]
    if _pct(over, 0.99) < 8:
        raise AssertionError("a 12 ms hit must fail the 8 ms p99 bar")


def main() -> int:
    try:
        test_python_mailbox()
        test_desktop_first_click_uv()
        test_desktop_mailbox_truth()
        test_desktop_confidence()
        test_client_does_not_wait()
        test_product_gun_mutes_hid_fire()
        test_forcegun_rearms_pad()
        test_hid_lives_on_window()
        test_sableperf_budget()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("hid fire contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
