#!/usr/bin/env python3
"""HID fire uses the last AimSample even if the current camera frame is missing."""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


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


def test_gdscript_does_not_wait() -> None:
    hid = _read("godot/src/input/hid_fire.gd")
    bus = _read("godot/src/input/aim_bus.gd")
    banned = (
        r"await\s+",
        r"wait_for",
        r"poll_capture",
        r"process_missing",
        r"get_next_frame",
    )
    for src, label in ((hid, "hid_fire.gd"), (bus, "aim_bus.gd")):
        for pat in banned:
            if re.search(pat, src):
                raise AssertionError(f"{label} gates fire on a camera wait ({pat})")
    if "func fire(" not in bus:
        raise AssertionError("aim_bus.gd must define fire()")
    if "return _latest" not in bus:
        raise AssertionError("aim_bus.gd fire/peek must return _latest")
    if "shot_from_bus" not in hid:
        raise AssertionError("hid_fire.gd must peek the bus")


def main() -> int:
    try:
        test_python_mailbox()
        test_gdscript_does_not_wait()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("hid fire contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
