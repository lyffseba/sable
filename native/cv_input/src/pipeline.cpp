#include "sable/pipeline.hpp"

#include <algorithm>
#include <cmath>

#include "sable/quality.hpp"

namespace sable {
namespace {

float dt_from_hw(std::int64_t t_hw, std::int64_t last_t) {
	if (last_t <= 0 || t_hw <= last_t) {
		return 1.0f / kOneEuroFallbackHz;
	}
	return static_cast<float>(t_hw - last_t) * 1e-6f;
}

float clampf(float v, float lo, float hi) { return std::max(lo, std::min(hi, v)); }

} // namespace

AimPipeline::AimPipeline(PipelineConfig cfg) : cfg_(cfg) {
	reset();
}

void AimPipeline::reset() {
	euro_.reset();
	H_.set_identity();
	gate_ = ColorGate{};
	gate_.luma_peak = true;
	gate_.luma_floor = 0.55f;
	have_calib_ = false;
	state_ = TrackState::Lost;
	filt_x_ = 0.0f;
	filt_y_ = 0.0f;
	vel_x_ = 0.0f;
	vel_y_ = 0.0f;
	last_uv_x_ = 0.5f;
	last_uv_y_ = 0.5f;
	last_conf_ = 0.0f;
	radius_ = 18.0f;
	pad_area_ = 0.0f;
	lift_ms_ = 0.0f;
	rejects_ = 0;
	frame_i_ = 0;
	last_blob_t_ = 0;
	last_t_ = 0;
	have_filt_ = false;
	debug_ = {};
	AimSample blank;
	blank.uv_x = 0.5f;
	blank.uv_y = 0.5f;
	bus_.publish(blank);
}

void AimPipeline::set_calib_hsv(const Hsv& sample) {
	gate_ = gate_from_sample(sample);
	have_calib_ = true;
}

void AimPipeline::set_homography(const Homography& h) { H_ = h; }

void AimPipeline::set_normalize(int width, int height) { H_.set_normalize(width, height); }

ColorGate AimPipeline::effective_gate() const { return gate_; }

void AimPipeline::adapt_gate(const ImageView& frame, const Roi& roi) {
	if (exposure_locked_) {
		return;
	}
	if (cfg_.adapt_every <= 0 || (frame_i_ % cfg_.adapt_every) != 0) {
		return;
	}
	const Roi r = clamp_roi(roi, frame.width, frame.height);
	if (r.empty()) {
		return;
	}
	std::vector<float> lumas;
	lumas.reserve(static_cast<size_t>(r.w * r.h / 4));
	for (int y = r.y; y < r.y + r.h; y += 2) {
		for (int x = r.x; x < r.x + r.w; x += 2) {
			Rgb rgb;
			if (!sample_rgb(frame, x, y, rgb)) {
				continue;
			}
			lumas.push_back(luma_rgb(rgb.r, rgb.g, rgb.b));
		}
	}
	if (lumas.empty()) {
		return;
	}
	std::sort(lumas.begin(), lumas.end());
	const float p90 = lumas[static_cast<size_t>(lumas.size() * 0.90)];
	gate_.luma_floor = clampf(p90 + 0.12f, 0.35f, 0.85f);
	gate_.min_v = clampf(p90 + 0.08f, 0.20f, 0.80f);
}

void AimPipeline::publish_hold(std::int64_t t_hw) {
	AimSample s = bus_.peek();
	s.uv_x = last_uv_x_;
	s.uv_y = last_uv_y_;
	s.valid = false;
	s.confidence = std::min(s.confidence, kSeekingConfidence * 0.5f);
	s.t_hw = t_hw;
	apply_lift(s, Blob{}, 0.0f);
	bus_.publish(s);
	debug_.seeking = true;
	debug_.state = TrackState::Lost;
}

void AimPipeline::apply_lift(AimSample& sample, const Blob& blob, float dt_s) {
	const float dt_ms = dt_s * 1000.0f;
	bool cam_lift = false;
	if (blob.found) {
		if (pad_area_ <= 1.0f) {
			pad_area_ = blob.mass;
		} else if (!sample.lifted) {
			pad_area_ = pad_area_ * 0.95f + blob.mass * 0.05f;
		}
		cam_lift = blob.mass > pad_area_ * kLiftAreaScale;
	}
	const bool want = hid_idle_ && cam_lift;
	if (want) {
		lift_ms_ += dt_ms;
	} else {
		lift_ms_ -= dt_ms;
	}
	lift_ms_ = clampf(lift_ms_, 0.0f, kLiftHysteresisMs * 2.0f);
	sample.lifted = lift_ms_ >= kLiftHysteresisMs;
	debug_.hid_idle = hid_idle_;
}

AimSample AimPipeline::process_missing(std::int64_t t_hw, float dt_s) {
	if (dt_s <= 0.0f) {
		dt_s = 1.0f / kOneEuroFallbackHz;
	}
	const float since_ms =
		(last_blob_t_ > 0) ? static_cast<float>(t_hw - last_blob_t_) * 1e-3f : 1e9f;

	AimSample sample;
	sample.t_hw = t_hw;
	sample.uv_x = last_uv_x_;
	sample.uv_y = last_uv_y_;
	sample.lifted = bus_.peek().lifted;

	if (have_filt_ && since_ms <= cfg_.coast_ms) {
		state_ = TrackState::Coasting;
		filt_x_ += vel_x_ * dt_s;
		filt_y_ += vel_y_ * dt_s;
		double u = last_uv_x_;
		double v = last_uv_y_;
		H_.map(filt_x_, filt_y_, u, v);
		last_uv_x_ = clampf(static_cast<float>(u), 0.0f, 1.0f);
		last_uv_y_ = clampf(static_cast<float>(v), 0.0f, 1.0f);
		last_conf_ *= std::exp(-dt_s / 0.085f);
		sample.uv_x = last_uv_x_;
		sample.uv_y = last_uv_y_;
		sample.confidence = last_conf_;
		sample.valid = last_conf_ >= cfg_.seeking_confidence;
	} else {
		state_ = TrackState::Lost;
		sample.valid = false;
		sample.confidence = std::min(last_conf_, cfg_.seeking_confidence * 0.5f);
		// Hold last UV. Never snap to 0,0.
		sample.uv_x = last_uv_x_;
		sample.uv_y = last_uv_y_;
	}

	apply_lift(sample, Blob{}, dt_s);
	debug_.state = state_;
	debug_.cam_x = filt_x_;
	debug_.cam_y = filt_y_;
	debug_.vel_x = vel_x_;
	debug_.vel_y = vel_y_;
	debug_.seeking = is_seeking(sample.confidence, sample.valid);
	debug_.rejects = rejects_;
	bus_.publish(sample);
	last_t_ = t_hw;
	return sample;
}

AimSample AimPipeline::process(const ImageView& frame) {
	++frame_i_;
	const float dt = dt_from_hw(frame.t_hw, last_t_);
	const double t_s = (frame.t_hw > 0) ? (static_cast<double>(frame.t_hw) * 1e-6)
										: (static_cast<double>(frame_i_) / kOneEuroFallbackHz);

	if (H_.h[0] == 1.0 && H_.h[4] == 1.0 && H_.h[8] == 1.0 && frame.width > 0) {
		H_.set_normalize(frame.width, frame.height);
	}

	const float pred_x = have_filt_ ? (filt_x_ + vel_x_ * dt) : (frame.width * 0.5f);
	const float pred_y = have_filt_ ? (filt_y_ + vel_y_ * dt) : (frame.height * 0.5f);

	Roi roi;
	if (state_ == TrackState::Lost || !have_filt_) {
		roi = Roi{0, 0, frame.width, frame.height};
	} else {
		const float rad = std::max(kRoiMinPx, radius_ * cfg_.roi_scale);
		roi = make_roi_around(pred_x, pred_y, rad, frame.width, frame.height);
	}

	adapt_gate(frame, roi);
	const ColorGate gate = effective_gate();
	Blob primary = moments_centroid(frame, roi, gate);

	// If the locked ROI missed, one full-frame search before declaring a hole.
	if (!primary.found && state_ != TrackState::Lost) {
		primary = moments_centroid(frame, Roi{0, 0, frame.width, frame.height}, gate);
	}

	if (!primary.found) {
		return process_missing(frame.t_hw, dt);
	}

	const float jx = primary.x - pred_x;
	const float jy = primary.y - pred_y;
	const float jump = std::sqrt(jx * jx + jy * jy);
	if (have_filt_ && jump > cfg_.outlier_jump_px) {
		++rejects_;
		if (rejects_ >= cfg_.outlier_relock) {
			state_ = TrackState::Lost;
			have_filt_ = false;
			rejects_ = 0;
			euro_.reset();
		}
		return process_missing(frame.t_hw, dt);
	}
	rejects_ = 0;

	std::vector<Blob> dots;
	dots.push_back(primary);
	Roi search = roi;
	if (search.empty()) {
		search = Roi{0, 0, frame.width, frame.height};
	}
	Blob second = moments_centroid_excluding(frame, search, gate, primary.x, primary.y,
											 primary.radius * 1.6f);
	if (second.found && second.mass > primary.mass * 0.18f) {
		dots.push_back(second);
		Blob third = moments_centroid_excluding(frame, search, gate, second.x, second.y,
												second.radius * 1.6f);
		if (third.found && third.mass > primary.mass * 0.18f) {
			const float dx = third.x - primary.x;
			const float dy = third.y - primary.y;
			if (dx * dx + dy * dy > (primary.radius * 1.6f) * (primary.radius * 1.6f)) {
				dots.push_back(third);
			}
		}
	}

	float use_x = primary.x;
	float use_y = primary.y;
	if (dots.size() >= 2) {
		use_x = 0.0f;
		use_y = 0.0f;
		for (const Blob& b : dots) {
			use_x += b.x;
			use_y += b.y;
		}
		use_x /= static_cast<float>(dots.size());
		use_y /= static_cast<float>(dots.size());
	}

	double fx = use_x;
	double fy = use_y;
	euro_.filter(use_x, use_y, t_s, fx, fy);

	if (have_filt_) {
		vel_x_ = static_cast<float>((fx - filt_x_) / std::max(dt, 1e-4f));
		vel_y_ = static_cast<float>((fy - filt_y_) / std::max(dt, 1e-4f));
	}
	filt_x_ = static_cast<float>(fx);
	filt_y_ = static_cast<float>(fy);
	have_filt_ = true;
	radius_ = primary.radius;
	last_blob_t_ = frame.t_hw;
	state_ = TrackState::Locked;

	double u = 0.5;
	double v = 0.5;
	H_.map(filt_x_, filt_y_, u, v);
	last_uv_x_ = clampf(static_cast<float>(u), 0.0f, 1.0f);
	last_uv_y_ = clampf(static_cast<float>(v), 0.0f, 1.0f);

	const float residual = static_cast<float>(H_.residual(filt_x_, filt_y_, last_uv_x_, last_uv_y_));
	last_conf_ = quality_confidence(primary, residual, frame.width, frame.height);

	AimSample sample;
	sample.uv_x = last_uv_x_;
	sample.uv_y = last_uv_y_;
	sample.confidence = last_conf_;
	sample.valid = last_conf_ >= cfg_.seeking_confidence;
	sample.t_hw = frame.t_hw;
	apply_lift(sample, primary, dt);

	debug_.state = state_;
	debug_.primary = primary;
	debug_.dot_count = static_cast<int>(dots.size());
	debug_.heading_deg = heading_deg(dots);
	debug_.cam_x = filt_x_;
	debug_.cam_y = filt_y_;
	debug_.vel_x = vel_x_;
	debug_.vel_y = vel_y_;
	debug_.residual = residual;
	debug_.seeking = is_seeking(sample.confidence, sample.valid);
	debug_.rejects = rejects_;

	bus_.publish(sample);
	last_t_ = frame.t_hw;
	return sample;
}

} // namespace sable
