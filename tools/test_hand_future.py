#!/usr/bin/env python3
"""Fail loud if the hand-future invent locks drift.

research/HAND_FUTURE.md is the architecture soT. AimSample stays five
fields. Product GUN is hands-only. Meta SAM-class is invent, not the
hot path. Reload stub must not invent mag. HID/DESKTOP/Space stay
labeled non-product fallbacks. PRODUCTION / aim_pipeline must not teach
Click-is-HID as the product shot — shark-fin peeks AimBus.
Chrome (proto/index.html boot/lock) must teach point + shark-fin
+ thumb-parallel SAFE + index+middle charger-plug reload / MAG refill,
not pad/pinch/Click-is-HID as shoot or reload. Calib chrome must teach
shark-fin (thumb UP) to capture — not Click-is-HID, not reload.
Proto file headers must not sell Trackpad / HID click fires as the
product shot — HID/trackpad is DESKTOP/forceGun only; shark-fin owns
the AimBus peek.
Root / proto README zip play path must not re-teach click-the-pad
(or pad-as-fire) as the shot — shark-fin fires; pad is menus /
DESKTOP emergency only.
Root README Requirements must not sell KeyT / "Desktop aim … still
works" as a first-class product capability. KeyT / DESKTOP is debug /
non-product (cam-deny / honesty fallback), not a ship SKU. Keys T
must match Trackpad honesty: debug / non-product — not the Q4 path.
Root / proto README must not re-sell Safari / Firefox as first-class
ship browsers. Ship floor is Chromium on MacBook Pro–class lid-cam.
PRODUCTION One sentence must not re-sell “laptop or TV” / TV as a
first-class ship surface. Floor is Chromium on MacBook Pro–class
lid-cam (hand + shark-fin AimBus). Player fantasy TV stays feel /
literacy — not a ship SKU. No Firefox/Safari SKU in that sentence.
Parked Bay specs (docs/modes.md Bay rules, docs/maps/bay.md) must not
re-sell “Fire is HID” / “Fire is always HID” / “Click fires” as the
Bay product verb — shark-fin AimBus peek owns Bay fire; HID/trackpad
is DESKTOP/forceGun emergency only (non-product). Bay stays parked.
docs/design.md must not re-sell “Click fires” / pad-strafe→click /
mouse-on-pad as the product gun — shark-fin AimBus peek owns the
shot against the latest AimSample; click/HID is DESKTOP emergency
only (non-product). Space stays Q4 forceGun escape if mentioned.
Lock chrome must not sell Gemini / AI HAND LOCK as product vision.
Lock stays SEEKING → Hands lock or Space / PLAY ANYWAY (Q4).
Proto server must not sell /api/gemini/lock or health.gemini.
Hands-class interim; Meta SAM-class invent; no Gemini product vision.
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

# Chrome lies — boot/lock must not sell pad/pinch/Click-is-HID as shoot or reload.
_CHROME_FIRE_LIES = (
    "tap the pad to fire",
    "tap the pad to reload",
    "trackpad is the trigger",
    "pinch comes next",
    "pinch to fire",
    "pinch to reload",
    "click to reload",
    "click-is-hid",
    "click is hid",
)

# Calib chrome lies — corners are shark-fin, not Click-is-HID.
_CHROME_CALIB_LIES = (
    "click to capture",
    "click to capture.",
    "click  to capture",
)

# Player-facing README Keys lies — shark-fin / AimBus peek owns the shot.
_README_KEYS_FIRE_LIES = (
    "fire is hid",
    "fire-is-hid",
    "fire stays hid-local",
    "fire stays hid local",
    "the shot does not: fire is hid",
)

# Proto file-header lies — HID click is DESKTOP/forceGun only.
_PROTO_HEADER_FIRE_LIES = (
    "trackpad / hid click fires",
    "hid click fires",
    "click fires from the aimbus",
    "click fires from the aimbus mailbox",
    "the click is the shot",
    "click is hid",
    "click-is-hid",
)

# Space row lies — Q4 forceGun escape is not a product lift verb.
_README_KEYS_SPACE_LIES = (
    "simulates physical lift",
    "simulate physical lift",
    "simulating physical lift",
    "physical lift",
    "product lift",
)

# Zip / Other-computer play-path lies — shark-fin owns the shot; pad is not fire.
_README_ZIP_PLAY_LIES = (
    "click the pad",
    "click-the-pad",
    "click the trackpad",
    "tap the pad",
    "tap the pad to fire",
    "point, click the pad",
)

# Requirements first-class DESKTOP / KeyT sell — debug / non-product only.
_README_REQ_DESKTOP_LIES = (
    "desktop aim (**t** key) still works",
    "desktop aim (t key) still works",
    "still works without a camera",
)

# Parked Bay spec lies — leftover HID/click as the Bay product verb.
_BAY_DOCS_FIRE_LIES = (
    r"\bfire is always hid\b",
    r"\bfire is hid\b",
    r"\bclick fires\b",
)

# design.md leftover click-as-product-fire — shark-fin AimBus peek owns the shot.
_DESIGN_MD_FIRE_LIES = (
    r"\bclick fires\b",
    r"→\s*\*{0,2}click\*{0,2}\s*→",
    r"pad-strafe\s*\(mouse on the pad",
    r"\bmouse on the pad\b",
)

# Requirements leftover multi-browser SKU — Chromium / MacBook is the floor.
_README_REQ_BROWSER_SKU_LIES = (
    "chrome, edge, safari, firefox",
    "modern web browser (chrome",
    "modern web browser",
)

# PRODUCTION One sentence leftover — Chromium / MacBook floor; no TV SKU.
_PRODUCTION_ONE_SENTENCE_SKU_LIES = (
    "laptop or tv",
    "laptop or a tv",
    "at a laptop or tv",
    "hand at a laptop or tv",
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
    test_readme_keys_shot_honesty()
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
    if re.search(r"pinch[\s\S]{0,40}to (fire|reload)", html, re.I):
        _fail("proto/index.html must not teach pinch to fire or reload")
    if re.search(r"click[\s\S]{0,40}to (fire|reload)", html, re.I):
        _fail("proto/index.html must not teach Click-is-HID as fire or reload")
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
                "non-product emergency — never product shoot or reload"
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
    test_chrome_reload_is_charger_plug()
    test_chrome_calib_capture_is_shark_fin()


def _chrome_teaches_reload(text: str) -> bool:
    """True when copy names the #87 charger-plug / index+middle MAG refill."""
    low = text.lower()
    has_fingers = "index+middle" in low or "index + middle" in low
    has_reload = "reload" in low or "mag refill" in low or "reloads mag" in low
    return has_fingers and has_reload


def test_chrome_reload_is_charger_plug() -> None:
    """proto/index.html boot+lock must name the same reload verb the code peeks."""
    html = _read("proto/index.html")
    copy = _boot_lock_copy(html)
    copy_low = copy.lower()
    if "charger-plug" not in copy_low and "charger plug" not in copy_low:
        _fail("boot/lock copy must name charger-plug as product reload")
    if "index+middle" not in copy_low and "index + middle" not in copy_low:
        _fail("boot/lock copy must teach index+middle ceiling reload")
    if "ceiling" not in copy_low:
        _fail("boot/lock copy must teach index+middle pointing up toward the ceiling")
    if "reload" not in copy_low:
        _fail("boot/lock copy must name reload")
    if "mag" not in copy_low:
        _fail("boot/lock copy must name MAG refill")
    if re.search(r"\b(pad|trackpad|hid|pinch|click)\b[\s\S]{0,40}reload", copy_low):
        _fail(
            "boot/lock must not sell pad/pinch/Click-is-HID as reload — "
            "charger-plug owns MAG refill"
        )
    boot = re.search(r'id="screen-boot"[\s\S]*?id="screen-lock"', html)
    lock = re.search(r'id="screen-lock"[\s\S]*?id="screen-calib"', html)
    if not boot or not lock:
        _fail("proto/index.html lost screen-boot or screen-lock")
    for block, name in ((boot.group(0), "boot"), (lock.group(0), "lock")):
        if not _chrome_teaches_reload(block):
            _fail(
                f"{name} chrome must teach index+middle reload / MAG refill — "
                "same verb maybeReloadGesture peeks"
            )
        if "charger-plug" not in block.lower() and "charger plug" not in block.lower():
            _fail(f"{name} chrome must name charger-plug")


