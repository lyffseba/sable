#!/usr/bin/env python3
"""STACK.md exists and still names the pins this tree actually solves.

Reads the work tree only. Does not fetch release pages. The SNAPSHOT_MARKERS
tuple is the 2026-09-25 latest-stable column; edit it in the same commit as
docs/STACK.md.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

HEADINGS = (
    "## Open these first",
    "## Version snapshot",
    "## How this tree uses each layer",
    "## Maintenance",
)

# Written snapshot. Not a live query.
SNAPSHOT_MARKERS = (
    "2026-09-25",
    "0.81.0",
    "v0.10.2",
    "1.1.0",
    "0.186.1",
    "r186",
    "@mediapipe/tasks-vision@1.0.1",
    "4.4.3",
    "16.2.0",
    "23.1.2",
    "24.21.0",
    "26.10.0",
    "v7.0.1",
    "5.2.2",
    "2.101.0",
    "float16/1",
    "Ubuntu 24.04",
)


def _read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise FileNotFoundError(rel)
    return path.read_text(encoding="utf-8")


def _one(pattern: str, text: str, label: str) -> str:
    match = re.search(pattern, text)
    if not match:
        raise ValueError(f"{label}: pattern not found: {pattern}")
    return match.group(1) if match.groups() else match.group(0)


def in_repo_needles() -> list[str]:
    lock = _read("pixi.lock")
    pixi = _read("pixi.toml")
    hands = _read("proto/hands.js")
    three = _read("proto/vendor/three.module.js")
    cmake = _read("native/cv_input/CMakeLists.txt")
    ci = _read(".github/workflows/ci.yml")
    release = _read(".github/workflows/release.yml")

    mojo = _one(r"mojo-(\d+\.\d+\.\d+)-release", lock, "pixi.lock mojo")
    python = _one(r"python-(\d+\.\d+\.\d+)-", lock, "pixi.lock python")
    mp = _one(r"@mediapipe/tasks-vision@(\d+\.\d+\.\d+)", hands, "hands.js mediapipe")
    rev = _one(r"REVISION = '(\d+)'", three, "three REVISION")
    cmake_floor = _one(r"cmake_minimum_required\(VERSION (\d+\.\d+)\)", cmake, "cmake")
    setup = _one(r"(prefix-dev/setup-pixi@v\d+\.\d+\.\d+)", ci, "ci setup-pixi")
    checkout = _one(r"(actions/checkout@v\d+)", ci, "ci checkout")
    mojo_spec = _one(r'mojo = "([^"]+)"', pixi, "pixi.toml mojo")
    python_spec = _one(r'python = "([^"]+)"', pixi, "pixi.toml python")

    if setup not in release or checkout not in release:
        raise ValueError("release.yml action pins diverged from ci.yml")

    return [
        f"mojo-{mojo}",
        f"python-{python}",
        f"@mediapipe/tasks-vision@{mp}",
        f"r{rev}",
        cmake_floor,
        setup,
        checkout,
        mojo_spec,
        python_spec,
        "version: 6",
    ]


def main() -> int:
    missing: list[str] = []
    stack_path = ROOT / "docs/STACK.md"
    if not stack_path.is_file():
        print("missing docs/STACK.md", file=sys.stderr)
        return 1
    stack = stack_path.read_text(encoding="utf-8")
    readme = _read("README.md")
    if "docs/STACK.md" not in readme:
        missing.append("README.md does not link docs/STACK.md")
    for heading in HEADINGS:
        if heading not in stack:
            missing.append(f"heading: {heading}")
    try:
        needles = in_repo_needles()
    except (OSError, ValueError) as exc:
        print(f"stack doc pin extract: {exc}", file=sys.stderr)
        return 1
    for needle in needles:
        if needle not in stack:
            missing.append(f"in-repo pin not named: {needle}")
    for marker in SNAPSHOT_MARKERS:
        if marker not in stack:
            missing.append(f"snapshot marker missing: {marker}")
    if missing:
        print("stack doc:\n" + "\n".join(missing), file=sys.stderr)
        return 1
    print("stack doc ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
