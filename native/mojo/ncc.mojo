"""NCC — SIMD normalized cross-correlation for muzzle lock."""

from std.sys.info import simd_width_of
from std.math import sqrt

comptime SW = simd_width_of[DType.float32]()


@fieldwise_init
struct NccHit(Copyable, Movable, ImplicitlyCopyable):
    var score: Float32
    var x: Int
    var y: Int


def ncc_at(
    gray: List[Float32],
    iw: Int,
    tpl: List[Float32],
    tw: Int,
    th: Int,
    tlx: Int,
    tly: Int,
) -> Float32:
    """Score one patch. tw should be a multiple of SIMD width when possible."""
    var sI = SIMD[DType.float32, SW](0)
    var sI2 = SIMD[DType.float32, SW](0)
    var sT = SIMD[DType.float32, SW](0)
    var sT2 = SIMD[DType.float32, SW](0)
    var dotv = SIMD[DType.float32, SW](0)
    var n_scalar = 0
    var sI_s = Float32(0)
    var sI2_s = Float32(0)
    var sT_s = Float32(0)
    var sT2_s = Float32(0)
    var dot_s = Float32(0)

    var y = 0
    while y < th:
        var grow = (tly + y) * iw + tlx
        var trow = y * tw
        var x = 0
        while x + SW <= tw:
            var iv = SIMD[DType.float32, SW](0)
            var tv = SIMD[DType.float32, SW](0)
            var k = 0
            while k < SW:
                iv[k] = gray[grow + x + k]
                tv[k] = tpl[trow + x + k]
                k += 1
            sI = sI + iv
            sI2 = sI2 + iv * iv
            sT = sT + tv
            sT2 = sT2 + tv * tv
            dotv = dotv + iv * tv
            x += SW
        while x < tw:
            var ivs = gray[grow + x]
            var tvs = tpl[trow + x]
            sI_s += ivs
            sI2_s += ivs * ivs
            sT_s += tvs
            sT2_s += tvs * tvs
            dot_s += ivs * tvs
            n_scalar += 1
            x += 1
        y += 1

    var n = Float32(tw * th)
    var sumI = sI.reduce_add() + sI_s
    var sumI2 = sI2.reduce_add() + sI2_s
    var sumT = sT.reduce_add() + sT_s
    var sumT2 = sT2.reduce_add() + sT2_s
    var dot = dotv.reduce_add() + dot_s
    var num = n * dot - sumI * sumT
    var denI = n * sumI2 - sumI * sumI
    var denT = n * sumT2 - sumT * sumT
    if denI < 1e-4 or denT < 1e-4:
        return -1.0
    return num / sqrt(denI * denT)


def ncc_search(
    gray: List[Float32],
    iw: Int,
    ih: Int,
    tpl: List[Float32],
    tw: Int,
    th: Int,
    x0: Int,
    y0: Int,
    x1: Int,
    y1: Int,
    stride: Int,
) -> NccHit:
    """Coarse-to-fine peak. Stride > 1 then refine ±stride."""
    var max_x = iw - tw
    var max_y = ih - th
    var xa = x0 if x0 > 0 else 0
    var ya = y0 if y0 > 0 else 0
    var xb = x1 if x1 < max_x else max_x
    var yb = y1 if y1 < max_y else max_y
    if xa > xb:
        var t = xa
        xa = xb
        xb = t
    if ya > yb:
        var t2 = ya
        ya = yb
        yb = t2
    var st = stride if stride >= 1 else 1
    var best = Float32(-2.0)
    var bx = xa
    var by = ya
    var y = ya
    while y <= yb:
        var x = xa
        while x <= xb:
            var s = ncc_at(gray, iw, tpl, tw, th, x, y)
            if s > best:
                best = s
                bx = x
                by = y
            x += st
        y += st
    if st > 1:
        var rx0 = bx - st if bx - st > 0 else 0
        var ry0 = by - st if by - st > 0 else 0
        var rx1 = bx + st if bx + st < max_x else max_x
        var ry1 = by + st if by + st < max_y else max_y
        var yy = ry0
        while yy <= ry1:
            var xx = rx0
            while xx <= rx1:
                var s2 = ncc_at(gray, iw, tpl, tw, th, xx, yy)
                if s2 > best:
                    best = s2
                    bx = xx
                    by = yy
                xx += 1
            yy += 1
    return NccHit(best, bx, by)


def make_blob_frame(w: Int, h: Int, cx: Int, cy: Int, radius: Int) -> List[Float32]:
    var gray = List[Float32]()
    var y = 0
    while y < h:
        var x = 0
        while x < w:
            var dx = x - cx
            var dy = y - cy
            var d2 = dx * dx + dy * dy
            var r2 = radius * radius
            var v = Float32(12.0)
            if d2 <= r2:
                v = Float32(220.0) - Float32(d2) * (180.0 / Float32(r2 + 1))
            gray.append(v)
            x += 1
        y += 1
    return gray^


def extract_tpl(gray: List[Float32], iw: Int, tlx: Int, tly: Int, tw: Int, th: Int) -> List[Float32]:
    var tpl = List[Float32]()
    var y = 0
    while y < th:
        var x = 0
        while x < tw:
            tpl.append(gray[(tly + y) * iw + tlx + x])
            x += 1
        y += 1
    return tpl^


def main():
    var w = 160
    var h = 90
    var tw = 16
    var cx = 80
    var cy = 45
    var gray = make_blob_frame(w, h, cx, cy, 10)
    var tpl = extract_tpl(gray, w, cx - tw // 2, cy - tw // 2, tw, tw)
    var hit = ncc_search(gray, w, h, tpl, tw, tw, 0, 0, w - tw, h - tw, 4)
    print("SIMD NCC peak", hit.score, "at", hit.x, hit.y)
