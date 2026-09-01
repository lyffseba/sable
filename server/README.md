# Dedicated server

Headless boot must work now. Hits are not authoritative yet; the process still has to start.

## Godot binary (no export)

```bash
export GODOT_BIN="${GODOT_BIN:-godot}"
"$GODOT_BIN" --headless --path "$(dirname "$0")/../godot"
```

Or from repo root: `./tools/headless_tick.sh`.

The boot autoload detects `dedicated_server`, `--headless`, or `--server`, ticks 64 Hz, prints `SABLE headless tick ok`, and exits 0 unless `--stay` is passed.

## Export

In Godot 4.7.2: **Project → Export → Linux Dedicated Server**.

```bash
"$GODOT_BIN" --headless --path godot --export-release "Linux Dedicated Server" ../build/linux/sable_server.x86_64
./build/linux/sable_server.x86_64
```

Requires Linux export templates for 4.7.2. CI skips this step when `GODOT_BIN` is unset.
