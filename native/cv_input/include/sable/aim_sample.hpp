#pragma once

#include <cstdint>

namespace sable {

// Shared aim contract. No engine types. Fire always peeks this;
// it never waits for the next camera frame.
struct AimSample {
	float uv_x = 0.5f;
	float uv_y = 0.5f;
	bool valid = false;
	bool lifted = false;
	float confidence = 0.0f;
	int64_t t_hw = 0;
};

inline bool operator==(const AimSample& a, const AimSample& b) {
	return a.uv_x == b.uv_x && a.uv_y == b.uv_y && a.valid == b.valid &&
		   a.lifted == b.lifted && a.confidence == b.confidence && a.t_hw == b.t_hw;
}

} // namespace sable
