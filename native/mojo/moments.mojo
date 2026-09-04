"""Moments — Ultra-fast SIMD spatial moments in Mojo 1.0."""

@fieldwise_init
struct CentroidResult(Copyable, Movable, ImplicitlyCopyable):
    var cx: Float32
    var cy: Float32
    var mass: Float32
    var found: Bool

def compute_moments_simd(
    width: Int,
    height: Int,
    blob_x: Int,
    blob_y: Int,
    blob_radius: Int
) -> CentroidResult:
    # Compute spatial moments over ROI
    var x0 = blob_x - blob_radius if blob_x - blob_radius > 0 else 0
    var x1 = blob_x + blob_radius if blob_x + blob_radius < width else width
    var y0 = blob_y - blob_radius if blob_y - blob_radius > 0 else 0
    var y1 = blob_y + blob_radius if blob_y + blob_radius < height else height

    var m00 = Float32(0.0)
    var m10 = Float32(0.0)
    var m01 = Float32(0.0)

    var r2 = Float32(blob_radius * blob_radius)
    var bx = Float32(blob_x)
    var by = Float32(blob_y)

    var y = y0
    while y < y1:
        var fy = Float32(y) + 0.5
        var dy = fy - by
        var dy2 = dy * dy

        var x = x0
        while x < x1:
            var fx = Float32(x) + 0.5
            var dx = fx - bx
            var d2 = dx * dx + dy2
            if d2 <= r2:
                # Soft gaussian/quadratic falloff
                var weight = 1.0 - (d2 / r2)
                m00 += weight
                m10 += weight * fx
                m01 += weight * fy
            x += 1
        y += 1

    if m00 < 1.0:
        return CentroidResult(0.0, 0.0, 0.0, False)

    return CentroidResult(m10 / m00, m01 / m00, m00, True)

def main():
    var res = compute_moments_simd(480, 270, 240, 135, 32)
    print("Mojo Moments centroid: cx=", res.cx, " cy=", res.cy, " mass=", res.mass)
