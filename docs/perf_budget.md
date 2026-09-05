# Perf budget

Floor: **1080p 60** on a GTX 1650 4 GB class.
Stretch: **1080p 120** on an RTX 3060 laptop class.

| System        | Budget                         |
|---------------|--------------------------------|
| Sim           | 128 Hz named tick (dedicated + local Range/Bay). Shared house is closed-form rewind, not this loop. |
| Render        | rAF WebGL, no glow, no bloom   |
| Shadows       | baked / few; no virtual geo    |
| Post          | off (no bloom)                 |
| Aim capture   | 1–3 ms CPU on the worker       |
| Aim filter    | << 0.2 ms                      |
| HID fire      | **< 8 ms** HID→hitscan (`?sableperf=1` / `window.SablePerf`). Shared Bay `reportSharedBayFire` / `reportSharedBayPose` / lobby poll stay fire-and-forget **after** `markHid` — never on the click. |
| Net (later)   | ENet, server-authoritative     |

Do not spend the frame on cinematic lighting. Spend it on a stable reticle. Shared Bay must not tax the HID fire verb.
