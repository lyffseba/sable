#pragma once

#include <cstdint>
#include <vector>

#include "sable/aim_bus.hpp"
#include "sable/aim_sample.hpp"
#include "sable/color.hpp"
#include "sable/constants.hpp"
#include "sable/homography.hpp"
#include "sable/image.hpp"
#include "sable/moments.hpp"
#include "sable/one_euro.hpp"

namespace sable {

enum class TrackState {
	Lost,
	Locked,
	Coasting,
};

struct PipelineConfig {
	float one_euro_mincutoff = kOneEuroMincutoffHz;
	float one_euro_beta = kOneEuroBeta;
	float one_euro_dcutoff = kOneEuroDcutoffHz;
	float coast_ms = kCoastMs;
	float roi_scale = kRoiRadiusScale;
	float outlier_jump_px = kOutlierJumpPx;
	int outlier_relock = kOutlierRejectsBeforeRelock;
	float seeking_confidence = kSeekingConfidence;
	int adapt_every = kAdaptEveryNFrames;
};

struct PipelineDebug {
	TrackState state = TrackState::Lost;
	Blob primary{};
	int dot_count = 0;
	float heading_deg = 0.0f;
	float cam_x = 0.0f;
	float cam_y = 0.0f;
	float vel_x = 0.0f;
	float vel_y = 0.0f;
	float residual = 0.0f;
	bool hid_idle = false;
	bool seeking = true;
	int rejects = 0;
};

// Bad-camera tracker. Input is a frame (+ optional HID idle). Output is
// AimSample on the bus. Fire peeks the bus and never waits here.
class AimPipeline {
public:
	explicit AimPipeline(PipelineConfig cfg = {});

	void reset();
	void set_calib_hsv(const Hsv& sample);
	void set_homography(const Homography& h);
	void set_normalize(int width, int height);
	void set_exposure_locked(bool locked) { exposure_locked_ = locked; }
	void set_hid_idle(bool idle) { hid_idle_ = idle; }

	AimSample process(const ImageView& frame);
	AimSample process_missing(std::int64_t t_hw, float dt_s);

	AimSample peek() const { return bus_.peek(); }
	AimSample fire() const { return bus_.fire(); }
	const PipelineDebug& debug() const { return debug_; }
	AimBus& bus() { return bus_; }

private:
	void publish_hold(std::int64_t t_hw);
	void apply_lift(AimSample& sample, const Blob& blob, float dt_s);
	void adapt_gate(const ImageView& frame, const Roi& roi);
	ColorGate effective_gate() const;

	PipelineConfig cfg_;
	AimBus bus_;
	OneEuro2 euro_;
	Homography H_;
	ColorGate gate_{};
	bool have_calib_ = false;
	bool exposure_locked_ = false;
	bool hid_idle_ = false;

	TrackState state_ = TrackState::Lost;
	float filt_x_ = 0.0f;
	float filt_y_ = 0.0f;
	float vel_x_ = 0.0f;
	float vel_y_ = 0.0f;
	float last_uv_x_ = 0.5f;
	float last_uv_y_ = 0.5f;
	float last_conf_ = 0.0f;
	float radius_ = 18.0f;
	float pad_area_ = 0.0f;
	float lift_ms_ = 0.0f;
	int rejects_ = 0;
	int frame_i_ = 0;
	std::int64_t last_blob_t_ = 0;
	std::int64_t last_t_ = 0;
	bool have_filt_ = false;
	PipelineDebug debug_{};
};

} // namespace sable
