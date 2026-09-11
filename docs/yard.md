# THE YARD — original paintball shooting range

SABLE first-party layout. **The sole active map.** Bay booth is parked (`docs/maps/bay.md`). **Not** a league field. **Not** another game’s island. If you rebuild this in any other editor, copy **this file**, never a published tournament diagram.

## What this is

A **shooting range** you stand in. One firing line. Original inflatables we designed. Plates come out from cover. Product path is hand + Chromium on a MacBook Pro–class lid camera (point + shark-fin). Trackpad is menus / DESKTOP emergency only (non-product). Two laptops join the same room later. The waiting arena is this same Yard — HUD chips, not a second map.

This is **not** a 5-on-5 match field yet. Same art kit can grow into a stadium **we** design.

## Rights

- Shapes are primitives we author (drum, peak, beam, stack, wing, cross).
- Names below are SABLE names. Do not label them with other companies’ bunker catalog names.
- Dimensions are ours. Do not paste a league 10-ft grid into the client.
- Colors: CANCHO charcoal / rust bunkers (few, low). Bone plates + mint cores stay the readable tell. Not another series’ vinyl.

## Range (meters, origin at the firing line)

Camera / player at `(0, 1.64, 0)` looking −Z. Floor y = −1.64.

| Piece | x | z | size (x,y,z) m | notes |
|-------|---|---|----------------|-------|
| Home pad | 0 | 1.35 | 2.1 × 0.12 × 1.3 | rust stand |
| Beam L | −3.4 | −4.2 | 2.8 × 0.76 × 0.76 | low charcoal crawler, rust caps |
| Beam R | 3.4 | −4.2 | 2.8 × 0.76 × 0.76 | low charcoal crawler, rust caps |
| Drum | −1.6 | −7.0 | 1.7 × 0.7 × 1.2 | short rust mass |
| Peak | 2.2 | −8.5 | Ø 2.0 × H 0.92 | low charcoal pyramid, rust rim |
| Backstop | 0 | −16.8 | 6.4 × 2.4 × 1.35 | solid rust block |

180° stadium symmetry is **later**. The range faces one way on purpose.

## Shared rules (any parallel prototype)

Use these numbers only — not another game’s device list.

- Playlist: Gallery 60 s (`docs/modes.md`), then later 5v5 on a **SABLE** stadium.
- One-hit plates / one-hit out in 5v5.
- Start pad 2.0 × 1.2 m.
- Fire is shark-fin on the hand path, HID on DESKTOP / pad fallback. Aim is the pointing hand. Shark-fin peeks the last pointing `AimBus` UV — the gesture must not rewrite the shot. Pinch is not a trigger.
- No bloom. No aim-assist.

## Trigger iterations (MacBook)

0. **Now:** point index at the glass. **Shark-fin** (thumb UP) = fire (rising-edge peek last pointing UV, including the waiting Yard). Thumb parallel = safe. Pad HID is DESKTOP / cam-deny fallback — `#hud` must not mute the tap. After JOIN, leftover CODE/JOIN under the hidden cursor must not eat the pad. Space is Q4 forceGun escape, not product shoot.
1. Pinch is removed as a fire() caller. `pinchStrength` is the shark-fin safe gate only. A fresh ONLINE arms the camera so shark-fin can live — no lock tax. WARM UP from that live Yard keeps the gun — no lock tax.
2. Reload (index+middle up / charger-plug) is this cut — `maybeReloadGesture` rising-edge refill. Do not invent reload on DESKTOP / HID / Space.
