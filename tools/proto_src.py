#!/usr/bin/env python3
"""Concatenated proto client JS for contract tests after the R1 split."""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROTO_CLIENT = (
    "aim.js",
    "hands.js",
    "house.js",
    "boot.js",
    "game.js",
)


def proto_js() -> str:
    chunks: list[str] = []
    for name in PROTO_CLIENT:
        path = ROOT / "proto" / name
        if path.is_file():
            chunks.append(path.read_text(encoding="utf-8"))
    if not chunks:
        raise FileNotFoundError("no proto client JS")
    return "\n".join(chunks)
