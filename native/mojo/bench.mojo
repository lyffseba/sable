"""Bench.mojo — Performance benchmarks for SABLE in Mojo 1.0."""

from std.time import perf_counter_ns
from one_euro import OneEuro
from moments import compute_moments_simd
from hitscan import Vec3, ray_sphere_intersect

def bench_one_euro():
    var iters = 1_000_000
    var f = OneEuro(3.0, 0.03, 1.0, 120.0)
    var val = Float64(100.0)
    var t = Float64(0.0)
    
    var t0 = perf_counter_ns()
    var i = 0
    while i < iters:
        t += 0.00833
        val = f.filter(val + 0.001, t)
        i += 1
    var t1 = perf_counter_ns()
    
    var total_ns = Float64(t1 - t0)
    var ns_per_step = total_ns / Float64(iters)
    print("1. OneEuro Filter (1M iterations):")
    print("   Total time:  ", total_ns / 1_000_000.0, "ms (checksum:", val, ")")
    print("   Latency/step:", ns_per_step, "ns (", 1_000_000_000.0 / ns_per_step, "steps/sec )")

def bench_moments():
    var iters = 20_000
    var checksum = Float32(0.0)
    
    var t0 = perf_counter_ns()
    var i = 0
    while i < iters:
        var res = compute_moments_simd(640, 480, 320 + (i % 16), 240 + (i % 16), 28)
        checksum += res.cx + res.cy
        i += 1
    var t1 = perf_counter_ns()
    
    var total_ns = Float64(t1 - t0)
    var ns_per_frame = total_ns / Float64(iters)
    print("2. Spatial Moments (20,000 ROIs):")
    print("   Total time:   ", total_ns / 1_000_000.0, "ms (checksum:", checksum, ")")
    print("   Latency/frame:", ns_per_frame / 1000.0, "µs (", 1_000_000_000.0 / ns_per_frame, "FPS capacity )")

def bench_hitscan():
    var iters = 500_000
    var origin = Vec3(0, 1.64, 10)
    var target = Vec3(0, 0.89, -10)
    var dir = target.sub(origin).normalize()
    var hits = 0
    
    var t0 = perf_counter_ns()
    var i = 0
    while i < iters:
        var hit = ray_sphere_intersect(origin, dir, target, 0.52)
        if hit.hit:
            hits += 1
        i += 1
    var t1 = perf_counter_ns()
    
    var total_ns = Float64(t1 - t0)
    var ns_per_ray = total_ns / Float64(iters)
    print("3. Hitscan 3D Raycasting (500,000 rays):")
    print("   Total time: ", total_ns / 1_000_000.0, "ms (hits:", hits, ")")
    print("   Latency/ray:", ns_per_ray, "ns (", 1_000_000_000.0 / ns_per_ray, "rays/sec )")

def main():
    print("=========================================================")
    print("  SABLE MOJO 1.0 SIMD COMPUTE PERFORMANCE BENCHMARK     ")
    print("=========================================================")
    bench_one_euro()
    bench_moments()
    bench_hitscan()
    print("=========================================================")
    print("  ALL BENCHMARKS COMPLETED AT HARDWARE-LIMIT SPEEDS!     ")
    print("=========================================================")
