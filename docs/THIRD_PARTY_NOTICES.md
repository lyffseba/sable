# Third-party notices

SABLE first-party code is Apache-2.0. The following third-party software is used by the client or native plugins.

## MediaPipe Tasks Vision (Hand Landmarker)

Copyright (c) Google LLC and MediaPipe authors.
Apache License 2.0. https://github.com/google-ai-edge/mediapipe

Loaded at runtime (local `proto/vendor/mediapipe/` if present, else jsDelivr `@mediapipe/tasks-vision` + Google model host). Used only to read 21 hand landmarks. Not a game asset.

## Three.js

Copyright (c) 2010-2024 Three.js Authors.
Licensed under the MIT License. https://github.com/mrdoob/three.js/blob/dev/LICENSE

Vendored at `proto/vendor/three.module.js`.

## Mojo

Copyright (c) Modular Inc. and Mojo contributors.
Apache License 2.0 with LLVM exceptions. https://github.com/modular/modular

Used via Pixi (`pixi.toml`) for `native/mojo`. Not vendored.

## One Euro Filter (algorithm)

Casiez, G., Roussel, N., and Vogel, D. 2012. *1€ Filter: A Simple Speed-based Low-pass Filter for Noisy Input in Interactive Systems.* CHI 2012.

SABLE's implementations in `native/cv_input/include/sable/one_euro.hpp`, `native/mojo/one_euro.mojo`, and `proto/game.js` are original first-party code written from the published equations. They are not copies of a third-party source tree.

## OpenCV (when linked)

Copyright (c) OpenCV team.
Licensed under Apache License 2.0. Not vendored. Linked later from `native/cv_input`.

## Godot Engine (historical)

Earlier scaffolds used Godot 4.7 (MIT). Godot is no longer in this tree.

## No GPL

This project does not include GPL-licensed libraries in the client or dedicated server. Do not add any.