def _calib_copy(html: str) -> str:
    """Player-facing calib instruction only (#calib-msg)."""
    calib = re.search(r'id="screen-calib"[\s\S]*?id="screen-lobby"', html)
    if not calib:
        _fail("proto/index.html lost screen-calib")
    block = calib.group(0)
    msg = re.search(r'id="calib-msg"[^>]*>([\s\S]*?)</p>', block)
    if not msg:
        _fail("calib screen lost #calib-msg")
    return msg.group(1)


def test_chrome_calib_capture_is_shark_fin() -> None:
    """Calib chrome + shark-fin path: captureCorner on the hand, not Click-is-HID."""
    html = _read("proto/index.html")
    src = proto_js()
    for banned in _CHROME_CALIB_LIES:
        if banned in html.lower():
            _fail(
                f"proto/index.html must not teach calib-lie {banned!r} — "
                "shark-fin (thumb UP) captures the glow; click is not product"
            )
    if "CLICK TO CAPTURE" in src or "Click to capture" in src:
        _fail(
            "updateCalibMsg / calib chrome must not paint CLICK TO CAPTURE "
            "as product capture — shark-fin owns the four corners"
        )
    copy = _calib_copy(html)
    copy_low = copy.lower()
    if "shark-fin" not in copy_low:
        _fail("#calib-msg must teach shark-fin to capture")
    if "thumb up" not in copy_low:
        _fail("#calib-msg must teach shark-fin (thumb UP) to capture")
    if "aim" not in copy_low and "glow" not in copy_low:
        _fail("#calib-msg must teach aim at the glow")
    if "reload" in copy_low or "charger-plug" in copy_low or "index+middle" in copy_low:
        _fail(
            "calib chrome must not teach reload — corners stay shark-fin capture"
        )
    if re.search(r"\bclick\b", copy_low):
        if "non-product" not in copy_low and "emergency" not in copy_low:
            _fail(
                "calib chrome must omit click or label it non-product "
                "emergency — never product capture"
            )
    msg = _js_fn(src, "updateCalibMsg")
    if "CLICK TO CAPTURE" in msg or "Click to capture" in msg:
        _fail("updateCalibMsg must not paint CLICK TO CAPTURE")
    if "SHARK-FIN" not in msg and "shark-fin" not in msg.lower():
        _fail("updateCalibMsg must teach shark-fin capture while corners remain")
    if "THUMB UP" not in msg and "thumb up" not in msg.lower():
        _fail("updateCalibMsg must teach thumb UP capture")
    if "TEST AIM" not in msg or "CENTER TARGET" not in msg:
        _fail("updateCalibMsg must keep the post-four-corners test-aim line")
    fin = _js_fn(src, "maybeSharkFinFire")
    if "S.finHeld" not in fin:
        _fail("calib shark-fin must keep rising-edge hygiene (finHeld)")
    if "captureCorner()" not in fin:
        _fail(
            "maybeSharkFinFire must invoke captureCorner on early calib — "
            "HID click is not the only corner path"
        )
    if 'phase === "calibrate"' not in fin or "S.calibIndex < 4" not in fin:
        _fail("early-calib shark-fin must gate captureCorner on calibrate + corners remain")
    if "captureCorner();return;" not in re.sub(r"\s+", "", fin):
        _fail(
            "early-calib shark-fin must captureCorner and return — "
            "do not spend mag / do not fire() the corner"
        )
    if "fire()" not in fin:
        _fail("shark-fin must still peek fire() after four corners / range")
    cap_line = None
    for line in fin.splitlines():
        if "captureCorner()" in line and "calibrate" in line:
            cap_line = line
            break
    if cap_line is None:
        for line in fin.splitlines():
            if "captureCorner()" in line:
                cap_line = line
                break
    if cap_line is None:
        _fail("maybeSharkFinFire lost the captureCorner line")
    if "fire()" in cap_line:
        _fail("captureCorner must not share a fire() call — corners are not shots")
    hid = _js_fn(src, "onHidPointerDown")
    if "captureCorner()" not in hid:
        _fail("HID click capture must stay as a non-product emergency fallback")
    if 'phase === "calibrate"' not in hid:
        _fail("HID emergency capture must still see phase calibrate")
    if "productGunHidFire" not in src:
        _fail("productGunHidFire bar must stay")
    gate = _js_fn(src, "productGunHidFire")
    if "return false" not in gate:
        _fail("productGunHidFire must stay false")


# Lock chrome lies — do not sell a missing Gemini API as product vision.
_CHROME_GEMINI_LOCK_LIES = (
    "ai hand lock",
    "btn-gemini-lock",
    "gemini 3.8",
    "gemini analyzing",
    "analyzing...",
)


def _readme_keys_block(md: str, label: str) -> str:
    """Keys heading through the next heading (table + footer)."""
    m = re.search(r"^#{2,3} Keys\s*\n[\s\S]*?(?=^#{1,3} |\Z)", md, re.MULTILINE)
    if not m:
        _fail(f"{label} lost the Keys section")
    return m.group(0)


def _keys_row_cells(line: str) -> tuple[str, str] | None:
    if not line.startswith("|"):
        return None
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) < 2:
        return None
    key, action = cells[0], cells[1]
    if set(key) <= set("-: ") or key.lower() in {"key", "what", "action"}:
        return None
    return key, action


def _keys_space_action(table: str, label: str) -> str:
    for line in table.splitlines():
        row = _keys_row_cells(line)
        if not row:
            continue
        if re.search(r"\bSpace\b", row[0], re.I):
            return row[1]
    _fail(f"{label} Keys table lost Space — Q4 forceGun escape")
    return ""


def _keys_footer(block: str) -> str:
    """Prose after the Keys table (root README shot-honesty line)."""
    after: list[str] = []
    seen_table = False
    in_table = False
    for line in block.splitlines():
        if line.startswith("|"):
            in_table = True
            seen_table = True
            continue
        if in_table and not line.startswith("|"):
            in_table = False
        if seen_table and not in_table:
            after.append(line)
    return "\n".join(after)


def _assert_readme_keys_shot_honest(block: str, label: str) -> None:
    """Keys table + footer: shark-fin / AimBus peek owns the shot; Space is Q4."""
    low = block.lower()
    for banned in _README_KEYS_FIRE_LIES:
        if banned in low:
            _fail(
                f"{label} Keys must not re-sell {banned!r} as the shot story — "
                "shark-fin / AimBus peek owns the shot"
            )
    space = _keys_space_action(block, label)
    space_low = space.lower()
    for banned in _README_KEYS_SPACE_LIES:
        if banned in space_low:
            _fail(
                f"{label} Space row must not sell {banned!r} — "
                "Space is Q4 forceGun escape, not a product lift"
            )
    if "q4" not in space_low:
        _fail(f"{label} Space row must name Q4 forceGun escape")
    if "forcegun" not in space_low and "force-gun" not in space_low and "force gun" not in space_low:
        _fail(f"{label} Space row must name forceGun")
    if "not a shot" not in space_low:
        _fail(f"{label} Space row must say Space is not a shot")
    if "escape" not in space_low:
        _fail(f"{label} Space row must name the Q4 escape")
    footer = _keys_footer(block)
    footer_low = footer.lower()
    for banned in _README_KEYS_FIRE_LIES:
        if banned in footer_low:
            _fail(
                f"{label} Keys footer must not re-sell {banned!r} as the shot story — "
                "shark-fin / AimBus peek owns the shot"
            )
    if label == "README.md":
        if "shark-fin" not in footer_low and "shark fin" not in footer_low:
            _fail("README.md Keys footer must name shark-fin as the shot owner")
        if "aimbus" not in footer_low:
            _fail("README.md Keys footer must name AimBus peek as the shot owner")
        if "peek" not in footer_low:
            _fail("README.md Keys footer must keep AimBus peek")
        if (
            "never gated" not in footer_low
            and "never waits" not in footer_low
            and "no camera gate" not in footer_low
        ):
            _fail("README.md Keys footer must keep never-gated-on-camera-frame honesty")


