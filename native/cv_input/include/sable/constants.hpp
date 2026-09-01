#pragma once

namespace sable {

// One Euro (Casiez, Roussel, Vogel 2012). Tuned for physical pointing
// at a monitor, not for smoothing an OS mouse.
constexpr float kOneEuroMincutoffHz = 1.0f;
constexpr float kOneEuroBeta = 0.007f;
constexpr float kOneEuroDcutoffHz = 1.0f;
constexpr float kOneEuroFallbackHz = 30.0f;

// Coast missing blobs this long, then drop valid and hold last UV.
constexpr float kCoastMs = 100.0f;

// ROI is ~3x measured blob radius around the predicted centroid.
constexpr float kRoiRadiusScale = 3.0f;
constexpr float kRoiMinPx = 16.0f;

// Jump vs prediction (rolling shutter / AE pop). One ignore, then relock.
constexpr float kOutlierJumpPx = 28.0f;
constexpr int kOutlierRejectsBeforeRelock = 2;

// Quality floor. Below this the Range chip is SEEKING.
constexpr float kSeekingConfidence = 0.35f;

// Re-estimate luma/HSV floors this often when AE could not be locked.
constexpr int kAdaptEveryNFrames = 15;

// Soft-mask floors for a calibrated neon/dot sample.
constexpr float kHueTolDeg = 28.0f;
constexpr float kMinSat = 0.28f;
constexpr float kMinVal = 0.28f;
constexpr float kLowSatFallback = 0.18f;

// Lift: blob area jump vs pad baseline, plus HID idle from the caller.
constexpr float kLiftAreaScale = 1.45f;
constexpr float kLiftHysteresisMs = 110.0f;

// HID idle window used with the camera lift signal.
constexpr float kHidIdleMsMin = 15.0f;
constexpr float kHidIdleMsMax = 30.0f;

} // namespace sable
