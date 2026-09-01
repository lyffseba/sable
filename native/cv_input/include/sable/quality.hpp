#pragma once

#include <algorithm>
#include <cmath>

#include "sable/constants.hpp"
#include "sable/moments.hpp"

namespace sable {

inline float quality_confidence(const Blob& blob, float reproj_residual, int frame_w, int frame_h) {
	if (!blob.found) {
		return 0.0f;
	}
	const float area_norm = static_cast<float>(frame_w * frame_h);
	const float area_frac = blob.mass / std::max(1.0f, area_norm);
	// Healthy neon sleeve at 720p occupies a small patch, not a flood.
	float area_q = 0.0f;
	if (area_frac > 0.00015f && area_frac < 0.08f) {
		area_q = 1.0f;
	} else if (area_frac >= 0.08f && area_frac < 0.18f) {
		area_q = 0.45f;
	} else if (area_frac >= 0.00005f) {
		area_q = 0.35f;
	}

	const float snr_q = std::clamp((blob.snr - 1.1f) / 3.0f, 0.0f, 1.0f);
	const float resid_q = std::clamp(1.0f - reproj_residual / 0.08f, 0.0f, 1.0f);

	const float q = 0.45f * snr_q + 0.35f * area_q + 0.20f * resid_q;
	return std::clamp(q, 0.0f, 1.0f);
}

inline bool is_seeking(float confidence, bool valid) {
	return !valid || confidence < kSeekingConfidence;
}

} // namespace sable
