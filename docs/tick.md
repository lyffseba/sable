# Tick

Simulation is **64 Hz**. Render is decoupled (`physics_interpolation` on).

- Gameplay, lift FSM HID half, and hitscan resolution belong in physics ticks or in the input event that already carries the sample.
- Camera capture is asynchronous. It publishes `AimSample` whenever a frame finishes.
- Fire is an HID event. It peeks the latest sample and does not wait for the next 64 Hz tick *or* the next camera frame to choose a UV.

Dedicated server boots headless at the same tick rate.
