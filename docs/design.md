# SABLE design (scaffold)

## 30-second loop

Pad-strafe (mouse on the pad, later) → **lift** → point at the monitor → **click** → drop back to the pad. Physical ADS is the verb. This is not a flick-assist shooter and it is not a bloom-the-reticle toy.

v1 modes (later): offline **Range**, **1v1**, **2v2**. This repository ships the engine skeleton and a dark Range so aim can be felt.

## Range (now)

Dark booth. Locked camera. High-contrast orbs. No world bloom. Crosshair follows `AimSample.uv`. Click fires the **latest** sample (desktop fallback = OS cursor via **T**. **Space** force-guns / `lifted`).

| Time | Phase | What |
|------|--------|------|
| 0–3s+ | PAD | Fat center orb + LIFT prompt. Chip pulses until `AimSample.lifted`. First-ever run also holds the fat orb until the first hit. The clock does **not** skip lift. |
| 3–27s | GUN | One orb at a time on L/C/R × near/mid/far. Hit = score + 80ms scale-pop, next orb 180ms later. Miss = dry tick, no flinch. |
| 27–30s | DROP | Freeze score, hide orb, no spawns. |

Mode chip in Range is the loop phase (`PAD` / `GUN` / `DROP`). Aim-service chips (`DESKTOP` / `SEEKING`) stay on the input bus.

WASD is unused in this pass.

## Visual bar

Baked / unshaded look. No realtime GI. No hardware RT. No virtualized geometry. No glow bloom on the reticle or the world. 1080p 60 on a GTX 1650 4 GB class floor; 1080p 120 on an RTX 3060 laptop class.

## What this pass is not

No maps, no guns, no netcode, no Steam, no anti-cheat beyond empty stubs. Aim is the engine.