def test_readme_keys_shot_honesty() -> None:
    """README Keys: shark-fin / AimBus peek owns the shot; Space is Q4 forceGun."""
    lie = (
        "### Keys\n"
        "| Key | Action |\n"
        "|-----|--------|\n"
        "| **Space** | Force gun (simulates physical lift) |\n"
        "\n"
        "The shot does not: fire is HID against the mailbox, never gated on the next frame.\n"
    )
    try:
        _assert_readme_keys_shot_honest(lie, "fixture")
    except AssertionError:
        pass
    else:
        _fail("Keys shot-honesty gate missed fire-is-HID / Space-as-lift fixture")
    for rel in ("README.md", "proto/README.md"):
        text = _read(rel)
        _assert_readme_keys_shot_honest(_readme_keys_block(text, rel), rel)
    readme = _read("README.md")
    if re.search(r"fire stays hid[- ]local", readme, re.I):
        _fail(
            "README.md must not sell Fire stays HID-local as the product shot — "
            "peek is local; never waits on net or a camera frame"
        )
    if re.search(r"\bfire is hid\b", readme, re.I):
        _fail(
            "README.md must not sell fire is HID as the shot story — "
            "shark-fin / AimBus peek owns the shot"
        )
    if "Peek is local" not in readme and "peek is local" not in readme.lower():
        _fail("README.md stack must keep peek-is-local latency honesty")
    test_proto_headers_shot_honesty()
    test_readme_zip_play_honesty()
    test_readme_t_desktop_honesty()
    test_readme_ship_floor_honesty()
    test_production_one_sentence_ship_floor()
    test_bay_docs_shot_honesty()
    test_design_md_shot_honesty()


def _js_file_header(src: str, label: str) -> str:
    """Leading block comment — file header only, not body HID-local / SablePerf notes."""
    m = re.search(r"^/\*[\s\S]*?\*/", src)
    if not m:
        _fail(f"{label} lost its file header")
    return m.group(0)


def _assert_aim_house_header_shot_honest(header: str, label: str) -> None:
    """aim.js / house.js headers: shark-fin owns product peek; HID is DESKTOP/forceGun."""
    low = header.lower()
    for banned in _PROTO_HEADER_FIRE_LIES:
        if banned in low:
            _fail(
                f"{label} header must not re-sell {banned!r} as the product shot — "
                "HID click is DESKTOP/forceGun only; shark-fin owns product peek"
            )
    if "shark-fin" not in low and "shark fin" not in low:
        _fail(f"{label} header must name shark-fin as product peek")
    if "aimbus" not in low:
        _fail(f"{label} header must name AimBus peek")
    if "desktop" not in low:
        _fail(f"{label} header must label HID/trackpad DESKTOP/forceGun only")
    if "forcegun" not in low and "force-gun" not in low and "force gun" not in low:
        _fail(f"{label} header must label HID/trackpad DESKTOP/forceGun only")
    if (
        "never waits on camera" not in low
        and "never wait on camera" not in low
        and "never waits on a camera" not in low
    ):
        _fail(f"{label} header must keep never-waits-on-camera honesty")


def test_proto_headers_shot_honesty() -> None:
    """proto headers: HID click is DESKTOP/forceGun only; shark-fin owns product peek."""
    lie = (
        "/* SABLE — aim.js\n"
        "   Trackpad / HID click fires from the AimBus mailbox — never waits on camera. */"
    )
    try:
        _assert_aim_house_header_shot_honest(lie, "fixture")
    except AssertionError:
        pass
    else:
        _fail("proto header shot-honesty gate missed HID-click-fires fixture")
    for rel in ("proto/aim.js", "proto/house.js"):
        _assert_aim_house_header_shot_honest(_js_file_header(_read(rel), rel), rel)
    # Other proto/*.js headers: ban the product-shot lie only.
    # Do not police HID-local latency / SablePerf probe wording in the body.
    for path in sorted((ROOT / "proto").glob("*.js")):
        rel = str(path.relative_to(ROOT))
        header = _js_file_header(_read(rel), rel)
        low = header.lower()
        for banned in _PROTO_HEADER_FIRE_LIES:
            if banned in low:
                _fail(
                    f"{rel} header must not re-sell {banned!r} as the product shot — "
                    "HID click is DESKTOP/forceGun only; shark-fin owns product peek"
                )


def _readme_zip_play_block(md: str, label: str) -> str:
    """Other computer / Zip heading through the next heading (zip play path)."""
    m = re.search(
        r"^#{2,3} (?:Other computer|Zip(?: \(other computer\))?)\s*\n"
        r"[\s\S]*?(?=^#{1,3} |\Z)",
        md,
        re.MULTILINE,
    )
    if not m:
        _fail(f"{label} lost the Other computer / Zip play path")
    return m.group(0)


def _readme_play_block(md: str) -> str | None:
    """Optional Play heading (proto README play path)."""
    m = re.search(r"^#{2,3} Play\s*\n[\s\S]*?(?=^#{1,3} |\Z)", md, re.MULTILINE)
    return m.group(0) if m else None


def _assert_readme_zip_play_honest(block: str, label: str) -> None:
    """Zip / play path: shark-fin fires; pad is menus / DESKTOP — never click-the-pad."""
    low = block.lower()
    for banned in _README_ZIP_PLAY_LIES:
        if banned in low:
            _fail(
                f"{label} zip/play path must not re-teach {banned!r} as the shot — "
                "shark-fin fires; pad is menus / DESKTOP emergency only"
            )
    if re.search(r"\b(click|tap)\b.{0,32}\b(the )?(track)?pad\b", low):
        _fail(
            f"{label} zip/play path must not teach click/tap-the-pad as the shot — "
            "shark-fin fires; pad is menus / DESKTOP emergency only"
        )
    if re.search(r"\b(the )?(track)?pad\b.{0,40}\b(to )?(fire|shoot|shot|trigger)\b", low):
        _fail(
            f"{label} zip/play path must not teach pad-as-fire — "
            "shark-fin owns the shot; pad is menus / DESKTOP emergency only"
        )
    if "shark-fin" not in low and "shark fin" not in low:
        _fail(f"{label} zip/play path must name shark-fin as the shot")
    if re.search(r"\b(pad|trackpad)\b", low):
        if "menus" not in low and "desktop" not in low:
            _fail(
                f"{label} zip/play pad/trackpad must be menus / DESKTOP emergency — "
                "never the shot"
            )


def test_readme_zip_play_honesty() -> None:
    """README zip/play path: shark-fin fires; never click-the-pad as the shot."""
    lie = (
        "## Other computer\n"
        "\n"
        "Open http://127.0.0.1:8080 — allow camera, raise a hand, point, click the pad.\n"
    )
    try:
        _assert_readme_zip_play_honest(lie, "fixture")
    except AssertionError:
        pass
    else:
        _fail("zip/play honesty gate missed click-the-pad fixture")
    for rel in ("README.md", "proto/README.md"):
        text = _read(rel)
        _assert_readme_zip_play_honest(_readme_zip_play_block(text, rel), rel)
        play = _readme_play_block(text)
        if play is not None:
            _assert_readme_zip_play_honest(play, f"{rel} Play")
        low = text.lower()
        for banned in _README_ZIP_PLAY_LIES:
            if banned in low:
                _fail(
                    f"{rel} must not re-teach {banned!r} as the zip/play shot — "
                    "shark-fin fires; pad is menus / DESKTOP emergency only"
                )


