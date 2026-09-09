# SablePort — port path

Ownership: **SablePort**. North star: keep SABLE original IP while leaving honest seams so a later migrate toward a CS2-class and/or Creative / UEFN-class *host feel* is possible. Feeling and architecture only. **Zero Valve / Epic IP in this tree now** — no stolen assets, maps, guns, names, audio, or chrome.

This is not a rewrite and not a content pack. Runtime host is **SABLE** (`SABLE_PORT_HOST = "sable"`). Code seam: `proto/port.js`. Literacy that names other titles lives here and in `research/`, never in runtime art. CS2 / UEFN stay literacy-only behind `sableHostFeel()` — adapters read the SABLE feel; they do not import foreign DNA.

## Ship floor (locked)

The playable product surface is **Chromium on MacBook Pro–class** (lid camera). Not optional. `SablePort.feel().surface` is `chromium-macbook` (`SABLE_PORT_SURFACE`). Host id stays `sable` — do not rename the host to a desktop title.

Godot / native work is an **engineering path only** — it may serve the web ship (kernels, capture experiments, CI). It is **not a second product** and not the product host. Soft-lock / ship only cuts that match hand-only + this Chromium / MacBook floor. Invent / Meta / SAM vision stays in-browser or a thin local bridge; this cut does not vendor a heavy model.

## Locked boundaries

A later host adapter plugs in behind these bars. It does not move them.

### Verb = AimBus hand gesture (`aimbus-hand-gesture`)

Product verb: **hand point** (aim) + **shark-fin** (shoot) → `AimBus` peek. Reload is **charger-plug** (index+middle ceiling). The shot still peeks `AimBus` only — `AimSample` stays `{ uv, valid, lifted, confidence, t_hw }`. The shot must not wait on a camera frame, the Hands worker, the 128 Hz step, rAF, or net.

DESKTOP HID pad (trackpad / mouse click) stays an **honesty fallback**, not the product verb. HID pointerdown lives on `window` — `#hud` is `pointer-events: none` and must not mute the pad. After JOIN, leftover CODE/JOIN under the hidden cursor is not chrome. Pinch is not a trigger. Shark-fin peeks last pointing UV after lift, before `updateAim`. Waiting-yard `lobby` uses the same `fire()`. No bloom. No aim-assist. No RNG on the lifted shot. Contract: `docs/aim_pipeline.md`.

### Sim tick = 128 Hz, HID outside

Named sim is **128 Hz** (`server/tick.py`, client `stepSim` / `S.simTick`). Render is rAF (consumer). Shared house and shared Bay are rewind (`fire_ms` on the grid), not a friend tick. Fire at tick 0 is legal. Contract: `docs/tick.md`.

### Look bible

Charcoal / bone / mint / rust. Unshaded / baked CANCHO. No ACES. No mint emissive bloom over the reticle. Original silhouettes — cuff, bone plates, Salt House ribs, charcoal / rust Yard bunkers (few, low) so plates stay readable. **Fortnite-class** on this path is **silhouette literacy only** (charcoal / bone / mint / rust) — not a license to import Epic / UEFN / Valve names, maps, guns, or chrome into `proto/` or `art/`. Paint sheets: `art/concepts/`. Runtime meshes: `proto/house.js`. A later host does not import Marketplace packs, scans, or third-party guns to “look right.”

### Modes

Playlist stays SABLE: Offline **GALLERY** (`play("range")`, one click), waiting-arena HUD-on-Yard always-practice (camera armed fire-and-forget, no lock tax), **WARM UP** (phase-preserve the live Yard — no `play()` lock tax), **ENTER RANGE**, **BAY** / **ENTER BAY**. Gallery is never the only gun. **BAY** / **ENTER BAY** are playlist / port architecture seams — not a live gun. Player chrome is Yard-only. Internal house phase stays `range`. Contract: `docs/modes.md`.

## Soft-lock (do not touch on this path)

Offline one-click. `AimSample` locked. Fire peek. R6 128 Hz. Hands Worker off the click. SableHUD thin chips (gallery **and** Bay first-to-5, plus hangar `WAIT` / `READY` / `LIVE` from `S.hangar` and a thin `ROOM` chip from `S.room` on `wait_practice` / `match_live`). Room snapshot owns hangar. SableAudio dry-tick / hit punch / mint-tell (`Mint. Lift.`) — short audio cue only, do not paint VO over the cuff / hide the gun. Boot **BAY** stays local as a seam. Shared Bay is rewind, not a lobby friend tick. ENTER RANGE is phase-preserve — skip calib/lock when already lifted; HID never waits on the lobby POST. After JOIN, leftover CODE/JOIN is not the pad. Behavior unchanged. Player-facing boot **BAY** / lobby **ENTER BAY** stay off chrome (`docs/modes.md`).

## Ship addendum (Yard look lock)

Ship this Look cut with the same bars. Fortnite-class = silhouette literacy only. `tools/test_sableport.py` fails loud if Epic / UEFN / Valve DNA lands in `proto/` (minus vendor) or `art/`. No bloom over the reticle. Offline / WARM UP stay one-click. Bay stays parked. `AimSample` untouched. Product fire peeks `AimBus` from the hand gesture. Chromium / MacBook Pro floor stays the ship surface.

## What a later port may take

- *Feeling*: peek-geometry literacy, island cadence, booth pressure — as architecture notes, then original SABLE rooms that rhyme.
- *Architecture*: a host adapter behind `SablePort.feel()` / `sableHostFeel()`. Today that function returns host `sable`, surface `chromium-macbook`, verb `aimbus-hand-gesture`. A later cut may swap host *feel* without rewriting the verb or leaving the Chromium floor.
- Tick honesty and HID-outside-both. Those travel.

## What a later port must not take

- Names, maps, guns, audio, UI chrome, or silhouettes from Valve or Epic titles.
- `de_*` halls, `.vmf` / `.bsp` / `.vmap`, Marketplace / Fab packs, published Creative / UEFN islands, league bunker catalogs.
- Changing `AimSample`, gating fire on cam / worker / tick, blooming the reticle, or making gallery the only gun.
- A second product on Godot or a desktop binary. Native stays an engineering path only.

## Runtime vs notes

| Tree | May name foreign titles? |
|------|--------------------------|
| `docs/port.md`, `docs/modes.md`, `research/` | Yes — refuse / literacy only |
| `proto/` (client, minus `vendor/`), `art/` | **No** — fail loud |

`tools/test_sableport.py` walks runtime art and fails on Valve / Epic DNA strings. Gallery / SableQA already scan a subset; this cut owns the full walk.

## Product gate

`tools/test_sableport.py` plus the existing Offline / tick / HUD / audio locks. Fail loud if the Chromium / MacBook floor dies, if host id leaves `sable`, if this file makes a desktop binary the product host, or if runtime invents foreign DNA. Merge when CI is green. Prefer docs + thin seams over a second game.
