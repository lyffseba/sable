#include "sable/aim_sample.hpp"
#include "sable/capture.hpp"
#include "sable/color.hpp"
#include "sable/pipeline.hpp"

#include <memory>

extern "C" {

struct CvInputHandle {
	sable::AimPipeline pipeline;
	std::unique_ptr<sable::CaptureThread> capture;
};

void* cv_input_create() { return new CvInputHandle(); }

void cv_input_destroy(void* ptr) {
	auto* h = static_cast<CvInputHandle*>(ptr);
	if (h && h->capture) {
		h->capture->stop();
	}
	delete h;
}

void cv_input_set_calib_hsv(void* ptr, float h, float s, float v) {
	auto* handle = static_cast<CvInputHandle*>(ptr);
	if (!handle) {
		return;
	}
	sable::Hsv hsv;
	hsv.h = h;
	hsv.s = s;
	hsv.v = v;
	handle->pipeline.set_calib_hsv(hsv);
}

void cv_input_process_rgb(void* ptr, const unsigned char* rgb, int width, int height, long long t_hw) {
	auto* handle = static_cast<CvInputHandle*>(ptr);
	if (!handle || !rgb) {
		return;
	}
	sable::ImageView view;
	view.data = rgb;
	view.width = width;
	view.height = height;
	view.stride = width * 3;
	view.format = sable::PixelFormat::Rgb24;
	view.t_hw = t_hw;
	handle->pipeline.process(view);
}

void cv_input_process_missing(void* ptr, long long t_hw, float dt_s) {
	auto* handle = static_cast<CvInputHandle*>(ptr);
	if (!handle) {
		return;
	}
	handle->pipeline.process_missing(t_hw, dt_s);
}

void cv_input_peek(void* ptr, float* uv_x, float* uv_y, int* valid, int* lifted, float* confidence,
				   long long* t_hw) {
	auto* handle = static_cast<CvInputHandle*>(ptr);
	sable::AimSample s;
	if (handle) {
		s = handle->pipeline.peek();
	}
	if (uv_x) {
		*uv_x = s.uv_x;
	}
	if (uv_y) {
		*uv_y = s.uv_y;
	}
	if (valid) {
		*valid = s.valid ? 1 : 0;
	}
	if (lifted) {
		*lifted = s.lifted ? 1 : 0;
	}
	if (confidence) {
		*confidence = s.confidence;
	}
	if (t_hw) {
		*t_hw = s.t_hw;
	}
}

void cv_input_fire(void* ptr, float* uv_x, float* uv_y, int* valid, int* lifted, float* confidence,
				   long long* t_hw) {
	auto* handle = static_cast<CvInputHandle*>(ptr);
	sable::AimSample s;
	if (handle) {
		s = handle->pipeline.fire();
	}
	if (uv_x) {
		*uv_x = s.uv_x;
	}
	if (uv_y) {
		*uv_y = s.uv_y;
	}
	if (valid) {
		*valid = s.valid ? 1 : 0;
	}
	if (lifted) {
		*lifted = s.lifted ? 1 : 0;
	}
	if (confidence) {
		*confidence = s.confidence;
	}
	if (t_hw) {
		*t_hw = s.t_hw;
	}
}

int cv_input_start_capture(void* ptr, const char* device) {
	auto* handle = static_cast<CvInputHandle*>(ptr);
	if (!handle) {
		return 0;
	}
	sable::CaptureConfig cfg;
	if (device && device[0]) {
		cfg.device = device;
	}
	handle->capture = std::make_unique<sable::V4l2Capture>();
	return handle->capture->start(cfg) ? 1 : 0;
}

void cv_input_stop_capture(void* ptr) {
	auto* handle = static_cast<CvInputHandle*>(ptr);
	if (!handle || !handle->capture) {
		return;
	}
	handle->capture->stop();
}

int cv_input_poll_capture(void* ptr) {
	auto* handle = static_cast<CvInputHandle*>(ptr);
	if (!handle || !handle->capture) {
		return 0;
	}
	sable::FrameBuffer frame;
	if (!handle->capture->latest(frame) || frame.bytes.empty()) {
		return 0;
	}
	handle->pipeline.set_exposure_locked(handle->capture->exposure_locked());
	handle->pipeline.process(frame.view());
	return 1;
}

} // extern "C"