def _readme_requirements_block(md: str, label: str) -> str:
    """Requirements heading through the next heading (player-facing ship list)."""
    m = re.search(r"^## Requirements\s*\n[\s\S]*?(?=^#{1,3} |\Z)", md, re.MULTILINE)
    if not m:
        _fail(f"{label} lost Requirements")
    return m.group(0)


def _keys_t_action(table: str, label: str) -> str:
    for line in table.splitlines():
        row = _keys_row_cells(line)
        if not row:
            continue
        key_plain = re.sub(r"[*`_]", "", row[0]).strip()
        key_u = key_plain.upper()
        if key_u == "T" or key_u.startswith("T "):
            return row[1]
    _fail(f"{label} Keys table lost T — desktop-aim debug")
    return ""


def _desktop_framed_non_product(text: str) -> bool:
    """True when copy labels KeyT / DESKTOP debug + non-product (not Q4)."""
    low = text.lower()
    has_debug = "debug" in low
    has_non_product = (
        "non-product" in low
        or "not q4" in low
        or "not the q4" in low
    )
    return has_debug and has_non_product


def _assert_readme_requirements_desktop_honest(block: str, label: str) -> None:
    """Requirements: do not sell KeyT / desktop aim as a first-class ship feature."""
    low = block.lower()
    for banned in _README_REQ_DESKTOP_LIES:
        if banned in low:
            _fail(
                f"{label} Requirements must not re-sell {banned!r} as a first-class "
                "product capability — KeyT / DESKTOP is debug / non-product "
                "(cam-deny / honesty fallback), not a ship feature"
            )
    if re.search(r"keyt|desktop[- ]aim|\*\*t\*\*\s*key|\bt\s+key\b", low):
        if not _desktop_framed_non_product(block):
            _fail(
                f"{label} Requirements must not sell KeyT / desktop aim as a ship "
                "feature — label debug / non-product or drop it from Requirements"
            )


def _assert_readme_keys_t_honest(block: str, label: str) -> None:
    """Keys T: debug / non-product — same honesty as the Trackpad row."""
    t_low = _keys_t_action(block, label).lower()
    if "debug" not in t_low:
        _fail(f"{label} T row must label desktop-aim debug — not a Q4 product path")
    if (
        "non-product" not in t_low
        and "not q4" not in t_low
        and "not the q4" not in t_low
    ):
        _fail(
            f"{label} T row must match Trackpad honesty — non-product / not Q4"
        )
    if "still works" in t_low:
        _fail(
            f"{label} T row must not sell desktop-aim as a first-class capability"
        )


def test_readme_t_desktop_honesty() -> None:
    """README: KeyT / DESKTOP is debug / non-product — not a Requirements ship SKU."""
    req_lie = (
        "## Requirements\n"
        "\n"
        "- Built-in laptop webcam is enough. "
        "Desktop aim (**T** key) still works without a camera.\n"
    )
    try:
        _assert_readme_requirements_desktop_honest(req_lie, "fixture")
    except AssertionError:
        pass
    else:
        _fail(
            "Requirements T-honesty gate missed first-class "
            "Desktop-aim-still-works fixture"
        )
    req_unframed = (
        "## Requirements\n"
        "\n"
        "- Built-in laptop webcam is enough. Desktop aim (**T** key) is available.\n"
    )
    try:
        _assert_readme_requirements_desktop_honest(req_unframed, "fixture")
    except AssertionError:
        pass
    else:
        _fail(
            "Requirements T-honesty gate missed unframed Desktop-aim mention"
        )
    req_ok = (
        "## Requirements\n"
        "\n"
        "- Built-in laptop webcam is enough. "
        "KeyT / DESKTOP is debug / non-product (cam-deny / honesty fallback).\n"
    )
    _assert_readme_requirements_desktop_honest(req_ok, "framed-fixture")
    keys_lie = (
        "### Keys\n"
        "| Key | Action |\n"
        "|-----|--------|\n"
        "| **T** | Desktop aim toggle (OS cursor fallback) |\n"
    )
    try:
        _assert_readme_keys_t_honest(keys_lie, "fixture")
    except AssertionError:
        pass
    else:
        _fail("Keys T-honesty gate missed first-class Desktop-aim-toggle fixture")
    readme = _read("README.md")
    _assert_readme_requirements_desktop_honest(
        _readme_requirements_block(readme, "README.md"), "README.md"
    )
    for rel in ("README.md", "proto/README.md"):
        text = _read(rel)
        _assert_readme_keys_t_honest(_readme_keys_block(text, rel), rel)


def _safari_firefox_framed_non_floor(text: str) -> bool:
    """True when Safari/Firefox are labeled stretch / non-floor, not ship browsers."""
    low = text.lower()
    return (
        "non-floor" in low
        or "not the floor" in low
        or "not first-class" in low
        or "not a first-class" in low
        or "stretch" in low
        or "not the ship" in low
    )


def _assert_readme_requirements_ship_floor(block: str, label: str) -> None:
    """Requirements: Chromium / MacBook floor — no Safari/Firefox SKU."""
    low = block.lower()
    if "chromium" not in low:
        _fail(f"{label} Requirements must name Chromium as the ship floor")
    if "macbook" not in low:
        _fail(f"{label} Requirements must name MacBook Pro–class as the ship floor")
    for banned in _README_REQ_BROWSER_SKU_LIES:
        if banned in low:
            _fail(
                f"{label} Requirements must not re-sell {banned!r} as a first-class "
                "ship browser SKU — floor is Chromium on MacBook Pro–class lid-cam"
            )
    if re.search(r"\bsafari\b|\bfirefox\b", low):
        if not _safari_firefox_framed_non_floor(block):
            _fail(
                f"{label} Requirements must not list Safari/Firefox as first-class "
                "ship browsers — label non-floor / stretch or name the Chromium / "
                "MacBook floor only"
            )


def _assert_proto_readme_ship_floor(text: str, label: str) -> None:
    """Proto lede: Chromium / MacBook floor — not a Safari/Firefox SKU."""
    low = text.lower()
    if "chromium" not in low:
        _fail(f"{label} must name Chromium as the ship floor")
    if "macbook" not in low:
        _fail(f"{label} must name MacBook Pro–class as the ship floor")
    if re.search(r"\bsafari\b|\bfirefox\b", low):
        if not _safari_firefox_framed_non_floor(text):
            _fail(
                f"{label} must not list Safari/Firefox as first-class ship browsers"
            )
    if re.search(r"^chrome range\b", low, re.M):
        _fail(
            f"{label} must not sell Chrome-range as the floor without MacBook — "
            "name Chromium on MacBook Pro–class lid-cam"
        )


