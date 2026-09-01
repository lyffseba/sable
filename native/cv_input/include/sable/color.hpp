#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>

#include "sable/constants.hpp"
#include "sable/image.hpp"

namespace sable {

struct Rgb {
	std::uint8_t r = 0;
	std::uint8_t g = 0;
	std::uint8_t b = 0;
};

struct Hsv {
	float h = 0.0f; // degrees [0, 360)
	float s = 0.0f; // [0, 1]
	float v = 0.0f; // [0, 1]
};

inline float hue_dist_deg(float a, float b) {
	float d = std::fabs(a - b);
	if (d > 180.0f) {
		d = 360.0f - d;
	}
	return d;
}

inline Hsv rgb_to_hsv(std::uint8_t r, std::uint8_t g, std::uint8_t b) {
	const float rf = r / 255.0f;
	const float gf = g / 255.0f;
	const float bf = b / 255.0f;
	const float maxv = std::max(rf, std::max(gf, bf));
	const float minv = std::min(rf, std::min(gf, bf));
	const float delta = maxv - minv;

	Hsv out;
	out.v = maxv;
	out.s = (maxv <= 1e-6f) ? 0.0f : (delta / maxv);

	if (delta <= 1e-6f) {
		out.h = 0.0f;
		return out;
	}
	if (maxv == rf) {
		out.h = 60.0f * std::fmod((gf - bf) / delta, 6.0f);
	} else if (maxv == gf) {
		out.h = 60.0f * (((bf - rf) / delta) + 2.0f);
	} else {
		out.h = 60.0f * (((rf - gf) / delta) + 4.0f);
	}
	if (out.h < 0.0f) {
		out.h += 360.0f;
	}
	return out;
}

inline float luma_rgb(std::uint8_t r, std::uint8_t g, std::uint8_t b) {
	return (0.2126f * r + 0.7152f * g + 0.0722f * b) / 255.0f;
}

inline bool sample_rgb(const ImageView& img, int x, int y, Rgb& out) {
	if (!img.data || x < 0 || y < 0 || x >= img.width || y >= img.height) {
		return false;
	}
	switch (img.format) {
	case PixelFormat::Gray8: {
		const std::uint8_t y8 = img.data[y * img.stride + x];
		out.r = out.g = out.b = y8;
		return true;
	}
	case PixelFormat::Rgb24: {
		const std::uint8_t* p = img.data + y * img.stride + x * 3;
		out.r = p[0];
		out.g = p[1];
		out.b = p[2];
		return true;
	}
	case PixelFormat::Bgr24: {
		const std::uint8_t* p = img.data + y * img.stride + x * 3;
		out.b = p[0];
		out.g = p[1];
		out.r = p[2];
		return true;
	}
	case PixelFormat::Yuy2: {
		const int pair = x & ~1;
		const std::uint8_t* p = img.data + y * img.stride + pair * 2;
		const std::uint8_t y8 = (x & 1) ? p[2] : p[0];
		out.r = out.g = out.b = y8;
		return true;
	}
	}
	return false;
}

inline float smooth01(float edge0, float edge1, float x) {
	if (edge1 <= edge0 + 1e-6f) {
		return x >= edge1 ? 1.0f : 0.0f;
	}
	float t = (x - edge0) / (edge1 - edge0);
	t = std::clamp(t, 0.0f, 1.0f);
	return t * t * (3.0f - 2.0f * t);
}

struct ColorGate {
	Hsv sample{};
	float hue_tol_deg = kHueTolDeg;
	float min_s = kMinSat;
	float min_v = kMinVal;
	bool luma_peak = false;
	float luma_floor = 0.55f;
};

inline ColorGate gate_from_sample(const Hsv& sample) {
	ColorGate g;
	g.sample = sample;
	g.luma_peak = sample.s < kLowSatFallback;
	g.min_s = std::min(kMinSat, sample.s * 0.55f);
	g.min_v = std::min(kMinVal, sample.v * 0.55f);
	g.luma_floor = std::max(0.40f, sample.v * 0.62f);
	return g;
}

// Soft weight in [0, 1]. HSV gate, or luma-peak when the calib sample is desaturated.
inline float mask_weight(const Rgb& rgb, const ColorGate& gate) {
	const float y = luma_rgb(rgb.r, rgb.g, rgb.b);
	if (gate.luma_peak) {
		return smooth01(gate.luma_floor, std::min(1.0f, gate.luma_floor + 0.22f), y);
	}
	const Hsv hsv = rgb_to_hsv(rgb.r, rgb.g, rgb.b);
	const float dh = hue_dist_deg(hsv.h, gate.sample.h);
	const float wh = 1.0f - smooth01(gate.hue_tol_deg * 0.65f, gate.hue_tol_deg, dh);
	const float ws = smooth01(gate.min_s * 0.75f, gate.min_s, hsv.s);
	const float wv = smooth01(gate.min_v * 0.75f, gate.min_v, hsv.v);
	return wh * ws * wv;
}

} // namespace sable
