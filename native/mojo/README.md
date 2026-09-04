# native/mojo — SABLE SIMD kernels (Mojo 1.0)

Apache-2.0. Built with Pixi against Modular Mojo 1.0.

| Module | Role |
|--------|------|
| `aim_sample.mojo` | Shared `AimSample` contract |
| `aim_bus.mojo` | Latest-sample mailbox. `fire()` peeks; never waits |
| `one_euro.mojo` | Adaptive pointing filter (Casiez 2012) |
| `moments.mojo` | Soft-mask spatial moments / sub-pixel centroid |
| `hitscan.mojo` | 3D ray–sphere intersection |
| `test_aim.mojo` | Unit suite |
| `bench.mojo` | Hardware-limit microbenchmarks |

```bash
pixi install
pixi run test-aim
pixi run bench
```
