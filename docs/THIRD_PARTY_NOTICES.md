# Third-party notices

SABLE game content is proprietary. The following third-party software may be used by the engine or native plugin.

## Godot Engine

Copyright (c) 2014-present Godot Engine contributors.
Copyright (c) 2007-2014 Juan Linietsky, Ariel Manzur.

Licensed under the MIT License. https://godotengine.org/license

Jolt Physics is included with Godot 4.4+ and used here as the 3D physics backend.

## Apple AVFoundation (macOS capture)

System frameworks (`AVFoundation`, `CoreMedia`, `CoreVideo`, `Foundation`). Not vendored. Linked only when building `native/cv_input` on Apple.

## OpenCV (when linked)

Copyright (c) OpenCV team.

Licensed under Apache License 2.0. Not vendored in this scaffold. Linked later from `native/cv_input`.

## One Euro Filter (algorithm)

Casiez, G., Roussel, N., and Vogel, D. 2012. *1€ Filter: A Simple Speed-based Low-pass Filter for Noisy Input in Interactive Systems.* CHI 2012.

SABLE's implementation in `native/cv_input/include/sable/one_euro.hpp` is original first-party code written from the published equations. It is not a copy of a third-party source tree.

## No GPL

This project does not include GPL-licensed libraries in the client or dedicated server. Do not add any.
