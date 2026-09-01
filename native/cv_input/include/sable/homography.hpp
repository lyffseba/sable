#pragma once

#include <array>
#include <cmath>
#include <vector>

namespace sable {

// 3x3 row-major homography. Maps camera pixels to monitor UV.
struct Homography {
	std::array<double, 9> h = {1, 0, 0, 0, 1, 0, 0, 0, 1};

	void set_identity() { h = {1, 0, 0, 0, 1, 0, 0, 0, 1}; }

	// Uncalibrated fallback: normalize by frame size.
	void set_normalize(int width, int height) {
		const double sx = (width > 0) ? 1.0 / static_cast<double>(width) : 1.0;
		const double sy = (height > 0) ? 1.0 / static_cast<double>(height) : 1.0;
		h = {sx, 0, 0, 0, sy, 0, 0, 0, 1};
	}

	void map(double x, double y, double& u, double& v) const {
		const double w = h[6] * x + h[7] * y + h[8];
		const double iw = (std::fabs(w) < 1e-12) ? 1.0 : (1.0 / w);
		u = (h[0] * x + h[1] * y + h[2]) * iw;
		v = (h[3] * x + h[4] * y + h[5]) * iw;
	}

	double residual(double x, double y, double u, double v) const {
		double pu = 0.0;
		double pv = 0.0;
		map(x, y, pu, pv);
		const double du = pu - u;
		const double dv = pv - v;
		return std::sqrt(du * du + dv * dv);
	}
};

struct Corr {
	double x = 0.0;
	double y = 0.0;
	double u = 0.0;
	double v = 0.0;
};

// Normalized DLT from 4+ correspondences. Returns false if underdetermined.
inline bool solve_homography(const std::vector<Corr>& pts, Homography& out) {
	if (pts.size() < 4) {
		return false;
	}

	// Build 2N x 8 system for h00..h21 with h22 = 1.
	const int n = static_cast<int>(pts.size());
	std::vector<std::array<double, 9>> a(static_cast<size_t>(n * 2));
	for (int i = 0; i < n; ++i) {
		const double x = pts[static_cast<size_t>(i)].x;
		const double y = pts[static_cast<size_t>(i)].y;
		const double u = pts[static_cast<size_t>(i)].u;
		const double v = pts[static_cast<size_t>(i)].v;
		a[static_cast<size_t>(2 * i)] = {-x, -y, -1, 0, 0, 0, u * x, u * y, u};
		a[static_cast<size_t>(2 * i + 1)] = {0, 0, 0, -x, -y, -1, v * x, v * y, v};
	}

	// Gaussian elimination on the 8 unknowns using the first 8 rows when
	// possible, otherwise a tiny normal-equation solve on 8x8.
	double ata[8][8] = {};
	double atb[8] = {};
	const int rows = n * 2;
	for (int r = 0; r < rows; ++r) {
		const double br = -a[static_cast<size_t>(r)][8];
		for (int i = 0; i < 8; ++i) {
			atb[i] += a[static_cast<size_t>(r)][i] * br;
			for (int j = 0; j < 8; ++j) {
				ata[i][j] += a[static_cast<size_t>(r)][i] * a[static_cast<size_t>(r)][j];
			}
		}
	}

	// Solve ata x = atb in place (Gaussian with partial pivot).
	double m[8][9] = {};
	for (int i = 0; i < 8; ++i) {
		for (int j = 0; j < 8; ++j) {
			m[i][j] = ata[i][j];
		}
		m[i][8] = atb[i];
	}
	for (int col = 0; col < 8; ++col) {
		int piv = col;
		double best = std::fabs(m[col][col]);
		for (int r = col + 1; r < 8; ++r) {
			const double v = std::fabs(m[r][col]);
			if (v > best) {
				best = v;
				piv = r;
			}
		}
		if (best < 1e-12) {
			return false;
		}
		if (piv != col) {
			for (int j = 0; j < 9; ++j) {
				const double tmp = m[col][j];
				m[col][j] = m[piv][j];
				m[piv][j] = tmp;
			}
		}
		const double diag = m[col][col];
		for (int j = col; j < 9; ++j) {
			m[col][j] /= diag;
		}
		for (int r = 0; r < 8; ++r) {
			if (r == col) {
				continue;
			}
			const double f = m[r][col];
			for (int j = col; j < 9; ++j) {
				m[r][j] -= f * m[col][j];
			}
		}
	}

	for (int i = 0; i < 8; ++i) {
		out.h[static_cast<size_t>(i)] = m[i][8];
	}
	out.h[8] = 1.0;
	return true;
}

} // namespace sable
