# SABLE design (scaffold)

## 30-second loop

Pad-strafe (mouse on the pad, later) → **lift** → point at the monitor → **click** → drop back to the pad. Physical ADS is the verb. This is not a flick-assist shooter and it is not a bloom-the-reticle toy.

v1 modes (later): offline **Range**, **1v1**, **2v2**. This repository ships the engine skeleton and a dark Range so aim can be felt.

## Range (now)

**Salt House** — original hall: rust ribs, mint centerline, bone plates. Crosshair follows `AimSample.uv`. Click fires the **latest** sample. Hits shatter a plate and spawn another. Mode chip: `PAD` / `GUN` / `DESKTOP` / `SEEKING`.

First-person mesh is CANCHO’s **cuff** (mint rail = muzzle). AimSample is still the gun. WASD unused on Range.

## Visual bar

Flat / unshaded charcoal–bone–mint–rust. No realtime GI. No hardware RT. No glow bloom on the reticle or the world. 1080p 60 on a GTX 1650 4 GB class floor; 1080p 120 on an RTX 3060 laptop class. Paint sheets: `art/concepts/`. Literature: `research/LITERATURE.md`.

## What this pass is not

No maps, no guns, no netcode, no Steam, no anti-cheat beyond empty stubs. Aim is the engine.
