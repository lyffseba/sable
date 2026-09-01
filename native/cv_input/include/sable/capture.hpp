#pragma once

#include <atomic>
#include <cstdint>
#include <memory>
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
// semantics). Linux V4L2; macOS AVFoundation; Media Foundation later.
class CaptureThread {
public:
	virtual ~CaptureThread() { stop(); }

	virtual bool start(const CaptureConfig& cfg);
	void stop();
	bool running() const { return running_.load(); }
	bool exposure_locked() const { return exposure_locked_.load(); }
	bool has_frame() const { return has_frame_.load(); }
	std::uint64_t seq() const { return seq_.load(); }

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
	std::atomic<std::uint64_t> seq_{0};
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
	V4l2Capture() { backend_ = "v4l2"; }
	bool start(const CaptureConfig& cfg) override;

protected:
	void run() override;
};

// AVFoundation capture when built on Apple. Otherwise a no-device stub.
class AvfCapture : public CaptureThread {
public:
	AvfCapture() { backend_ = "avf"; }
	bool start(const CaptureConfig& cfg) override;
	// AVF delegate hook (CMSampleBufferRef as void*). Not a game API.
	void on_sample_buffer(void* sample_buffer);

protected:
	void run() override;
};

// Dummy capture used when no camera is present. Does not invent aim.
class DummyCapture : public CaptureThread {
public:
	DummyCapture() { backend_ = "dummy"; }
	bool start(const CaptureConfig& cfg) override;

protected:
	void run() override;
};

// Platform camera: AvfCapture on Apple, V4l2Capture on Linux, else dummy.
std::unique_ptr<CaptureThread> make_capture();

} // namespace sable
