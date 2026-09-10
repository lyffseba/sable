#!/usr/bin/env python3
"""Fail loud if the hand-future invent locks drift.

research/HAND_FUTURE.md is the architecture soT. AimSample stays five
fields. Product GUN is hands-only. Meta SAM-class is invent, not the
hot path. Reload stub must not invent mag. HID/DESKTOP/Space stay
labeled non-product fallbacks. PRODUCTION / aim_pipeline must not teach
Click-is-HID as the product shot — shark-fin peeks AimBus.
Chrome (proto/index.html boot/lock) must teach point + shark-fin,
not pad/pinch as product shoot.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402


def _fail(msg: str) -> None:
    raise AssertionError(f"SABLEQA FAIL: hand future — {msg}")


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"(?:async )?function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        _fail(f"missing function {name}")
    return m.group(0)


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# Box PRODUCT.md north star — fold verbatim into PRODUCT + TRACKING + HAND_FUTURE.
LOCK_NEEDLES = (
    "## North star (LOCKED)",
    "**Gesture-only control. Mouse-shooter precision. No mouse control.**",
    "Hands + Meta vision models must feel as precise as a mouse shooter — CS honesty, Beat Saber energy, zero mouse as input verb.",
    "## Core invent (LOCKED)",
    "**Hand-only. No mouse as product verb. Mouse-shooter precision.**",
    "Reinvent the mouse as a **hand system**: the camera + best vision models own aim, shoot, reload, and lift/pose.",
    "No mouse mesh as a shipping product art step (that Blender ask was Kruidenhof flat — out of SABLE scope).",
    "Vision-model stack: **Meta object-recognition vision models** for in-game hand tracking (Juan lock).",
    "Invent/spike path open — win latency + honesty on MacBook lid-cam Chromium.",
    "MediaPipe Hands-class may stay interim until Meta stack ships. No mouse ever.",
    "HID / trackpad / Space forceGun may remain **engineering fallbacks**, never the product story",
    "AimSample off-limits unless Juan unlocks",
    "Mouse Blender / `lyffseba/sable-mouse` SABLE art track — STOP",
    "Mouse-as-gun / mouse-cam aim — retired",
)


def test_locks_verbatim() -> None:
    future = _read("research/HAND_FUTURE.md")
    product = _read("research/PRODUCT.md")
    tracking = _read("research/TRACKING.md")
    for needle in LOCK_NEEDLES:
        if needle not in future:
            _fail(f"HAND_FUTURE.md lost box lock: {needle}")
        if needle not in product:
            _fail(f"PRODUCT.md lost box lock: {needle}")
        if needle not in tracking:
            _fail(f"TRACKING.md lost box lock: {needle}")
    if "research/HAND_FUTURE.md" not in product or "research/HAND_FUTURE.md" not in tracking:
        _fail("PRODUCT/TRACKING must point at HAND_FUTURE.md")
    for box_only in (
        "## Vision",
        "**Feel DNA:** Counter-Strike–class competitive shooter",
        "**Shoot energy:** Beat Saber",
        "**Look:** Fortnite-class bold readability",
        "**Ship target:** **web** — MacBook Pro + Chromium floor",
        "## Hand verb (see TRACKING.md)",
        "Primary playable surface = Chromium on MacBook Pro–class.",
    ):
        if box_only not in product:
            _fail(f"PRODUCT.md must keep box section: {box_only}")
    if "do not rewrite" not in product.lower() and "Invent spike" not in product:
        _fail("PRODUCT.md must keep an invent-spike appendix without rewriting box locks")
    if "#86" not in product or "do not block" not in product.lower():
        _fail("PRODUCT.md must not block on #86 shark-fin")
    if "Do not merge" not in product:
        _fail("PRODUCT.md must keep do not merge")
    for rel in ("research/PRODUCT.md", "research/TRACKING.md", "research/HAND_FUTURE.md"):
        text = _read(rel)
        if "chromium-macbook" not in text:
            _fail(f"{rel} must keep #89 surface chromium-macbook")
        if "aimbus-hand-gesture" not in text:
            _fail(f"{rel} must keep #89 verb aimbus-hand-gesture")
    port = _read("docs/port.md")
    if "chromium-macbook" not in port or "aimbus-hand-gesture" not in port:
        _fail("docs/port.md must keep #89 chromium-macbook / aimbus-hand-gesture")


def test_aimsample_five_fields() -> None:
    src = proto_js()
    sample = re.search(r"class AimSample \{[\s\S]*?\n\}", src)
    if not sample:
        _fail("AimSample class missing")
    fields = re.findall(r"this\.(\w+)", sample.group(0))
    if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
        _fail("AimSample must stay five fields — do not invent a sixth")
    hpp = _read("native/cv_input/include/sable/aim_sample.hpp")
    for name in ("uv_x", "uv_y", "valid", "lifted", "confidence", "t_hw"):
        if name not in hpp:
            _fail(f"native AimSample lost {name}")
    if "reload" in hpp.lower() or "gesture" in hpp.lower() or "mag" in hpp.lower():
        _fail("native AimSample grew a gesture / mag field")
    future = _read("research/HAND_FUTURE.md")
    if "AimSample { uv, valid, lifted, confidence, t_hw }" not in future:
        _fail("HAND_FUTURE.md must keep the five-field mailbox")


def test_vision_stack_honesty() -> None:
    future = _read("research/HAND_FUTURE.md")
    if "hand_landmarker_lite" not in future or "404" not in future:
        _fail("HAND_FUTURE.md must call out that lite .task is 404")
    if "float16/1" not in future or "7819105" not in future:
        _fail("HAND_FUTURE.md must keep the published full float16/1 bundle")
    if "SAM-class" not in future:
        _fail("HAND_FUTURE.md must name the SAM-class invent path")
    if "not game-ready" not in future.lower():
        _fail("HAND_FUTURE.md must say SAM-class is not the Chromium 60 Hz hot path")
    if "Detectron2" not in future or "real-time in the browser" not in future:
        _fail("HAND_FUTURE.md must refuse Detectron2 / full SAM as real-time in Chromium")
    if "A100" not in future or "91.2" not in future:
        _fail("HAND_FUTURE.md must keep official SAM 2 FPS as A100, not MacBook")
    if "second product" not in future:
        _fail("HAND_FUTURE.md must refuse a required local Meta bridge as web ship")
    if "Interim landmark FSM" not in future:
        _fail("HAND_FUTURE.md must label MediaPipe as interim vs Meta invent")
    if "product invent" not in future.lower():
        _fail("HAND_FUTURE.md must label Meta object recognition as product invent")
    if "SAM alone is shark-fin" not in future:
        _fail("HAND_FUTURE.md must refuse SAM-alone as shark-fin")
    if "hand-as-object" not in future:
        _fail("HAND_FUTURE.md must name hand-as-object mask")
    if "120 Hz" not in future and "120Hz" not in future:
        _fail("HAND_FUTURE.md must say SAM encode is not a 120 Hz gesture loop")
    if "next-sam" not in future or "WebSAM" not in future:
        _fail("HAND_FUTURE.md must name the Chromium ORT-web demos")
    if "Python/native" not in future:
        _fail("HAND_FUTURE.md must keep Detectron2 as Python/native, not the zip")
    if "Prefer pure web" not in future and "prefer pure web" not in future:
        _fail("HAND_FUTURE.md must prefer pure web over a local bridge")
    if "SAM2-tiny" not in future or "MobileSAM" not in future:
        _fail("HAND_FUTURE.md must name SAM2-tiny / MobileSAM as the invent cut")
    if "Sapiens" not in future or "YOLO" not in future:
        _fail("HAND_FUTURE.md must call out Sapiens/YOLO as not defaults")
    if "Sapiens2" not in future:
        _fail("HAND_FUTURE.md must name Sapiens2 as not a default")
    if "MediaPipe Tasks Vision Hand Landmarker" not in future:
        _fail("HAND_FUTURE.md must keep MediaPipe Tasks Vision as the ship default")
    if "Three.js WebGL" not in future or "Worker + careful delegate" not in future:
        _fail("HAND_FUTURE.md must lock Worker GPU vs Three.js WebGL conflict")
    if "self-host" not in future.lower() and "Self-host" not in future:
        _fail("HAND_FUTURE.md must pin self-host / CDN")
    if "micro-handpose" not in future:
        _fail("HAND_FUTURE.md must name the micro-handpose stretch")
    if "Not the invent default" not in future:
        _fail("HAND_FUTURE.md must keep micro-handpose off the invent default")
    if "Chrome 113" not in future:
        _fail("HAND_FUTURE.md must keep the Chrome 113+ floor for the stretch")
    if "author bench" not in future.lower():
        _fail("HAND_FUTURE.md must not treat micro-handpose ~2x as a SABLE bench")
    hands = _read("proto/hands.js")
    worker = _read("proto/hands_worker.js")
    if "hand_landmarker_lite" in hands or "hand_landmarker_lite" in worker:
        _fail("do not point proto at a non-existent lite .task")
    if "sapiens" in hands.lower() or "yolo" in hands.lower() or "sam2" in hands.lower():
        _fail("Sapiens/YOLO/SAM must not become the shipped default tracker")
    if "micro-handpose" in hands or "micro-handpose" in worker:
        _fail("micro-handpose must not land in proto before a MacBook Chromium bench")
    fire = _js_fn(proto_js(), "fire")
    if re.search(r"SAM|Sapiens|detectForVideo|createImageBitmap", fire):
        _fail("fire() must not wait on Meta/SAM/detect")
    tracking = _read("research/TRACKING.md")
    if "micro-handpose" not in tracking:
        _fail("TRACKING.md must name micro-handpose as stretch only")


def test_shark_fin_and_charger_plug_on_tip() -> None:
    src = proto_js()
    if "function sharkFin" not in src or "function maybeSharkFinFire" not in src:
        _fail("shark-fin (#86 on tip) must stay — do not regress the verb")
    if "function chargerPlug" not in src or "function maybeReloadGesture" not in src:
        _fail("charger-plug reload (#87 on tip) must stay — do not regress the verb")
    if "function chargerReload" in src or "function onReloadStub" in src:
        _fail("do not land a second reload stub beside #87 charger-plug")
    reload_fn = _js_fn(src, "maybeReloadGesture")
    if "fire()" in reload_fn or "publishAim" in reload_fn or "updateAim" in reload_fn:
        _fail("maybeReloadGesture must not fire or rewrite aim")
    frame = _js_fn(src, "frame")
    if frame.find("updateMode") > frame.find("maybeSharkFinFire"):
        _fail("shark-fin must run after updateMode")
    if "maybePinchFire" in frame or "function maybePinchFire" in src:
        _fail("pinch must not peek — maybePinchFire is retired")
    if "pinchHeld" in src:
        _fail("S.pinchHeld died with the pinch verb")
    if frame.find("maybeSharkFinFire") > frame.find("maybeReloadGesture"):
        _fail("shark-fin must run before reload — product shoot first")
    if frame.find("maybeReloadGesture") > frame.find("updateAim"):
        _fail("reload must run before updateAim")
    desk_else = re.search(r"else if \(S\.desktop\) \{([\s\S]*?)\n  \}", frame)
    if not desk_else:
        _fail("frame lost the !camReady DESKTOP path")
    if "maybeSharkFinFire" in desk_else.group(1) or "maybePinchFire" in desk_else.group(1):
        _fail("!camReady DESKTOP must not run product gestures")
    if "maybeReloadGesture" in desk_else.group(1):
        _fail("!camReady DESKTOP must not run charger-plug reload")
    fire = _js_fn(src, "fire")
    if "maybeReloadGesture" in fire:
        _fail("reload must not enter fire()")
    future = _read("research/HAND_FUTURE.md")
    if "#86" not in future or "#87" not in future:
        _fail("HAND_FUTURE.md must name #86 shark-fin and #87 charger-plug")
    if "on tip" not in future:
        _fail("HAND_FUTURE.md must say those verbs are on tip")


def test_product_gun_hid_deprecated() -> None:
    src = proto_js()
    if "function productGunHidFire" not in src:
        _fail("productGunHidFire missing")
    gate = _js_fn(src, "productGunHidFire")
    if "return false" not in gate:
        _fail("productGunHidFire must stay false — pad is not the GUN")
    if "fire()" in gate or "publishAim" in gate:
        _fail("productGunHidFire must not peek")
    hid = _js_fn(src, "onHidPointerDown")
    if "if (S.desktop || S.forceGun || productGunHidFire()) fire()" not in hid:
        _fail("range/lobby HID must gate fire on DESKTOP / forceGun / productGunHidFire")
    if "if (S.desktop || S.forceGun) publishAim(e.clientX, e.clientY)" not in hid:
        _fail("DESKTOP / forceGun HID must still publish click UV before fire()")
    if hid.find("publishAim") > hid.find("fire()"):
        _fail("DESKTOP / forceGun publishAim must land before any fire() peek")
    future = _read("research/HAND_FUTURE.md")
    if "productGunHidFire" not in future:
        _fail("HAND_FUTURE.md must name the HID-as-gun deprecation gate")
    tracking = _read("research/TRACKING.md")
    if "productGunHidFire" not in tracking:
        _fail("TRACKING.md must name productGunHidFire")


def test_liftshot_product_pivot() -> None:
    future = _read("research/HAND_FUTURE.md")
    if "Retire — mouse-gun product verb and mouse mesh prototype path" not in future:
        _fail("HAND_FUTURE.md must retire mouse-gun verb and mouse mesh prototype path")
    if "Do not generate, import, or prototype a mouse gun / mouse mesh" not in future:
        _fail("HAND_FUTURE.md must forbid a mouse mesh prototype path")
    if "Do not reopen a mouse mesh / sable-mouse prototype" not in future:
        _fail("HAND_FUTURE.md must keep sable-mouse prototype STOP")
    if "SAM-class" not in future or "hybrid" not in future.lower():
        _fail("HAND_FUTURE.md must keep Meta SAM-class hybrid honesty")
    if "do not block" not in future.lower() or "#86" not in future:
        _fail("HAND_FUTURE.md must not block on #86")
    if "AimSample locked" not in future:
        _fail("HAND_FUTURE.md must keep AimSample locked")
    product = _read("research/PRODUCT.md")
    if "AimSample locked" not in product:
        _fail("PRODUCT.md invent appendix must keep AimSample locked")
    tracking = _read("research/TRACKING.md")
    if "AimSample locked" not in tracking:
        _fail("TRACKING.md must keep AimSample locked")
    if "SAM-class" not in tracking:
        _fail("TRACKING.md must keep SAM-class hybrid pointer")


# Product-fantasy phrases the bible must not teach as the shoot verb.
_CLICK_IS_HID_FANTASY = (
    "click is hid",
    "the click is the shot",
    "click is always hid",
    "fire-is-hid mailbox",
)

# Chrome lies — boot/lock must not sell pad/pinch as product shoot.
_CHROME_FIRE_LIES = (
    "tap the pad to fire",
    "trackpad is the trigger",
    "pinch comes next",
)


def test_fallbacks_labeled_non_product() -> None:
    for rel in (
        "research/HAND_FUTURE.md",
        "research/PRODUCT.md",
        "research/TRACKING.md",
        "docs/PRODUCTION.md",
        "docs/aim_pipeline.md",
    ):
        text = _read(rel)
        if "never the product story" not in text and "never product story" not in text:
            _fail(f"{rel} must label HID/DESKTOP/Space as never the product story")
        if "non-product emergency" not in text and "engineering fallbacks" not in text:
            _fail(f"{rel} must label DESKTOP/HID as engineering fallbacks / non-product")
    future = _read("research/HAND_FUTURE.md")
    if "sable-mouse" not in future or "STOP" not in future:
        _fail("HAND_FUTURE.md must keep sable-mouse STOP")
    if "No mouse ever" not in future:
        _fail("HAND_FUTURE.md must keep no mouse ever")
    test_bible_product_shoot_is_shark_fin()


def test_bible_product_shoot_is_shark_fin() -> None:
    """PRODUCTION + aim_pipeline: shark-fin owns product shoot; click-is-HID is not the fantasy."""
    for rel in ("docs/PRODUCTION.md", "docs/aim_pipeline.md"):
        text = _read(rel)
        low = text.lower()
        for banned in _CLICK_IS_HID_FANTASY:
            if banned in low:
                _fail(
                    f"{rel} must not teach product-fantasy {banned!r} — "
                    "shark-fin owns product shoot; HID is non-product"
                )
        if re.search(r"^## Fire is HID\b", text, re.M):
            _fail(f"{rel} must not lead fire with 'Fire is HID' as the product story")
        if "shark-fin" not in low and "maybesharkfinfire" not in low:
            _fail(f"{rel} must name shark-fin / maybeSharkFinFire as product shoot")
        if "maybeSharkFinFire" not in text and "shark-fin" not in low:
            _fail(f"{rel} must name shark-fin or maybeSharkFinFire")
        if "product shoot" not in low and "product fire" not in low and "product peek" not in low:
            _fail(f"{rel} must name shark-fin as product shoot / product peek")
        if "aimbus" not in low:
            _fail(f"{rel} must name AimBus peek")
        if "peek" not in low:
            _fail(f"{rel} must keep AimBus peek")
        if (
            "no camera gate" not in low
            and "never wait for the next camera" not in low
            and "never waits on a camera" not in low
        ):
            _fail(f"{rel} must keep no camera gate / never wait on a camera frame")
        if "HID" not in text or "DESKTOP" not in text or "Space" not in text:
            _fail(f"{rel} must name HID / DESKTOP / Space as the non-product emergency")
        if "never the product story" not in text and "never product story" not in text:
            _fail(f"{rel} must label HID/DESKTOP/Space as never the product story")
        if "non-product emergency" not in text and "engineering fallbacks" not in text:
            _fail(f"{rel} must label HID/DESKTOP/Space non-product emergency")
        if "productGunHidFire" not in text:
            _fail(f"{rel} must keep the productGunHidFire bar")
    prod = _read("docs/PRODUCTION.md")
    if "HID click → peek" in prod or "→ click →" in prod:
        _fail("PRODUCTION.md must not sell HID click / click as the product shot")
    if "AimBus.fire()" not in prod:
        _fail("PRODUCTION.md must name AimBus.fire() as the product peek")
    pipe = _read("docs/aim_pipeline.md")
    if "HID click → hitscan" in pipe:
        _fail("aim_pipeline.md must not sell HID click as the <8ms product bar")
    if "< 8 ms" not in pipe and "<8 ms" not in pipe:
        _fail("aim_pipeline.md must keep the <8ms peek bar")
    if "sticky" not in pipe.lower():
        _fail("aim_pipeline.md must keep sticky lift")
    if "waiting" not in pipe.lower() or "yard" not in pipe.lower():
        _fail("aim_pipeline.md must keep waiting-Yard")
    test_chrome_product_shoot_is_shark_fin()


def _boot_lock_copy(html: str) -> str:
    """Player-facing boot + lock copy only (tag / lock-copy / safety)."""
    chunks: list[str] = []
    boot = re.search(r'id="screen-boot"[\s\S]*?id="screen-lock"', html)
    lock = re.search(r'id="screen-lock"[\s\S]*?id="screen-calib"', html)
    if not boot:
        _fail("proto/index.html lost screen-boot")
    if not lock:
        _fail("proto/index.html lost screen-lock")
    for block, name in ((boot.group(0), "boot"), (lock.group(0), "lock")):
        for cls in ("tag", "lock-copy", "safety"):
            for m in re.finditer(
                rf'<p class="{cls}">([\s\S]*?)</p>', block
            ):
                chunks.append(m.group(1))
        if name == "lock" and 'class="lock-copy"' not in block:
            _fail("lock screen lost .lock-copy")
        if name == "boot" and 'class="tag"' not in block:
            _fail("boot screen lost .tag")
        if block.count('class="safety"') < 1:
            _fail(f"{name} screen lost .safety")
    return "\n".join(chunks)


def test_chrome_product_shoot_is_shark_fin() -> None:
    """proto/index.html boot+lock: shark-fin owns product shoot; pad/pinch are not the story."""
    html = _read("proto/index.html")
    low = html.lower()
    for banned in _CHROME_FIRE_LIES:
        if banned in low:
            _fail(
                f"proto/index.html must not teach chrome-lie {banned!r} — "
                "shark-fin owns product shoot; pad/HID is non-product"
            )
    if re.search(r"pinch[\s\S]{0,40}to fire", html, re.I):
        _fail("proto/index.html must not teach pinch to fire")
    copy = _boot_lock_copy(html)
    copy_low = copy.lower()
    if "shark-fin" not in copy_low:
        _fail("boot/lock copy must name shark-fin as product shoot")
    if "thumb up" not in copy_low:
        _fail("boot/lock copy must teach shark-fin (thumb UP)")
    if "thumb parallel" not in copy_low:
        _fail("boot/lock copy must teach thumb parallel = SAFE")
    if "safe" not in copy_low:
        _fail("boot/lock copy must name thumb parallel as SAFE")
    if "point" not in copy_low:
        _fail("boot/lock copy must teach point")
    # Pad / HID may be omitted; if named, they must be non-product emergency.
    if re.search(r"\b(pad|trackpad|hid)\b", copy_low):
        if "non-product" not in copy_low and "emergency" not in copy_low:
            _fail(
                "boot/lock pad/HID must be omitted or labeled "
                "non-product emergency — never product shoot"
            )
    boot = re.search(r'id="screen-boot"[\s\S]*?id="screen-lock"', html)
    lock = re.search(r'id="screen-lock"[\s\S]*?id="screen-calib"', html)
    if not boot or not lock:
        _fail("proto/index.html lost screen-boot or screen-lock")
    for block, name in ((boot.group(0), "boot"), (lock.group(0), "lock")):
        if "shark-fin" not in block.lower():
            _fail(f"{name} copy must name shark-fin")
        if "thumb" not in block.lower():
            _fail(f"{name} copy must teach the thumb (UP / parallel)")


def test_no_mouse_art_invented() -> None:
    src = proto_js()
    if re.search(r"mouseMesh|sable[-_]?mouse|kruidenhof", src, re.I):
        _fail("proto invented mouse-gun art — sable-mouse track STOP")
    future = _read("research/HAND_FUTURE.md")
    if "Original IP" not in future:
        _fail("HAND_FUTURE.md must keep original IP")
    if "Yard" not in future or "Bay" not in future:
        _fail("HAND_FUTURE.md must keep Yard sole / Bay parked")


def main() -> int:
    try:
        test_locks_verbatim()
        test_aimsample_five_fields()
        test_vision_stack_honesty()
        test_shark_fin_and_charger_plug_on_tip()
        test_product_gun_hid_deprecated()
        test_liftshot_product_pivot()
        test_fallbacks_labeled_non_product()
        test_bible_product_shoot_is_shark_fin()
        test_chrome_product_shoot_is_shark_fin()
        test_no_mouse_art_invented()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("hand future invent ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