def test_readme_ship_floor_honesty() -> None:
    """README: ship floor is Chromium / MacBook — no Firefox/Safari SKU."""
    req_lie = (
        "## Requirements\n"
        "\n"
        "- Modern web browser (Chrome, Edge, Safari, Firefox).\n"
    )
    try:
        _assert_readme_requirements_ship_floor(req_lie, "fixture")
    except AssertionError:
        pass
    else:
        _fail(
            "Requirements ship-floor gate missed first-class "
            "Chrome/Edge/Safari/Firefox SKU fixture"
        )
    req_unframed = (
        "## Requirements\n"
        "\n"
        "- Chromium on a MacBook Pro–class lid camera. Also Safari and Firefox.\n"
    )
    try:
        _assert_readme_requirements_ship_floor(req_unframed, "fixture")
    except AssertionError:
        pass
    else:
        _fail(
            "Requirements ship-floor gate missed unframed Safari/Firefox mention"
        )
    req_no_floor = (
        "## Requirements\n"
        "\n"
        "- Chrome.\n"
    )
    try:
        _assert_readme_requirements_ship_floor(req_no_floor, "fixture")
    except AssertionError:
        pass
    else:
        _fail("Requirements ship-floor gate missed Chrome-only (no Chromium/MacBook)")
    req_floor_plus_sku = (
        "## Requirements\n"
        "\n"
        "- Chromium on a MacBook Pro–class lid camera (ship floor).\n"
        "- Modern web browser (Chrome, Edge, Safari, Firefox).\n"
    )
    try:
        _assert_readme_requirements_ship_floor(req_floor_plus_sku, "fixture")
    except AssertionError:
        pass
    else:
        _fail(
            "Requirements ship-floor gate missed leftover Safari/Firefox SKU "
            "beside a Chromium/MacBook line"
        )
    req_ok = (
        "## Requirements\n"
        "\n"
        "- Chromium on a MacBook Pro–class lid camera (ship floor).\n"
    )
    _assert_readme_requirements_ship_floor(req_ok, "framed-fixture")
    req_stretch = (
        "## Requirements\n"
        "\n"
        "- Chromium on a MacBook Pro–class lid camera (ship floor). "
        "Safari/Firefox are non-floor stretch.\n"
    )
    _assert_readme_requirements_ship_floor(req_stretch, "stretch-fixture")
    proto_lie = "Chrome range. Webcam tracks the hand.\n"
    try:
        _assert_proto_readme_ship_floor(proto_lie, "fixture")
    except AssertionError:
        pass
    else:
        _fail("proto README ship-floor gate missed Chrome-range leftover")
    readme = _read("README.md")
    _assert_readme_requirements_ship_floor(
        _readme_requirements_block(readme, "README.md"), "README.md"
    )
    _assert_proto_readme_ship_floor(_read("proto/README.md"), "proto/README.md")


def _production_one_sentence(md: str, label: str = "docs/PRODUCTION.md") -> str:
    """One sentence heading through the next heading (product claim)."""
    m = re.search(r"^## One sentence\s*\n[\s\S]*?(?=^## |\Z)", md, re.MULTILINE)
    if not m:
        _fail(f"{label} lost ## One sentence")
    return m.group(0)


def _production_player_fantasy(md: str, label: str = "docs/PRODUCTION.md") -> str:
    """Player fantasy heading through the next heading (feel / literacy)."""
    m = re.search(
        r"^## Player fantasy[^\n]*\n[\s\S]*?(?=^## |\Z)", md, re.MULTILINE
    )
    if not m:
        _fail(f"{label} lost ## Player fantasy")
    return m.group(0)


def _tv_framed_feel_or_stretch(text: str) -> bool:
    """True when TV is feel / literacy or later stretch, not a ship SKU."""
    low = text.lower()
    return (
        "feeling" in low
        or "feel / literacy" in low
        or "feel/literacy" in low
        or "feel-only" in low
        or "not a ship" in low
        or "not the ship" in low
        or "later stretch" in low
        or "not a second product" in low
        or "not a first-class" in low
        or "not first-class" in low
    )


def _assert_production_one_sentence_ship_floor(block: str, label: str) -> None:
    """PRODUCTION One sentence: Chromium / MacBook floor — no laptop-or-TV SKU."""
    low = block.lower()
    if "chromium" not in low:
        _fail(f"{label} One sentence must name Chromium as the ship floor")
    if "macbook" not in low:
        _fail(f"{label} One sentence must name MacBook Pro–class as the ship floor")
    for banned in _PRODUCTION_ONE_SENTENCE_SKU_LIES:
        if banned in low:
            _fail(
                f"{label} One sentence must not re-sell {banned!r} as a first-class "
                "ship surface — floor is Chromium on MacBook Pro–class lid-cam"
            )
    if re.search(r"\bfirefox\b|\bsafari\b", low):
        _fail(
            f"{label} One sentence must not invent Firefox/Safari as ship SKUs — "
            "floor is Chromium on MacBook Pro–class lid-cam"
        )
    if re.search(r"\btv\b", low):
        if not _tv_framed_feel_or_stretch(block):
            _fail(
                f"{label} One sentence must not sell TV as a first-class ship "
                "surface — label feel / literacy or later stretch, or name the "
                "Chromium / MacBook floor only"
            )


def test_production_one_sentence_ship_floor() -> None:
    """PRODUCTION One sentence: Chromium / MacBook floor — no TV SKU."""
    leftover = (
        "## One sentence\n"
        "\n"
        "You raise a hand at a laptop or TV, the house throws plates, "
        "shark-fin peeks AimBus — and friends can stand in the same house.\n"
    )
    try:
        _assert_production_one_sentence_ship_floor(leftover, "fixture")
    except AssertionError:
        pass
    else:
        _fail(
            "PRODUCTION One sentence ship-floor gate missed leftover "
            "laptop-or-TV SKU fixture"
        )
    unframed_tv = (
        "## One sentence\n"
        "\n"
        "You raise a hand at Chromium on a MacBook Pro–class lid camera "
        "or a TV, the house throws plates, shark-fin peeks AimBus.\n"
    )
    try:
        _assert_production_one_sentence_ship_floor(unframed_tv, "fixture")
    except AssertionError:
        pass
    else:
        _fail(
            "PRODUCTION One sentence ship-floor gate missed unframed TV "
            "beside a Chromium/MacBook line"
        )
    no_floor = (
        "## One sentence\n"
        "\n"
        "You raise a hand, the house throws plates, shark-fin peeks AimBus.\n"
    )
    try:
        _assert_production_one_sentence_ship_floor(no_floor, "fixture")
    except AssertionError:
        pass
    else:
        _fail(
            "PRODUCTION One sentence ship-floor gate missed missing "
            "Chromium/MacBook floor"
        )
    firefox_sku = (
        "## One sentence\n"
        "\n"
        "You raise a hand at Chromium or Firefox on a MacBook Pro–class "
        "lid camera, the house throws plates, shark-fin peeks AimBus.\n"
    )
    try:
        _assert_production_one_sentence_ship_floor(firefox_sku, "fixture")
    except AssertionError:
        pass
    else:
        _fail(
            "PRODUCTION One sentence ship-floor gate missed Firefox SKU fixture"
        )
    floor_plus_tv = (
        "## One sentence\n"
        "\n"
        "You raise a hand at Chromium on a MacBook Pro–class lid camera "
        "or a laptop or TV, the house throws plates, shark-fin peeks AimBus.\n"
    )
    try:
        _assert_production_one_sentence_ship_floor(floor_plus_tv, "fixture")
    except AssertionError:
        pass
    else:
        _fail(
            "PRODUCTION One sentence ship-floor gate missed leftover "
            "laptop-or-TV SKU beside a Chromium/MacBook line"
        )
    ok = (
        "## One sentence\n"
        "\n"
        "You raise a hand at Chromium on a MacBook Pro–class lid camera, "
        "the house throws plates, shark-fin peeks AimBus — and friends "
        "can stand in the same house.\n"
    )
    _assert_production_one_sentence_ship_floor(ok, "framed-fixture")
    bible = _read("docs/PRODUCTION.md")
    _assert_production_one_sentence_ship_floor(
        _production_one_sentence(bible), "docs/PRODUCTION.md"
    )
    if "laptop or tv" in bible.lower() or "laptop or a tv" in bible.lower():
        _fail(
            "docs/PRODUCTION.md must not re-sell laptop-or-TV as a first-class "
            "ship surface — floor is Chromium on MacBook Pro–class lid-cam"
        )
    fantasy = _production_player_fantasy(bible)
    if re.search(r"\btv\b", fantasy, re.I):
        if not _tv_framed_feel_or_stretch(fantasy):
            _fail(
                "PRODUCTION Player fantasy TV must stay feel / literacy — "
                "not a ship SKU / not Requirements"
            )


