"""Test_aim.mojo — Comprehensive unit tests in Mojo 1.0."""

from aim_sample import AimSample
from aim_bus import AimBus
from one_euro import OneEuro
from moments import compute_moments_simd
from hitscan import Vec3, ray_sphere_intersect, batch_sphere_hits
from ncc import ncc_search, make_blob_frame, extract_tpl

def check(cond: Bool, msg: String) raises:
    if not cond:
        print("FAIL:", msg)
        raise Error(msg)
    else:
        print("ok  ", msg)

def test_aim_sample() raises:
    var s1 = AimSample(0.5, 0.5, True, True, 0.95, 42)
    var s2 = AimSample(0.5, 0.5, True, True, 0.95, 42)
    var s3 = AimSample(0.1, 0.2, False, False, 0.0, 0)
    check(s1.is_equal(s2), "AimSample equality matches")
    check(not s1.is_equal(s3), "AimSample inequality works")

def test_aim_bus() raises:
    var bus = AimBus()
    var init = bus.peek()
    check(not init.valid, "AimBus starts invalid")
    
    var s = AimSample(0.33, 0.66, True, True, 0.99, 12345)
    bus.publish(s)
    
    var peeked = bus.peek()
    check(peeked.is_equal(s), "AimBus.peek returns latest sample")
    
    var shot = bus.fire()
    check(shot.is_equal(s), "AimBus.fire returns latest sample")
    check(shot.t_hw == 12345, "AimBus.fire preserves hardware timestamp")

def test_one_euro() raises:
    var f = OneEuro(3.0, 0.03, 1.0, 60.0)
    var out1 = f.filter(100.0, 0.016)
    var out2 = f.filter(100.0, 0.032)
    var out3 = f.filter(100.0, 0.048)
    check(out1 == 100.0, "OneEuro seeds with initial value")
    check(out2 == 100.0 and out3 == 100.0, "OneEuro holds constant signal")
    
    # Step change
    var step_out = f.filter(110.0, 0.064)
    check(step_out > 100.0 and step_out < 110.0, "OneEuro filters step change smoothly")

def test_moments() raises:
    var res = compute_moments_simd(640, 480, 320, 240, 24)
    check(res.found, "Moments finds synthetic blob")
    check(res.cx > 319.9 and res.cx < 320.1, "Moments centroid X sub-pixel accurate")
    check(res.cy > 239.9 and res.cy < 240.1, "Moments centroid Y sub-pixel accurate")

def test_hitscan() raises:
    var origin = Vec3(0, 1.64, 10)
    var target = Vec3(0, 0.89, -10)
    var dir = target.sub(origin).normalize()
    var hit = ray_sphere_intersect(origin, dir, target, 0.52)
    check(hit.hit, "Hitscan direct ray hits sphere")
    check(hit.distance > 19.0 and hit.distance < 20.0, "Hitscan distance accurate")
    
    var miss_dir = Vec3(1, 0, 0).normalize()
    var miss = ray_sphere_intersect(origin, miss_dir, target, 0.52)
    check(not miss.hit, "Hitscan orthogonal ray misses")

def test_ncc() raises:
    var w = 160
    var h = 90
    var tw = 16
    var cx = 80
    var cy = 45
    var gray = make_blob_frame(w, h, cx, cy, 10)
    var tpl = extract_tpl(gray, w, cx - tw // 2, cy - tw // 2, tw, tw)
    var hit = ncc_search(gray, w, h, tpl, tw, tw, 0, 0, w - tw, h - tw, 4)
    check(hit.score > 0.95, "SIMD NCC peak near 1.0")
    check(hit.x == cx - tw // 2, "SIMD NCC X locks template origin")
    check(hit.y == cy - tw // 2, "SIMD NCC Y locks template origin")


def test_batch_hitscan() raises:
    var origin = Vec3(0, 1.64, 10)
    var target = Vec3(0, 0.89, -10)
    var dir = target.sub(origin).normalize()
    var orbs = List[Vec3]()
    orbs.append(target)
    orbs.append(Vec3(8, 0.89, -10))
    var n = batch_sphere_hits(origin, dir, orbs, 0.52)
    check(n == 1, "Batch hitscan counts only the lined-up orb")


def main():
    print("=== SABLE Mojo 1.0 Comprehensive Suite ===")
    try:
        test_aim_sample()
        test_aim_bus()
        test_one_euro()
        test_moments()
        test_hitscan()
        test_ncc()
        test_batch_hitscan()
        print("ALL MOJO 1.0 TESTS PASSED!")
    except e:
        print("Mojo test suite failure:", e)
