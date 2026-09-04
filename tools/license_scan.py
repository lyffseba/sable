#!/usr/bin/env python3
"""Fail if GPL strings appear in client/server trees.

Third-party credits may mention historical licenses only in
docs/THIRD_PARTY_NOTICES.md, which is not scanned. Never skip this tool.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TREES = (ROOT / "proto", ROOT / "server", ROOT / "native")
SKIP_PARTS = {".git", "build", "bin", "node_modules"}
NEEDLES = (
    "GNU General Public License",
    "GPL-2.0",
    "GPL-3.0",
    "GPLv2",
    "GPLv3",
    "www.gnu.org/licenses",
)

TEXT_SUFFIX = {
    ".js",
    ".html",
    ".css",
    ".json",
    ".mojo",
    ".toml",
    ".hpp",
    ".h",
    ".hh",
    ".cpp",
    ".cc",
    ".c",
    ".py",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".sh",
    ".cmake",
    ".svg",
}


def iter_files() -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for tree in TREES:
        if not tree.exists():
            continue
        for path in tree.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            if path.suffix.lower() not in TEXT_SUFFIX and path.name not in {
                "CMakeLists.txt",
                "SConstruct",
                "LICENSE",
            }:
                continue
            out.append(path)
    return out


def main() -> int:
    hits: list[str] = []
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"unreadable {path}: {exc}", file=sys.stderr)
            return 1
        for needle in NEEDLES:
            if needle in text:
                rel = path.relative_to(ROOT)
                hits.append(f"{rel}: {needle}")
    if hits:
        print("GPL string(s) in client/server:", file=sys.stderr)
        for h in hits:
            print(f"  {h}", file=sys.stderr)
        return 1
    print("license_scan ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