def _modes_bay_rules(md: str) -> str:
    """Bay rules heading through the next heading (parked booth spec)."""
    m = re.search(r"^## Bay rules[^\n]*\n[\s\S]*?(?=^## |\Z)", md, re.MULTILINE)
    if not m:
        _fail("docs/modes.md lost Bay rules")
    return m.group(0)


def _bay_md_section(md: str, heading: str) -> str:
    m = re.search(
        rf"^## {re.escape(heading)}\s*\n[\s\S]*?(?=^## |\Z)",
        md,
        re.MULTILINE,
    )
    if not m:
        _fail(f"docs/maps/bay.md lost ## {heading}")
    return m.group(0)


def _assert_no_bay_fire_lies(text: str, label: str) -> None:
    """Leftover HID/click product-verb phrasing must not return."""
    low = text.lower()
    for pat in _BAY_DOCS_FIRE_LIES:
        if re.search(pat, low):
            _fail(
                f"{label} must not re-sell leftover {pat!r} as the Bay product "
                "verb — shark-fin AimBus peek owns Bay fire; HID is DESKTOP/"
                "forceGun emergency only"
            )


def _assert_bay_rules_shot_honest(block: str, label: str) -> None:
    """modes.md Bay rules: shark-fin AimBus peek; HID emergency only; parked."""
    _assert_no_bay_fire_lies(block, label)
    low = block.lower()
    if "parked" not in low:
        _fail(f"{label} must keep Bay parked — do not unpark the booth")
    if "shark-fin" not in low and "shark fin" not in low:
        _fail(f"{label} must name shark-fin as the Bay product shoot")
    if "aimbus" not in low:
        _fail(f"{label} must name AimBus peek as the Bay product shoot")
    if "peek" not in low:
        _fail(f"{label} must keep AimBus peek")
    if "fire()" not in block and "firebay3d" not in low:
        _fail(f"{label} must keep fire() / fireBay3D as the peek path")
    if "desktop" not in low:
        _fail(f"{label} must label HID/trackpad DESKTOP/forceGun emergency only")
    if "forcegun" not in low and "force-gun" not in low and "force gun" not in low:
        _fail(f"{label} must label HID/trackpad DESKTOP/forceGun emergency only")
    if "emergency" not in low and "non-product" not in low:
        _fail(f"{label} must label HID/trackpad non-product emergency")
    if "enter bay" in low and "off" not in low and "not" not in low:
        _fail(f"{label} must not resurrect ENTER BAY as a player path")


def _assert_bay_run_keys_honest(block: str, label: str) -> None:
    """bay.md Run: shark-fin owns the shot; keys are parked/engineering."""
    _assert_no_bay_fire_lies(block, label)
    low = block.lower()
    if "shark-fin" not in low and "shark fin" not in low:
        _fail(f"{label} Run must name shark-fin as the shot owner")
    if "aimsample" not in low:
        _fail(f"{label} Run must keep the shot against the latest AimSample")
    if "desktop" not in low or "emergency" not in low:
        _fail(f"{label} Run must label click/HID DESKTOP emergency only")
    if "non-product" not in low:
        _fail(f"{label} Run must label click/HID / T non-product")
    if re.search(r"\*\*t\*\*", block, re.I) or re.search(r"\bt\b.{0,24}desktop", low):
        if "debug" not in low:
            _fail(f"{label} T must stay hidden debug — not player chrome")
        if "hidden" not in low:
            _fail(f"{label} T must stay hidden debug / non-product desktop-aim")
    if re.search(r"\*\*space\*\*", block, re.I) or re.search(r"\bspace\b", low):
        if "q4" not in low:
            _fail(f"{label} Space must stay Q4 forceGun escape")
        if "forcegun" not in low and "force-gun" not in low and "force gun" not in low:
            _fail(f"{label} Space must name forceGun")
        if "not a shot" not in low:
            _fail(f"{label} Space must say Space is not a shot")
    if re.search(r"\bwasd\b", low) or re.search(r"\*\*l\*\*", block, re.I):
        if "parked" not in low and "engineering" not in low:
            _fail(
                f"{label} WASD/L must stay parked/engineering — never player chrome"
            )
    if re.search(r"\bf5\b|\bf6\b", low):
        if "spec" not in low and "engineering" not in low:
            _fail(
                f"{label} Godot F5/F6 must stay engineering/spec — not product zip play"
            )
    if re.search(r"enter bay|boot\s+\*{0,2}bay\*{0,2}", low):
        if "spec" not in low and "parked" not in low and "not" not in low:
            _fail(f"{label} must not resurrect boot BAY / ENTER BAY as player paths")


def _assert_bay_combat_shot_honest(block: str, label: str) -> None:
    """bay.md Combat: shark-fin owns the shot; click/HID is DESKTOP emergency."""
    _assert_no_bay_fire_lies(block, label)
    low = block.lower()
    if "shark-fin" not in low and "shark fin" not in low:
        _fail(f"{label} Combat must name shark-fin as the shot owner")
    if "aimsample" not in low:
        _fail(f"{label} Combat must keep the shot against the latest AimSample")
    if "aimbus" not in low:
        _fail(f"{label} Combat must name AimBus peek")
    if "desktop" not in low or "emergency" not in low:
        _fail(f"{label} Combat must label click/HID DESKTOP emergency only")
    if "non-product" not in low:
        _fail(f"{label} Combat must label click/HID non-product")


def test_bay_docs_shot_honesty() -> None:
    """Parked Bay specs: shark-fin owns fire; leftover HID/click phrasing fails."""
    modes_lie = (
        "## Bay rules (parked 1v1 booth)\n"
        "\n"
        "Parked. Not playable from boot or the waiting arena.\n"
        "\n"
        "- Fire is HID (`fire()` → `fireBay3D`). Stamps `Bay.fireMs`.\n"
    )
    try:
        _assert_bay_rules_shot_honest(modes_lie, "fixture")
    except AssertionError:
        pass
    else:
        _fail("Bay rules shot-honesty gate missed Fire-is-HID leftover fixture")
    bay_run_lie = (
        "## Run\n"
        "\n"
        "**T** desktop aim. **Space** force gun (`AimSample.lifted`). "
        "**WASD** only while PAD. **L** cycles locker style. "
        "Click fires the latest `AimSample`.\n"
    )
    try:
        _assert_bay_run_keys_honest(bay_run_lie, "fixture")
    except AssertionError:
        pass
    else:
        _fail("Bay Run shot-honesty gate missed Click-fires leftover fixture")
    bay_combat_lie = (
        "## Combat verb\n"
        "\n"
        "Physical ADS is the gun. Fire is always HID against the latest "
        "`AimSample`. Do not wait for a camera frame.\n"
    )
    try:
        _assert_bay_combat_shot_honest(bay_combat_lie, "fixture")
    except AssertionError:
        pass
    else:
        _fail("Bay Combat shot-honesty gate missed Fire-is-always-HID leftover fixture")
    modes = _read("docs/modes.md")
    _assert_bay_rules_shot_honest(_modes_bay_rules(modes), "docs/modes.md Bay rules")
    bay = _read("docs/maps/bay.md")
    if "**Parked.**" not in bay and "**Parked**" not in bay:
        _fail("docs/maps/bay.md must keep the Parked banner")
    if "sole active" not in bay.lower():
        _fail("docs/maps/bay.md must keep Yard as the sole active map")
    if "does not offer" not in bay.lower() and "player chrome does not" not in bay.lower():
        _fail("docs/maps/bay.md must keep boot BAY / ENTER BAY off player chrome")
    _assert_no_bay_fire_lies(bay, "docs/maps/bay.md")
    _assert_bay_run_keys_honest(_bay_md_section(bay, "Run"), "docs/maps/bay.md")
    _assert_bay_combat_shot_honest(_bay_md_section(bay, "Combat verb"), "docs/maps/bay.md")


