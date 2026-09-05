# SABLE art — from paint to mesh

First-party only. Palette is CANCHO: charcoal, bone, mint, rust.

```
art/concepts/*.svg   paint / ortho sheets
art/blender/*.py     rebuild + render in Blender (optional)
proto/game.js        runtime meshes (must match the sheets)
```

Open a sheet in any browser. Open `build_sable_kit.py` in Blender 4.x: Scripting → Run. Exports GLB next to the script when bpy is present.

Do not import third-party game FBX, Marketplace packs, or scans.
