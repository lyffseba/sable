#!/usr/bin/env python3
"""Fail loud if the hand-future invent locks drift.

research/HAND_FUTURE.md is the architecture soT. AimSample stays five
fields. Product GUN is hands-only. Meta SAM-class is invent, not the
hot path. Reload stub must not invent mag. HID/DESKTOP/Space stay
labeled non-product fallbacks.
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


LOCK_NEEDLES = (
    "NORTH STAR (LOCKED):",
    "Gesture-only control. Mouse-shooter precision. No mouse control.",
    "Hands + Meta vision models must feel as precise as a mouse shooter",
    "CS honesty, Beat Saber energy, zero mouse as input verb.",
    "Hand-only. No mouse as product verb. Mouse-shooter precision.",
    "Reinvent the mouse as a hand system",
    "No mouse-body optical lock. No mouse-lift gun. No mouse mesh as shipping product art",
    "Blender ask was Kruidenhof — STOPPED for SABLE / sable-mouse track STOP",
    "Vision stack: Meta object-recognition invent path (SAM-class gate + landmark FSM hybrid",
    "MediaPipe Hands-class may stay interim until Meta stack ships. No mouse ever.",
    "aim=point; shark-fin thumb up=shoot; thumb parallel=safe; index+middle ceiling=reload.",
    "soft-lock/ship only hand-only cuts; AimSample locked; HID/DESKTOP/Space = engineering fallbacks never product story.",
    "Platform: MacBook Pro + Chromium web floor.",
)


def test_locks_verbatim() -> None:
    future = _read("research/HAND_FUTURE.md")
    product = _read("research/PRODUCT.md")
    tracking = _read("research/TRACKING.md")
    if "LOCKS (verbatim" not in future:
        _fail("HAND_FUTURE.md must fold LiftShot LOCKS verbatim")
    for needle in LOCK_NEEDLES:
        if needle not in future:
            _fail(f"HAND_FUTURE.md lost verbatim lock: {needle}")
        if needle not in product:
            _fail(f"PRODUCT.md lost verbatim lock: {needle}")
        if needle not in tracking:
            _fail(f"TRACKING.md lost verbatim lock: {needle}")
    if "research/HAND_FUTURE.md" not in product or "research/HAND_FUTURE.md" not in tracking:
        _fail("PRODUCT/TRACKING must point at HAND_FUTURE.md")


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


def test_reload_stub() -> None:
    src = proto_js()
    if "function chargerReload" not in src or "function maybeReloadGesture" not in src:
        _fail("reload rising-edge stub missing")
    if "function onReloadStub" not in src:
        _fail("onReloadStub hook missing")
    reload_fn = _js_fn(src, "maybeReloadGesture")
    stub = _js_fn(src, "onReloadStub")
    charger = _js_fn(src, "chargerReload")
    if "fire()" in reload_fn or "publishAim" in reload_fn or "updateAim" in reload_fn:
        _fail("maybeReloadGesture must not fire or rewrite aim")
    if "fire()" in stub or "publishAim" in stub or "aimBus" in stub:
        _fail("onReloadStub must not peek or publish")
    if re.search(r"S\.(mag|ammo|reserve|magazine)\s*=", stub):
        _fail("onReloadStub wrote a mag field")
    if "reloadPulse" not in stub:
        _fail("onReloadStub must pulse S.reloadPulse only")
    if "S.reloadPulse" not in stub:
        _fail("onReloadStub must pulse S.reloadPulse only")
    if "S.desktop" not in reload_fn:
        _fail("maybeReloadGesture must no-op on DESKTOP")
    if "chargerReload" not in reload_fn or "S.reloadHeld" not in reload_fn:
        _fail("maybeReloadGesture must be a rising edge on chargerReload")
    if "lm[8]" not in charger or "lm[12]" not in charger:
        _fail("chargerReload must use index + middle (8 / 12)")
    frame = _js_fn(src, "frame")
    if frame.find("updateMode") > frame.find("maybeReloadGesture"):
        _fail("reload stub must run after updateMode")
    if frame.find("maybeReloadGesture") > frame.find("maybePinchFire"):
        _fail("reload stub must run before interim pinch")
    if frame.find("maybePinchFire") > frame.find("updateAim"):
        _fail("pinch must still peek before updateAim")
    desk_else = re.search(r"else if \(S\.desktop\) \{([\s\S]*?)\n  \}", frame)
    if not desk_else:
        _fail("frame lost the !camReady DESKTOP path")
    if "maybeReloadGesture" in desk_else.group(1) or "maybePinchFire" in desk_else.group(1):
        _fail("!camReady DESKTOP must not run product gestures")
    fire = _js_fn(src, "fire")
    if "onReloadStub" in fire or "maybeReloadGesture" in fire or "reloadPulse" in fire:
        _fail("reload must not enter fire()")


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
    if "if (S.desktop || productGunHidFire()) fire()" not in hid:
        _fail("range/lobby HID must gate fire on DESKTOP / productGunHidFire")
    if "if (S.desktop) publishAim(e.clientX, e.clientY)" not in hid:
        _fail("DESKTOP HID must still publish click UV before fire()")
    if hid.find("if (S.desktop) publishAim") > hid.find("fire()"):
        _fail("DESKTOP publishAim must land before any fire() peek")
    future = _read("research/HAND_FUTURE.md")
    if "productGunHidFire" not in future:
        _fail("HAND_FUTURE.md must name the HID-as-gun deprecation gate")
    tracking = _read("research/TRACKING.md")
    if "productGunHidFire" not in tracking:
        _fail("TRACKING.md must name productGunHidFire")


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
    future = _read("research/HAND_FUTURE.md")
    if "Non-product" not in future and "non-product" not in future:
        _fail("HAND_FUTURE.md must label DESKTOP/cam-deny non-product")
    if "sable-mouse track STOP" not in future:
        _fail("HAND_FUTURE.md must keep sable-mouse STOP")
    if "No mouse ever" not in future:
        _fail("HAND_FUTURE.md must keep no mouse ever")


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
        test_reload_stub()
        test_product_gun_hid_deprecated()
        test_fallbacks_labeled_non_product()
        test_no_mouse_art_invented()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("hand future invent ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
