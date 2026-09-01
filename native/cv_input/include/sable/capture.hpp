#pragma once

#include <atomic>
#include <cstdint>
#include <mutex>
#include <string>
#include <thread>

#include "sable/image.hpp"

namespace sable {

struct CaptureConfig {
	std::string device = "/dev/video0";
	int width = 640;
	int height = 480;
	int fps = 30;
	bool prefer_yuy2 = true;
	bool lock_exposure = true;
	bool lock_awb = true;
};

// Worker-thread capture. Always keeps the newest frame (drop-old, buffer=1
// semantics). Linux V4L2 first; Media Foundation is a later Windows port.
class CaptureThread {
public:
	virtual ~CaptureThread() { stop(); }

	virtual bool start(const CaptureConfig& cfg);
	void stop();
	bool running() const { return running_.load(); }
	bool exposure_locked() const { return exposure_locked_.load(); }
	bool has_frame() const { return has_frame_.load(); }

	// Copy the latest frame. Returns false if none yet.
	bool latest(FrameBuffer& out) const;

	const std::string& last_error() const { return error_; }
	const std::string& backend() const { return backend_; }

protected:
	virtual void run() = 0;
	void publish(const FrameBuffer& frame);

	CaptureConfig cfg_{};
	std::atomic<bool> stop_{false};
	std::atomic<bool> running_{false};
	std::atomic<bool> has_frame_{false};
	std::atomic<bool> exposure_locked_{false};
	std::string error_;
	std::string backend_ = "none";

private:
	std::thread thread_;
	mutable std::mutex mu_;
	FrameBuffer latest_{};
};

// V4L2 capture when built on Linux. Otherwise a no-device stub.
class V4l2Capture : public CaptureThread {
public:
	bool start(const CaptureConfig& cfg) override;

protected:
	void run() override;
};

// Dummy capture used when no camera is present. Does not invent aim.
class DummyCapture : public CaptureThread {
public:
	bool start(const CaptureConfig& cfg) override;

protected:
	void run() override;
};

} // namespace sable
