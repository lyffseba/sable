# Perf budget

Floor: **1080p 60** on a GTX 1650 4 GB class.
Stretch: **1080p 120** on an RTX 3060 laptop class.

| System        | Budget                         |
|---------------|--------------------------------|
| Sim           | 64 Hz, Jolt                    |
| Render        | Forward+, no glow, no SDFGI    |
| Shadows       | baked / few; no virtual geo    |
| Post          | off (no bloom)                 |
| Aim capture   | 1–3 ms CPU on the worker       |
| Aim filter    | << 0.2 ms                      |
| Net (later)   | ENet, server-authoritative     |

Do not spend the frame on cinematic lighting. Spend it on a stable reticle.
