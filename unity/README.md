# SABLE Unity

Engine: **Unity 2022.3 LTS**. Webcam aim uses Hydrargyrum Games’ luma tracker (MPL-2.0). Credit: Hydrargyrum Games.

This machine did not have the Unity Editor. Install Unity Hub, add **2022.3 LTS**, open this `unity/` folder.

## Scene

1. Add `HgTracker` from `Assets/Plugins/HgWebcamObjectTracking`.
2. Assign the included compute shader + visualizer material.
3. Put `AimBus`, `HgAimSource`, `HidFire`, `RangeLoop` on a bootstrap object.
4. Eyedropper a luma **different from the desk**. A black Superlight on a dark mat will not lock — that is luma tracking, not a missing neural net.
5. Play. T = desktop debug. Space = force gun. Click peeks `AimSample`.

## Why Unity, not Unreal

Hg’s tracker is Unity compute shaders. Unreal is not on this box and is a 50–100 GB install for no gain on the gun. Godot is gone on this branch.
