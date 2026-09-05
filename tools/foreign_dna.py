#!/usr/bin/env python3
"""Valve / Epic DNA needles for runtime art.

Architecture notes in docs/ and research/ may name destinations.
proto/ (minus vendor/) and art/ must not. SablePort owns the walk.
"""

from __future__ import annotations

import pathlib

# Titles, maps, pack formats — not generic words like "epic" or "creative".
# Docs may name these as refuse / silhouette literacy. proto/ + art/ must not.
FOREIGN_DNA = (
    "de_dust",
    "de_mirage",
    "de_inferno",
    "de_nuke",
    "de_overpass",
    "de_anubis",
    "de_ancient",
    "de_vertigo",
    "de_cache",
    "de_train",
    "dust2",
    "Tilted Towers",
    "Pleasant Park",
    "Retail Row",
    "Salty Springs",
    "Valve",
    "Epic Games",
    "Fortnite",
    "Counter-Strike",
    "CS:GO",
    "CS2",
    ".vmf",
    ".bsp",
    ".vmap",
    ".umap",
    "Unreal Marketplace",
    "Fab Marketplace",
    "UEFN",
)

# Ship bar: these four must stay in FOREIGN_DNA so proto/art fail loud.
REQUIRED_DNA = ("Valve", "Epic Games", "Fortnite", "UEFN")

_TEXT_SUFFIX = {".js", ".html", ".css", ".svg", ".md", ".py", ".json", ".txt"}
_SKIP_PARTS = {"vendor", ".git", "build", "bin", "node_modules"}


def iter_runtime_art(root: pathlib.Path) -> list[pathlib.Path]:
    """First-party runtime art + client (no vendor, no docs, no tests)."""
    out: list[pathlib.Path] = []
    for tree in (root / "proto", root / "art"):
        if not tree.exists():
            continue
        for path in tree.rglob("*"):
            if not path.is_file():
                continue
            if any(part in _SKIP_PARTS for part in path.parts):
                continue
            if path.suffix.lower() not in _TEXT_SUFFIX:
                continue
            out.append(path)
    return sorted(out)


def dna_hits(text: str) -> list[str]:
    low = text.lower()
    return [needle for needle in FOREIGN_DNA if needle.lower() in low]


def scan_runtime_art(root: pathlib.Path) -> list[str]:
    hits: list[str] = []
    for path in iter_runtime_art(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            hits.append(f"unreadable {path.relative_to(root)}: {exc}")
            continue
        for needle in dna_hits(text):
            hits.append(f"{path.relative_to(root)}: {needle}")
    return hits
