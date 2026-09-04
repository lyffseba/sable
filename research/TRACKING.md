# SABLE tracking v2 — Gemini 3.8 Flash Muzzle Lock

Geometry is inverted vs Sinden: webcam at display top-center, player points mouse nose at monitor.

## Muzzle Landmark (The True Shot Origin)
- Box center / hump is the **stock** (shooting from stock misses high).
- Scroll wheel sits behind the leading edge (heading only).
- The true physical ADS barrel is the **silhouette nose / front leading-edge split between LMB and RMB**.
- **Gemini 3.8 Flash** zero-shot multimodal vision locates the exact mouse model, bounding box, and `muzzle_point` [y, x] in normalized camera space without markers, tape, or custom training.

## Hybrid Real-Time Tracking Pipeline
1. **AI Muzzle Lock (Gemini 3.8 Flash)**: Inspects live webcam frame, returns mouse identity, bounding box, muzzle coordinates, and lift state.
2. **Client-Side High-Speed Tracker (60–120 FPS)**: High-speed NCC patch tracking and One Euro pointing filter initialized at the Gemini-detected muzzle landmark.
3. **HID Fire Mailbox**: Left-click fires instantaneously against the latest `AimSample` in the mailbox. Shot is never delayed or gated on camera frame acquisition.
4. **Physical ADS Verb**: WASD moves on pad; lifting mouse locks walk and activates light-gun hitscan ray.

`AimSample { uv, valid, lifted, confidence, t_hw }`
