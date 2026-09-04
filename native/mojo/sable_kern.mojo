"""Sable_kern — Mojo 1.0 kernels callable from Python."""

from std.python import Python, PythonObject
from std.python.bindings import PythonModuleBuilder
from std.os import abort

from one_euro import OneEuro
from moments import compute_moments_simd
from hitscan import Vec3, ray_sphere_intersect


def ping() raises -> PythonObject:
    return "sable-mojo-1.0"


def one_euro_step(args: PythonObject) raises -> PythonObject:
    """Args: [value, t_s, prev, prev_t] -> filtered float."""
    var value = Float64(py=args[0])
    var t_s = Float64(py=args[1])
    var prev = Float64(py=args[2])
    var prev_t = Float64(py=args[3])
    var f = OneEuro(3.0, 0.03, 1.0, 120.0)
    if prev_t >= 0.0:
        _ = f.filter(prev, prev_t)
    return f.filter(value, t_s)


def centroid(args: PythonObject) raises -> PythonObject:
    """Args: [width, height, blob_x, blob_y, radius] -> [cx, cy, mass, found]."""
    var r = compute_moments_simd(
        Int(py=args[0]),
        Int(py=args[1]),
        Int(py=args[2]),
        Int(py=args[3]),
        Int(py=args[4]),
    )
    var out = Python.list()
    out.append(Float64(r.cx))
    out.append(Float64(r.cy))
    out.append(Float64(r.mass))
    out.append(r.found)
    return out


def hitscan(args: PythonObject) raises -> PythonObject:
    """Args: [ox,oy,oz, dx,dy,dz, sx,sy,sz, radius] -> [hit, distance]."""
    var origin = Vec3(Float32(py=args[0]), Float32(py=args[1]), Float32(py=args[2]))
    var direction = Vec3(
        Float32(py=args[3]), Float32(py=args[4]), Float32(py=args[5])
    ).normalize()
    var center = Vec3(Float32(py=args[6]), Float32(py=args[7]), Float32(py=args[8]))
    var hit = ray_sphere_intersect(origin, direction, center, Float32(py=args[9]))
    var out = Python.list()
    out.append(hit.hit)
    out.append(Float64(hit.distance))
    return out


@export
def PyInit_sable_kern() abi("C") -> PythonObject:
    try:
        var m = PythonModuleBuilder("sable_kern")
        m.def_function[ping]("ping", docstring="Kernel identity.")
        m.def_function[one_euro_step]("one_euro_step", docstring="One Euro filter step.")
        m.def_function[centroid]("centroid", docstring="Spatial moments centroid.")
        m.def_function[hitscan]("hitscan", docstring="3D ray-sphere hitscan.")
        return m.finalize()
    except e:
        abort(String("error creating Python Mojo module: ", e))
