# CANCHO — Operator 1 locker

Specs live in this repo. There is no second art repo. There is no body mesh yet. Do not invent one.

**CANCHO** is operator slot 1. The player is this operator, not a nameless capsule. Code: `godot/src/locker/` (`locker.gd`, `operator_def.gd`, `outfit_style.gd`). Autoload: `Locker`. Bay applies the look with `Locker.apply_capsule(...)`.

`id`: `cancho`. `skeleton_id`: `cancho_capsule`. Three style ids are skins on that one skeleton, later the same skeleton, not new characters.

## Original IP

SABLE original. Canserbero is voltage only: no face, no likeness, no catalog, no beanie, no glasses. Do not generate or import a portrait. Do not add a gun mesh. Do not body-scan anyone.

## Silhouette (intent)

Lean **1.78 m**. High collar. Fade — no hair, no face. Capsule radius **0.28 m** in `godot/scenes/bay/Bay.tscn` until a real body exists. Eye height **1.64 m**. Collar is a short cylinder on the capsule. That is the placeholder, not the product mesh.

## Tell

Mint stripe on the **lifting / gun-arm glove**. Rust thread at the wrist. The mint stripe is the tell on every look. Night dims it until `AimSample.lifted`, then it goes full mint.

The gun arm stays visible in Bay (except match-over) so the night dim stripe can read. No weapon mesh hangs off it. AimSample is the gun.

## Palette

Unshaded tints only. No new textures this pass. Paint albedos later on the same skeleton.

| Token | RGB |
|-------|-----|
| charcoal body (default) | `0.06 0.07 0.08` |
| HUD bone | `0.90 0.88 0.82` (`Locker.BONE`) |
| mint | `0.35 0.95 0.78` (`Locker.MINT`) |

`Locker.apply_capsule` writes `StandardMaterial3D` with `SHADING_MODE_UNSHADED`.

## Styles (same skeleton)

Cycle in Bay with **L** (`cycle_style`, physical keycode 76). `Locker.cycle_style()` walks `default → ranked → night → default`. HUD score line shows the equipped style id.

| id | Body | Stripe | Rest (not lifted) | Extra |
|----|------|--------|-------------------|-------|
| `default` | `0.06 0.07 0.08` | mint `0.35 0.95 0.78` | same mint | rust wrist `0.55 0.28 0.18` |
| `ranked` | `0.04 0.05 0.07` | mint on **gun arm and chest** | same mint | rust wrist `0.45 0.26 0.20` |
| `night` | `0.02 0.02 0.025` | full mint **when lifted** | dim mint `0.12 0.35 0.28` | rust wrist `0.20 0.10 0.08` |

Chest band (`ChestBand`) is visible only for `ranked`. It paints with full mint, not the rest color. Night has no chest band.

## VO (operator, not outfit)

Lines belong to CANCHO. Swapping a look does not change VO.

| Event | Line |
|-------|------|
| lift mint-tell (`AimSample.lifted` / GUN edge) | `Mint. Lift.` (SableAudio; oscillator chirp this cut — no browser TTS, no VO chip over the cuff) |
| hit | `Claro.` |
| drop (`!lifted` edge) | `Al suelo.` |
| first-to-5 | `Se escribió.` |

HUD `VoChip` holds hit / drop / win for **0.70 s**. Lift mint-tell is the short SableAudio chirp only — do not paint `Mint. Lift.` over the cuff. Miss is a **dry tick** (generated click + HUD tick). No trash talk. Cancho does not comment a miss.

## Do not

- Do not touch `AimSample` or the tracker.
- Do not hide the gun with mint-tell VO.
- Do not add a second art repo.
- Do not invent a body mesh, face, beanie, glasses, or gun.
- Do not treat a style id as a new operator.
