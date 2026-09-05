#!/usr/bin/env python3
"""Hands Worker cut: detect off main rAF. Fail loud if fire waits on the worker."""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from proto_src import proto_js  # noqa: E402

LITE_TASK = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)
VENDOR_TASK = "vendor/mediapipe/hand_landmarker.task"


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"(?:async )?function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        raise AssertionError(f"missing function {name}")
    return m.group(0)


def _fail(msg: str) -> None:
    raise AssertionError(f"SABLEQA FAIL: Hands worker — {msg}")


def main() -> int:
    try:
        js = proto_js()
        worker = (ROOT / "proto/hands_worker.js").read_text(encoding="utf-8")
        hands = (ROOT / "proto/hands.js").read_text(encoding="utf-8")
        notice = (ROOT / "proto/vendor/mediapipe/NOTICE").read_text(encoding="utf-8")
        task = ROOT / "proto/vendor/mediapipe/hand_landmarker.task"

        if "HandLandmarker" not in worker or "detectForVideo" not in worker:
            _fail("worker lost HandLandmarker.detectForVideo")
        if 'delegate: want' not in worker and "delegate: want" not in worker:
            if '"GPU"' not in worker:
                _fail("worker must prefer GPU")
        if '"GPU"' not in worker or '"CPU"' not in worker:
            _fail("worker must try GPU then CPU")
        if "FilesetResolver" not in worker:
            _fail("worker must load Tasks Vision wasm")

        if "new Worker" not in hands or "hands_worker.js" not in hands:
            _fail("initHands must spawn proto/hands_worker.js")
        if "startHandsWorker" not in hands:
            _fail("worker boot missing")
        if "applyEuroPoint" not in _js_fn(js, "applyMpLandmarks"):
            _fail("One Euro must run on UV after landmarks, before mailbox")
        mp = _js_fn(js, "mpTrack")
        if "kickAndFresh" not in mp and "kickWorkerDetect" not in mp:
            _fail("mpTrack must kick the worker, not detect on main")
        if "detectForVideo" in mp:
            _fail("mpTrack happy path called detectForVideo on main")

        fire = _js_fn(js, "fire")
        if re.search(r"await\s+", fire):
            _fail("fire() awaits — HID waits on a promise")
        if re.search(r"postMessage|createImageBitmap|detectForVideo|hands_worker|new Worker", fire):
            _fail("fire() talks to the worker — HID waits on cam/detect")
        if "coastTrack" in fire or "updateAim" in fire:
            _fail("fire() recomputes aim")
        if "aimBus.fire" not in fire:
            _fail("fire() no longer peeks AimBus")

        sample = re.search(r"class AimSample \{[\s\S]*?\n\}", js)
        if not sample:
            _fail("AimSample class missing")
        fields = re.findall(r"this\.(\w+)", sample.group(0))
        if fields != ["uv", "valid", "lifted", "confidence", "t_hw"]:
            _fail("AimSample fields changed — keep the locked struct")

        if not task.is_file() or task.stat().st_size != 7819105:
            _fail("vendored HandLandmarker is not Google float16/1 (7819105 bytes)")
        if "float16/1/hand_landmarker.task" not in notice:
            _fail("NOTICE must name the published float16/1 task")
        if LITE_TASK.split("mediapipe-models/")[1] not in hands and VENDOR_TASK not in hands:
            _fail("hands.js must keep the published float16/1 / vendored task path")
        if "hand_landmarker_lite" in hands or "hand_landmarker_lite" in worker:
            _fail("do not point at a non-existent lite .task")
        if "yolo" in hands.lower() or "sapiens" in hands.lower():
            _fail("Sapiens/YOLO must not become the default tracker")

        html = (ROOT / "proto/index.html").read_text(encoding="utf-8")
        if 'id="btn-play"' not in html or ">OFFLINE<" not in html:
            _fail("Offline one-click died")
        play = re.search(
            r'\$\("btn-play"\)\.addEventListener\("click", \(\) => \{[\s\S]*?play\("range"\)',
            js,
        )
        if not play or "S.online = false" not in play.group(0):
            _fail("Offline shoot path died")
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("hands worker ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
