#pragma once

#include <cstdint>
#include <vector>

namespace sable {

enum class PixelFormat {
	Gray8,
	Rgb24,
	Bgr24,
	Bgra32,
	Yuy2,
};

struct ImageView {
	const std::uint8_t* data = nullptr;
	int width = 0;
	int height = 0;
	int stride = 0;
	PixelFormat format = PixelFormat::Gray8;
	std::int64_t t_hw = 0;
};

struct Roi {
	int x = 0;
	int y = 0;
	int w = 0;
	int h = 0;

	bool empty() const { return w <= 0 || h <= 0; }
};

inline Roi clamp_roi(Roi r, int width, int height) {
	if (r.x < 0) {
		r.w += r.x;
		r.x = 0;
	}
	if (r.y < 0) {
		r.h += r.y;
		r.y = 0;
	}
	if (r.x + r.w > width) {
		r.w = width - r.x;
	}
	if (r.y + r.h > height) {
		r.h = height - r.y;
	}
	if (r.w < 0) {
		r.w = 0;
	}
	if (r.h < 0) {
		r.h = 0;
	}
	return r;
}

inline Roi make_roi_around(float cx, float cy, float radius, int width, int height) {
	const float r = radius;
	Roi out;
	out.x = static_cast<int>(cx - r);
	out.y = static_cast<int>(cy - r);
	out.w = static_cast<int>(r * 2.0f + 1.0f);
	out.h = static_cast<int>(r * 2.0f + 1.0f);
	return clamp_roi(out, width, height);
}

struct FrameBuffer {
	std::vector<std::uint8_t> bytes;
	int width = 0;
	int height = 0;
	int stride = 0;
	PixelFormat format = PixelFormat::Rgb24;
	std::int64_t t_hw = 0;

	ImageView view() const {
		ImageView v;
		v.data = bytes.empty() ? nullptr : bytes.data();
		v.width = width;
		v.height = height;
		v.stride = stride;
		v.format = format;
		v.t_hw = t_hw;
		return v;
	}
};

} // namespace sable
