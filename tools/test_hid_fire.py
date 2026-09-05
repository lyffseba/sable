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


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _js_fn(src: str, name: str) -> str:
    m = re.search(rf"function {name}\([^)]*\) \{{[\s\S]*?\n\}}", src)
    if not m:
        raise AssertionError(f"missing function {name}")
    return m.group(0)


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
        test_client_does_not_wait()
        test_sableperf_budget()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("hid fire contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
