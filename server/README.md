# Dedicated server

128 Hz headless tick. Hitscan uses Mojo 1.0 kernels when Pixi is installed.

```bash
./tools/headless_tick.sh
# or
pixi run python server/tick.py
```

Prints `SABLE headless tick ok` and exits 0. Browser fire stays HID-local; this process is the sim peek, not a gate on the shot.
