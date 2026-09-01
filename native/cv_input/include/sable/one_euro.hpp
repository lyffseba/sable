#pragma once

#include <cmath>

#include "sable/constants.hpp"

namespace sable {

// First-order low-pass with time-varying alpha (Casiez 2012 eq. 1 / 6).
class LowPass {
public:
	void reset(double init = 0.0) {
		hat_ = init;
		initialized_ = false;
	}

	double filter(double value, double alpha) {
		if (!initialized_) {
			hat_ = value;
			initialized_ = true;
			return hat_;
		}
		if (alpha < 0.0) {
			alpha = 0.0;
		}
		if (alpha > 1.0) {
			alpha = 1.0;
		}
		hat_ = alpha * value + (1.0 - alpha) * hat_;
		return hat_;
	}

	double hat() const { return hat_; }
	bool initialized() const { return initialized_; }

private:
	double hat_ = 0.0;
	bool initialized_ = false;
};

// 1€ filter on a scalar. Cutoff rises with |filtered derivative|.
class OneEuro {
public:
	explicit OneEuro(double mincutoff = kOneEuroMincutoffHz,
					 double beta = kOneEuroBeta,
					 double dcutoff = kOneEuroDcutoffHz,
					 double freq = kOneEuroFallbackHz)
		: mincutoff_(mincutoff), beta_(beta), dcutoff_(dcutoff), freq_(freq) {}

	void reset() {
		x_.reset();
		dx_.reset();
		last_t_s_ = -1.0;
	}

	double filter(double value, double t_s) {
		double te = 1.0 / freq_;
		if (last_t_s_ >= 0.0 && t_s > last_t_s_) {
			te = t_s - last_t_s_;
		}
		if (te <= 1e-6) {
			te = 1.0 / freq_;
		}
		const double freq = 1.0 / te;

		double dx = 0.0;
		if (x_.initialized()) {
			dx = (value - x_.hat()) * freq;
		}
		const double edx = dx_.filter(dx, alpha(dcutoff_, te));
		const double cutoff = mincutoff_ + beta_ * std::fabs(edx);
		const double hat = x_.filter(value, alpha(cutoff, te));
		last_t_s_ = t_s;
		return hat;
	}

	double hat() const { return x_.hat(); }

private:
	static double alpha(double cutoff, double te) {
		const double tau = 1.0 / (2.0 * 3.14159265358979323846 * cutoff);
		return 1.0 / (1.0 + tau / te);
	}

	double mincutoff_;
	double beta_;
	double dcutoff_;
	double freq_;
	LowPass x_;
	LowPass dx_;
	double last_t_s_ = -1.0;
};

class OneEuro2 {
public:
	void reset() {
		x_.reset();
		y_.reset();
	}

	void filter(double x, double y, double t_s, double& ox, double& oy) {
		ox = x_.filter(x, t_s);
		oy = y_.filter(y, t_s);
	}

	void hat(double& ox, double& oy) const {
		ox = x_.hat();
		oy = y_.hat();
	}

private:
	OneEuro x_;
	OneEuro y_;
};

} // namespace sable
