# SABLE design (scaffold)

## 30-second loop

Pad-strafe (mouse on the pad, later) → **lift** → point at the monitor → **click** → drop back to the pad. Physical ADS is the verb. This is not a flick-assist shooter and it is not a bloom-the-reticle toy.

v1 modes (later): offline **Range**, **1v1**, **2v2**. This repository ships the engine skeleton and a dark Range so aim can be felt.

## Range (now)

Dark empty volume. One dummy orb. Crosshair follows `AimSample.uv`. Click fires the **latest** sample (desktop fallback = OS cursor). Hits despawn the orb and spawn another. Score in the corner. Mode chip: `PAD` / `GUN` / `DESKTOP` / `SEEKING`. Confidence meter on screen.

WASD is unused in this pass.

## Visual bar

Baked / unshaded look. No realtime GI. No hardware RT. No virtualized geometry. No glow bloom on the reticle or the world. 1080p 60 on a GTX 1650 4 GB class floor; 1080p 120 on an RTX 3060 laptop class.

## What this pass is not

No maps, no guns, no netcode, no Steam, no anti-cheat beyond empty stubs. Aim is the engine.