def _design_md_section(md: str, heading: str) -> str:
    m = re.search(
        rf"^## {re.escape(heading)}\s*\n[\s\S]*?(?=^## |\Z)",
        md,
        re.MULTILINE,
    )
    if not m:
        _fail(f"docs/design.md lost ## {heading}")
    return m.group(0)


def _assert_no_design_md_fire_lies(text: str, label: str) -> None:
    """Leftover click / pad-strafe-as-gun phrasing must not return."""
    low = text.lower()
    for pat in _DESIGN_MD_FIRE_LIES:
        if re.search(pat, low):
            _fail(
                f"{label} must not re-sell leftover {pat!r} as the product "
                "gun — shark-fin AimBus peek owns the shot; click/HID is "
                "DESKTOP emergency only (non-product)"
            )


def _assert_design_md_click_framed(block: str, label: str) -> None:
    """Bare click as product fire is a lie; DESKTOP emergency is honesty."""
    low = block.lower()
    if re.search(r"\bclick\b", low):
        if "desktop" not in low or "emergency" not in low:
            _fail(
                f"{label} must not sell bare click-as-product-fire — "
                "label click/HID DESKTOP emergency only, or drop click"
            )
        if "non-product" not in low:
            _fail(
                f"{label} must label click/HID non-product — "
                "never the product gun"
            )


def _assert_design_md_pad_not_gun(block: str, label: str) -> None:
    """Pad-strafe / mouse-on-pad must not read as the product gun."""
    low = block.lower()
    if re.search(r"pad-strafe|mouse-on-pad|mouse on the pad", low):
        if "not the product gun" not in low and "not the product" not in low:
            _fail(
                f"{label} pad-strafe / mouse-on-pad must not read as the "
                "product gun — say it is not, or drop it from the loop"
            )


def _assert_design_md_space_q4(block: str, label: str) -> None:
    """Space stays Q4 forceGun escape if mentioned — not a shot."""
    low = block.lower()
    if not re.search(r"\bspace\b", low):
        return
    if "q4" not in low:
        _fail(f"{label} Space must stay Q4 forceGun escape")
    if "forcegun" not in low and "force-gun" not in low and "force gun" not in low:
        _fail(f"{label} Space must name forceGun")
    if "not a shot" not in low:
        _fail(f"{label} Space must say Space is not a shot")


def _assert_design_md_loop_shot_honest(block: str, label: str) -> None:
    """design.md 30-second loop: shark-fin AimBus peek owns the shot."""
    _assert_no_design_md_fire_lies(block, label)
    _assert_design_md_click_framed(block, label)
    _assert_design_md_pad_not_gun(block, label)
    _assert_design_md_space_q4(block, label)
    low = block.lower()
    if "shark-fin" not in low and "shark fin" not in low:
        _fail(f"{label} must name shark-fin as the product shot")
    if "aimsample" not in low:
        _fail(f"{label} must keep the shot against the latest AimSample")
    if "latest" not in low:
        _fail(f"{label} must keep the latest AimSample")
    if "aimbus" not in low:
        _fail(f"{label} must name AimBus peek")
    if "peek" not in low:
        _fail(f"{label} must keep AimBus peek")
    if "desktop" not in low or "emergency" not in low:
        _fail(f"{label} must label click/HID DESKTOP emergency only")
    if "non-product" not in low:
        _fail(f"{label} must label click/HID non-product")


def _assert_design_md_gallery_shot_honest(block: str, label: str) -> None:
    """design.md Salt House: shark-fin owns fire against the latest sample."""
    _assert_no_design_md_fire_lies(block, label)
    _assert_design_md_click_framed(block, label)
    _assert_design_md_pad_not_gun(block, label)
    _assert_design_md_space_q4(block, label)
    low = block.lower()
    if "shark-fin" not in low and "shark fin" not in low:
        _fail(f"{label} must name shark-fin as the Salt House shot")
    if "aimsample" not in low and "latest" not in low:
        _fail(f"{label} must keep the shot against the latest AimSample")
    if "latest" not in low:
        _fail(f"{label} must keep the latest sample")
    if "aimbus" not in low:
        _fail(f"{label} must name AimBus peek")
    if "peek" not in low:
        _fail(f"{label} must keep AimBus peek")
    if "desktop" not in low or "emergency" not in low:
        _fail(f"{label} must label click/HID DESKTOP emergency only")
    if "non-product" not in low:
        _fail(f"{label} must label click/HID non-product")


def test_design_md_shot_honesty() -> None:
    """docs/design.md: shark-fin owns fire; leftover click / pad-strafe fails."""
    loop_lie = (
        "## 30-second loop\n"
        "\n"
        "Pad-strafe (mouse on the pad, later) → **lift** → point at the "
        "monitor → **click** → drop back to the pad. Physical ADS is the verb.\n"
    )
    try:
        _assert_design_md_loop_shot_honest(loop_lie, "fixture")
    except AssertionError:
        pass
    else:
        _fail("design.md loop gate missed pad-strafe→click leftover fixture")
    gallery_lie = (
        "## Gallery (now)\n"
        "\n"
        "Crosshair follows `AimSample.uv`. Click fires the **latest** sample.\n"
    )
    try:
        _assert_design_md_gallery_shot_honest(gallery_lie, "fixture")
    except AssertionError:
        pass
    else:
        _fail("design.md Gallery gate missed Click-fires leftover fixture")
    bare_click = (
        "## 30-second loop\n"
        "\n"
        "Lift → point → click → drop. Physical ADS is the verb.\n"
    )
    try:
        _assert_design_md_loop_shot_honest(bare_click, "fixture")
    except AssertionError:
        pass
    else:
        _fail("design.md loop gate missed bare click-as-product-fire fixture")
    design = _read("docs/design.md")
    _assert_no_design_md_fire_lies(design, "docs/design.md")
    _assert_design_md_loop_shot_honest(
        _design_md_section(design, "30-second loop"), "docs/design.md"
    )
    _assert_design_md_gallery_shot_honest(
        _design_md_section(design, "Gallery (now)"), "docs/design.md"
    )
    low = design.lower()
    if "parked" not in low:
        _fail("docs/design.md must keep Bay parked — do not unpark the booth")
    if re.search(r"\b(firefox|safari)\b", low):
        _fail("docs/design.md must not invent a Firefox/Safari SKU")
    if re.search(r"\bkeyt\b|\*\*t\*\*\s*key|\bt\s+key\b", low):
        _fail("docs/design.md must not sell KeyT as a product path")
    if "speechsynthesis" in low or "gemini" in low:
        _fail("docs/design.md must not invent speechSynthesis / Gemini")


