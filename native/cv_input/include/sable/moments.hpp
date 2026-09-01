#pragma once

#include <cmath>
#include <vector>

#include "sable/color.hpp"
#include "sable/constants.hpp"
#include "sable/image.hpp"

namespace sable {

struct Blob {
	float x = 0.0f;
	float y = 0.0f;
	float mass = 0.0f;
	float radius = 0.0f;
	float snr = 0.0f;
	float mu20 = 0.0f;
	float mu02 = 0.0f;
	float mu11 = 0.0f;
	bool found = false;
};

// Spatial moments on a soft mask. Sub-pixel centroid is m10/m00, m01/m00 —
// not a bounding-box center and not argmax.
inline Blob moments_centroid(const ImageView& img, const Roi& roi, const ColorGate& gate) {
	Blob out;
	const Roi r = clamp_roi(roi, img.width, img.height);
	if (r.empty() || !img.data) {
		return out;
	}

	double m00 = 0.0;
	double m10 = 0.0;
	double m01 = 0.0;
	double m20 = 0.0;
	double m02 = 0.0;
	double m11 = 0.0;
	double signal = 0.0;
	double bg = 0.0;
	int bg_n = 0;
	int sig_n = 0;

	for (int y = r.y; y < r.y + r.h; ++y) {
		for (int x = r.x; x < r.x + r.w; ++x) {
			Rgb rgb;
			if (!sample_rgb(img, x, y, rgb)) {
				continue;
			}
			const float w = mask_weight(rgb, gate);
			const float lum = luma_rgb(rgb.r, rgb.g, rgb.b);
			if (w > 0.05f) {
				const double ww = static_cast<double>(w);
				const double xf = static_cast<double>(x) + 0.5;
				const double yf = static_cast<double>(y) + 0.5;
				m00 += ww;
				m10 += ww * xf;
				m01 += ww * yf;
				m20 += ww * xf * xf;
				m02 += ww * yf * yf;
				m11 += ww * xf * yf;
				signal += lum * w;
				++sig_n;
			} else {
				bg += lum;
				++bg_n;
			}
		}
	}

	if (m00 < 2.0) {
		return out;
	}

	out.found = true;
	out.mass = static_cast<float>(m00);
	out.x = static_cast<float>(m10 / m00);
	out.y = static_cast<float>(m01 / m00);
	out.mu20 = static_cast<float>(m20 / m00 - (m10 / m00) * (m10 / m00));
	out.mu02 = static_cast<float>(m02 / m00 - (m01 / m00) * (m01 / m00));
	out.mu11 = static_cast<float>(m11 / m00 - (m10 / m00) * (m01 / m00));
	const float area_r = static_cast<float>(std::sqrt(std::max(0.0, m00 / 3.141592653589793)));
	const float moment_r = static_cast<float>(std::sqrt(std::max(0.0f, out.mu20 + out.mu02)));
	out.radius = std::max(2.0f, std::max(area_r, moment_r));

	const float mean_sig = (sig_n > 0) ? static_cast<float>(signal / std::max(1, sig_n)) : 0.0f;
	const float mean_bg = (bg_n > 0) ? static_cast<float>(bg / bg_n) : 0.0f;
	out.snr = mean_sig / std::max(0.04f, mean_bg + 0.02f);
	return out;
}

// After the primary blob, punch a hole and search again for extra dots.
inline Blob moments_centroid_excluding(const ImageView& img, const Roi& roi, const ColorGate& gate,
									   float ex, float ey, float exclude_r) {
	const float r2 = exclude_r * exclude_r;
	Blob out;
	const Roi r = clamp_roi(roi, img.width, img.height);
	if (r.empty() || !img.data) {
		return out;
	}
	double m00 = 0.0;
	double m10 = 0.0;
	double m01 = 0.0;
	double m20 = 0.0;
	double m02 = 0.0;
	double m11 = 0.0;
	double signal = 0.0;
	double bg = 0.0;
	int bg_n = 0;
	int sig_n = 0;
	for (int y = r.y; y < r.y + r.h; ++y) {
		for (int x = r.x; x < r.x + r.w; ++x) {
			const float dx = (static_cast<float>(x) + 0.5f) - ex;
			const float dy = (static_cast<float>(y) + 0.5f) - ey;
			if (dx * dx + dy * dy < r2) {
				continue;
			}
			Rgb rgb;
			if (!sample_rgb(img, x, y, rgb)) {
				continue;
			}
			const float w = mask_weight(rgb, gate);
			const float lum = luma_rgb(rgb.r, rgb.g, rgb.b);
			if (w > 0.05f) {
				const double ww = static_cast<double>(w);
				const double xf = static_cast<double>(x) + 0.5;
				const double yf = static_cast<double>(y) + 0.5;
				m00 += ww;
				m10 += ww * xf;
				m01 += ww * yf;
				m20 += ww * xf * xf;
				m02 += ww * yf * yf;
				m11 += ww * xf * yf;
				signal += lum * w;
				++sig_n;
			} else {
				bg += lum;
				++bg_n;
			}
		}
	}
	if (m00 < 2.0) {
		return out;
	}
	out.found = true;
	out.mass = static_cast<float>(m00);
	out.x = static_cast<float>(m10 / m00);
	out.y = static_cast<float>(m01 / m00);
	out.mu20 = static_cast<float>(m20 / m00 - (m10 / m00) * (m10 / m00));
	out.mu02 = static_cast<float>(m02 / m00 - (m01 / m00) * (m01 / m00));
	const float area_r = static_cast<float>(std::sqrt(std::max(0.0, m00 / 3.141592653589793)));
	const float moment_r = static_cast<float>(std::sqrt(std::max(0.0f, out.mu20 + out.mu02)));
	out.radius = std::max(2.0f, std::max(area_r, moment_r));
	const float mean_sig = (sig_n > 0) ? static_cast<float>(signal / std::max(1, sig_n)) : 0.0f;
	const float mean_bg = (bg_n > 0) ? static_cast<float>(bg / bg_n) : 0.0f;
	out.snr = mean_sig / std::max(0.04f, mean_bg + 0.02f);
	return out;
}

inline float heading_deg(const std::vector<Blob>& dots) {
	if (dots.size() < 2) {
		return 0.0f;
	}
	double mx = 0.0;
	double my = 0.0;
	for (const Blob& b : dots) {
		mx += b.x;
		my += b.y;
	}
	mx /= static_cast<double>(dots.size());
	my /= static_cast<double>(dots.size());
	double sxx = 0.0;
	double syy = 0.0;
	double sxy = 0.0;
	for (const Blob& b : dots) {
		const double dx = b.x - mx;
		const double dy = b.y - my;
		sxx += dx * dx;
		syy += dy * dy;
		sxy += dx * dy;
	}
	return static_cast<float>(std::atan2(2.0 * sxy, sxx - syy) * 90.0 / 3.141592653589793);
}

} // namespace sable
