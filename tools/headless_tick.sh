#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${GODOT_BIN:-}"
if [[ -z "$BIN" ]]; then
	for c in godot godot4 godot4.7 Godot_v4.7.2-stable_linux.x86_64; do
		if command -v "$c" >/dev/null 2>&1; then
			BIN="$c"
			break
		fi
	done
fi
if [[ -z "$BIN" ]]; then
	echo "GODOT_BIN not set and no Godot binary on PATH. Headless boot skipped."
	exit 0
fi
exec "$BIN" --headless --path "$ROOT/godot" "$@"