def test_lock_chrome_does_not_sell_gemini() -> None:
    """Lock chrome is Hands-class / PLAY ANYWAY — not Gemini AI HAND LOCK."""
    html = _read("proto/index.html")
    lock = re.search(r'id="screen-lock"[\s\S]*?id="screen-calib"', html)
    if not lock:
        _fail("proto/index.html lost screen-lock")
    lock_html = lock.group(0)
    lock_low = lock_html.lower()
    for banned in _CHROME_GEMINI_LOCK_LIES:
        if banned in lock_low:
            _fail(
                f"lock chrome must not sell Gemini product-lock {banned!r} — "
                "Hands-class is the interim stack; PLAY ANYWAY / Space stay Q4"
            )
    if "gemini" in lock_low:
        _fail(
            "lock chrome must not name Gemini as product lock — "
            "MediaPipe Hands-class is the interim ship stack"
        )
    if "ai hand" in lock_low:
        _fail("lock chrome must not sell AI HAND LOCK as product vision")
    if 'id="btn-gemini-lock"' in html or "btn-gemini-lock" in html:
        _fail("lock chrome must not paint btn-gemini-lock")
    if "AI HAND LOCK" in html:
        _fail("lock chrome must not paint AI HAND LOCK")
    if "PLAY ANYWAY" not in lock_html or 'id="btn-skip-lock"' not in lock_html:
        _fail("Q4 PLAY ANYWAY / btn-skip-lock must stay on the lock screen")
    if "SEEKING" not in lock_html:
        _fail("lock chrome must still open on SEEKING")

    boot = _read("proto/boot.js")
    src = proto_js()
    if "GEMINI 3.8 ANALYZING" in boot or "GEMINI 3.8 ANALYZING" in src:
        _fail("lock status must not paint GEMINI 3.8 ANALYZING as product lock")
    if re.search(r'fetch\s*\(\s*["\']/api/gemini/lock', boot):
        _fail("lock path must not fetch /api/gemini/lock — Hands-class owns lock")
    if re.search(r'fetch\s*\(\s*["\']/api/gemini/lock', src):
        _fail("proto must not fetch /api/gemini/lock from the lock UI path")
    if "function requestGeminiLock" in boot or "function requestGeminiLock" in src:
        req = _js_fn(src, "requestGeminiLock")
        if "/api/gemini/lock" in req or "fetch(" in req:
            _fail(
                "requestGeminiLock must stay dead-path — "
                "do not fetch /api/gemini/lock as product lock"
            )
    tick = _js_fn(src, "tickLock")
    if "requestGeminiLock" in tick:
        _fail("tickLock must not auto-call requestGeminiLock after lock start")
    if "geminiAutoTried" in tick or "geminiLockPending" in tick:
        _fail("tickLock must not auto-try a Gemini lock fetch")
    if "/api/gemini/lock" in tick:
        _fail("tickLock must not hit /api/gemini/lock")
    if 'st.textContent = "SEEKING"' not in tick and 'textContent = "SEEKING"' not in tick:
        _fail("tickLock must still paint SEEKING until Hands lock")
    if "LOCKING" not in tick:
        _fail("tickLock must still paint LOCKING during the Hands sample window")
    if "HAND LOCKED" not in tick:
        _fail("tickLock must still confirm Hands lock — do not invent a new vision stack")
    if "goCalib" not in tick:
        _fail("Hands lock must still advance to calib")
    skip = re.search(
        r'btn-skip-lock[\s\S]{0,400}addEventListener\("click", \(\) => \{[\s\S]*?\n\}\);',
        boot,
    )
    if not skip:
        _fail("PLAY ANYWAY (btn-skip-lock) click path missing")
    skip_body = skip.group(0)
    if "goCalib" not in skip_body or "goDesktopRange" not in skip_body:
        _fail("PLAY ANYWAY must stay Q4 — goCalib or goDesktopRange")
    if "requestGeminiLock" in skip_body:
        _fail("PLAY ANYWAY must not call Gemini lock")
    test_engine_hud_does_not_sell_gemini()


def test_engine_hud_does_not_sell_gemini() -> None:
    """Engine chips are HANDS + MOJO — not GEMINI / GEMINI OFF product status."""
    src = proto_js()
    boot = _read("proto/boot.js")
    chip = _js_fn(src, "drawModeChip")
    if re.search(r"\bGEMINI(\s+OFF)?\b", chip) or re.search(r"gemini", chip, re.I):
        _fail(
            "drawModeChip must not paint GEMINI / GEMINI OFF as a live engine — "
            "Hands-class + Mojo are the product engine tells"
        )
    if "S.engine.gemini" in src or "S.engine.gemini" in boot:
        _fail("S.engine.gemini is dead — do not wire HUD or health into a Gemini engine")
    if re.search(r"S\.engine\.gemini\s*=", src):
        _fail("do not assign S.engine.gemini from /api/health or anywhere else")
    if re.search(r"engine:\s*\{[^}]*gemini", src):
        _fail("S.engine must not keep a dead gemini field as product engine state")
    if "h.gemini" in boot:
        _fail("health fetch must not wire h.gemini into S.engine — HUD archaeology")
    if '"HANDS"' not in chip or "HANDS OFF" not in chip:
        _fail("drawModeChip must still paint HANDS / HANDS OFF — MediaPipe interim truth")
    if "S.engine.hands" not in chip:
        _fail("HANDS chip must read S.engine.hands")
    if "MOJO 1.0" not in chip or "MOJO OFF" not in chip:
        _fail("drawModeChip must still paint MOJO 1.0 / MOJO OFF — Mojo kernel truth")
    if "S.engine.mojo" not in chip:
        _fail("MOJO chip must read S.engine.mojo")
    hud = _js_fn(src, "drawHUD")
    if "GEMINI" in hud or "gemini" in hud.lower():
        _fail("drawHUD must not invent a GEMINI engine chip")
    html = _read("proto/index.html")
    if "GEMINI" in html or "gemini" in html.lower():
        _fail("proto chrome must not paint GEMINI as a live engine")


def test_serve_proto_does_not_sell_gemini() -> None:
    """Server must not sell Gemini lock / health after #103/#104 chrome retirement."""
    serve = _read("tools/serve_proto.py")
    if "/api/gemini/lock" in serve:
        _fail("serve_proto must not define /api/gemini/lock — Hands-class owns lock")
    if "gemini_muzzle_tracker" in serve:
        _fail("serve_proto must not import gemini_muzzle_tracker")
    if "detect_mouse_in_image" in serve or "detect_hand_in_image" in serve:
        _fail("serve_proto must not keep a Gemini detector import")
    health = re.search(r'if path == "/api/health":[\s\S]*?return', serve)
    if not health:
        _fail("serve_proto lost GET /api/health")
    if re.search(r'["\']gemini["\']', health.group(0)):
        _fail("health JSON must not advertise a gemini field")
    if re.search(r"gemini\s*=", serve):
        _fail("startup banner must not advertise gemini=")
    if "gemini" in serve.lower():
        _fail("serve_proto must not name Gemini as a live capability")
    if (ROOT / "tools/gemini_muzzle_tracker.py").is_file():
        _fail("gemini_muzzle_tracker.py must stay deleted — not on the ship path")
    release = _read(".github/workflows/release.yml")
    if re.search(r"zip\s[^\n]*gemini_muzzle_tracker", release):
        _fail("release zip must not ship gemini_muzzle_tracker.py")
    if re.search(r"test\s+-f\s+tools/gemini_muzzle_tracker", release):
        _fail("release must not require gemini_muzzle_tracker.py")
    for rel in (
        "README.md",
        "docs/aim_pipeline.md",
        "research/TRACKING.md",
        "research/HAND_FUTURE.md",
    ):
        text = _read(rel)
        if "/api/gemini/lock" in text:
            _fail(f"{rel} must not cite /api/gemini/lock as a live pattern")
        if re.search(r"Gemini (only seeds|may seed)", text):
            _fail(f"{rel} must not claim Gemini seeds as product")
        if "gemini_muzzle_tracker" in text:
            _fail(f"{rel} must not keep gemini_muzzle_tracker on the product path")


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
        test_readme_keys_shot_honesty()
        test_proto_headers_shot_honesty()
        test_readme_zip_play_honesty()
        test_readme_t_desktop_honesty()
        test_readme_ship_floor_honesty()
        test_production_one_sentence_ship_floor()
        test_bay_docs_shot_honesty()
        test_design_md_shot_honesty()
        test_chrome_product_shoot_is_shark_fin()
        test_chrome_reload_is_charger_plug()
        test_chrome_calib_capture_is_shark_fin()
        test_lock_chrome_does_not_sell_gemini()
        test_engine_hud_does_not_sell_gemini()
        test_serve_proto_does_not_sell_gemini()
        test_no_mouse_art_invented()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("hand future invent ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
