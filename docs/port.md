# SablePort — port path

Ownership: **SablePort**. North star: keep SABLE original IP while leaving honest seams so a later migrate toward a CS2-class and/or Creative / UEFN-class *host feel* is possible. Feeling and architecture only. **Zero Valve / Epic IP in this tree now** — no stolen assets, maps, guns, names, audio, or chrome.

This is not a rewrite and not a content pack. Runtime host is **SABLE**. Code seam: `proto/port.js`. Literacy that names other titles lives here and in `research/`, never in runtime art.

## Locked boundaries

A later host adapter plugs in behind these bars. It does not move them.

### Verb = AimBus / HID peek

The gun is the pointing hand. `fire()` peeks `AimBus` only. `AimSample` stays `{ uv, valid, lifted, confidence, t_hw }`. The shot must not wait on a camera frame, the Hands worker, the 128 Hz step, rAF, or net. No bloom. No aim-assist. No RNG on the lifted shot. Contract: `docs/aim_pipeline.md`.

### Sim tick = 128 Hz, HID outside

Named sim is **128 Hz** (`server/tick.py`, client `stepSim` / `S.simTick`). Render is rAF (consumer). Shared house and shared Bay are rewind (`fire_ms` on the grid), not a friend tick. Fire at tick 0 is legal. Contract: `docs/tick.md`.

### Look bible

Charcoal / bone / mint / rust. Unshaded / baked CANCHO. No ACES. No mint emissive bloom over the reticle. Original silhouettes — cuff, bone plates, Salt House ribs. Paint sheets: `art/concepts/`. Runtime meshes: `proto/house.js`. A later host does not import Marketplace packs, scans, or third-party guns to “look right.”

### Modes

Playlist stays SABLE: Offline **GALLERY** (`play("range")`, one click), **WARM UP**, **ENTER RANGE**, **BAY** / **ENTER BAY**. Gallery is never the only gun. Internal house phase stays `range`. Contract: `docs/modes.md`.

## Soft-lock (do not touch on this path)

Offline one-click. `AimSample` locked. Fire peek. R6 128 Hz. Hands Worker off the click. SableHUD thin chips (gallery **and** Bay first-to-5). SableAudio dry-tick / hit punch / mint-tell (`Mint. Lift.`) — short audio cue only, do not paint VO over the cuff / hide the gun. Boot **BAY** stays local. Shared Bay is rewind, not a lobby friend tick. Behavior unchanged.

## What a later port may take

- *Feeling*: peek-geometry literacy, island cadence, booth pressure — as architecture notes, then original SABLE rooms that rhyme.
- *Architecture*: a host adapter behind `SablePort.feel()` / `sableHostFeel()`. Today that function returns the SABLE identity. A later cut may swap the host id without rewriting the verb.
- Tick honesty and HID-outside-both. Those travel.

## What a later port must not take

- Names, maps, guns, audio, UI chrome, or silhouettes from Valve or Epic titles.
- `de_*` halls, `.vmf` / `.bsp` / `.vmap`, Marketplace / Fab packs, published Creative / UEFN islands, league bunker catalogs.
- Changing `AimSample`, gating fire on cam / worker / tick, blooming the reticle, or making gallery the only gun.

## Runtime vs notes

| Tree | May name foreign titles? |
|------|--------------------------|
| `docs/port.md`, `docs/modes.md`, `research/` | Yes — refuse / literacy only |
| `proto/` (client, minus `vendor/`), `art/` | **No** — fail loud |

`tools/test_sableport.py` walks runtime art and fails on Valve / Epic DNA strings. Gallery / SableQA already scan a subset; this cut owns the full walk.

## Product gate

`tools/test_sableport.py` plus the existing Offline / tick / HUD / audio locks. Merge when CI is green. Prefer docs + thin seams over a second game.
