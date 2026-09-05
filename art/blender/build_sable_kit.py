#!/usr/bin/env python3
"""Rebuild SABLE kit in Blender from the paint sheets. First-party only.

Run inside Blender 4.x:
    blender --background --python art/blender/build_sable_kit.py

Or Scripting workspace → Open → Run Script.
"""

from __future__ import annotations

from pathlib import Path

MINT = (0.35, 0.95, 0.78, 1.0)
BONE = (0.90, 0.88, 0.82, 1.0)
RUST = (0.55, 0.28, 0.18, 1.0)
CHAR = (0.06, 0.07, 0.08, 1.0)


def _blender() -> None:
    import bpy

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    def mat(name: str, col: tuple) -> object:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = col
            bsdf.inputs["Roughness"].default_value = 0.62
        return m

    mint, bone, rust, char = mat("mint", MINT), mat("bone", BONE), mat("rust", RUST), mat("char", CHAR)

    def cube(name, loc, scale, material):
        bpy.ops.mesh.primitive_cube_add(location=loc)
        ob = bpy.context.active_object
        ob.name = name
        ob.scale = scale
        ob.data.materials.append(material)
        return ob

    cube("cuff", (0, 0, 0.08), (0.045, 0.04, 0.03), rust)
    cube("palm", (0, 0.01, 0.0), (0.05, 0.035, 0.06), bone)
    cube("rail", (0, 0.03, -0.08), (0.012, 0.008, 0.09), mint)
    cube("index", (0, 0.012, -0.12), (0.014, 0.014, 0.07), char)

    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.55, depth=0.07, location=(4, 0, 1.2))
    plate = bpy.context.active_object
    plate.name = "plate"
    plate.data.materials.append(bone)

    bpy.ops.mesh.primitive_cube_add(location=(0, -8, 0))
    hall = bpy.context.active_object
    hall.name = "backstop"
    hall.scale = (8, 0.2, 3)
    hall.data.materials.append(rust)

    out = Path(__file__).resolve().parent / "sable_kit.glb"
    bpy.ops.export_scene.gltf(filepath=str(out), export_format="GLB")
    print("wrote", out)


if __name__ == "__main__":
    try:
        _blender()
    except ImportError:
        print("Run this script inside Blender 4.x (bpy not in this Python).")
