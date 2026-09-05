# SABLE design (scaffold)

## 30-second loop

Pad-strafe (mouse on the pad, later) → **lift** → point at the monitor → **click** → drop back to the pad. Physical ADS is the verb. This is not a flick-assist shooter and it is not a bloom-the-reticle toy.

v1 modes: offline **Gallery** (Salt House 60s), **Bay** 1v1, waiting-arena **WARM UP** / **ENTER RANGE**. Playlist: `docs/modes.md`.

## Gallery (now)

**Salt House** — original hall: rust ribs, mint centerline, bone plates. 60s scored round. Escape = miss. End state: GALLERY CLEAR. Crosshair follows `AimSample.uv`. Click fires the **latest** sample. Hits shatter a plate and spawn another. Mode chip: `PAD` / `GUN` / `DESKTOP` / `SEEKING`. Thin SableHUD bar chips `SCORE` / `ROUND` / `60s GALLERY`. Sparse SableAudio: dry-tick miss, hit punch, quiet mint-tell lift (`Mint. Lift.`).

First-person mesh is CANCHO’s **cuff** (mint rail = muzzle). AimSample is still the gun. WASD unused on gallery.

## Visual bar

Flat / unshaded charcoal–bone–mint–rust. No realtime GI. No hardware RT. No glow bloom on the reticle or the world. 1080p 60 on a GTX 1650 4 GB class floor; 1080p 120 on an RTX 3060 laptop class. Paint sheets: `art/concepts/`. Literature: `research/LITERATURE.md`.

## What this pass is not

No maps, no guns, no netcode, no Steam, no anti-cheat beyond empty stubs. Aim is the engine.
