"""Hitscan — Vectorized 3D raycasting in Mojo 1.0."""

from std.math import sqrt

@fieldwise_init
struct Vec3(Copyable, Movable, ImplicitlyCopyable):
    var x: Float32
    var y: Float32
    var z: Float32

    def dot(self, other: Vec3) -> Float32:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def length(self) -> Float32:
        return sqrt(self.dot(self))

    def normalize(self) -> Vec3:
        var l = self.length()
        if l < 1e-6:
            return Vec3(0, 0, 0)
        var inv = 1.0 / l
        return Vec3(self.x * inv, self.y * inv, self.z * inv)

    def sub(self, other: Vec3) -> Vec3:
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def add(self, other: Vec3) -> Vec3:
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def scale(self, s: Float32) -> Vec3:
        return Vec3(self.x * s, self.y * s, self.z * s)

@fieldwise_init
struct RayHit(Copyable, Movable, ImplicitlyCopyable):
    var hit: Bool
    var distance: Float32
    var point: Vec3

def ray_sphere_intersect(
    ray_origin: Vec3,
    ray_dir: Vec3,
    sphere_center: Vec3,
    radius: Float32
) -> RayHit:
    var oc = ray_origin.sub(sphere_center)
    var b = 2.0 * oc.dot(ray_dir)
    var c = oc.dot(oc) - radius * radius
    var disc = b * b - 4.0 * c
    if disc < 0.0:
        return RayHit(False, 0.0, Vec3(0, 0, 0))

    var t = (-b - sqrt(disc)) * 0.5
    if t > 0.0:
        var pt = ray_origin.add(ray_dir.scale(t))
        return RayHit(True, t, pt)

    return RayHit(False, 0.0, Vec3(0, 0, 0))


def batch_sphere_hits(
    origin: Vec3,
    ray_dir: Vec3,
    targets: List[Vec3],
    radius: Float32,
) -> Int:
    """Count hits against a target list (arena tick)."""
    var n = 0
    var i = 0
    var count = len(targets)
    while i < count:
        var h = ray_sphere_intersect(origin, ray_dir, targets[i], radius)
        if h.hit:
            n += 1
        i += 1
    return n


def main():
    var origin = Vec3(0, 1.64, 10)
    var target = Vec3(0, 0.89, -10)
    var dir = target.sub(origin).normalize()
    var hit = ray_sphere_intersect(origin, dir, target, 0.52)
    print("Mojo Hitscan test: hit=", hit.hit, "distance=", hit.distance)
