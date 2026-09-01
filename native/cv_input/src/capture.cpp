#include "sable/capture.hpp"

#include <algorithm>
#include <chrono>
#include <cstring>
#include <memory>
#include <vector>

#if defined(__linux__)
#include <cstring>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <linux/videodev2.h>
#endif

namespace sable {

bool CaptureThread::start(const CaptureConfig& cfg) {
	stop();
	cfg_ = cfg;
	stop_ = false;
	error_.clear();
	thread_ = std::thread([this]() {
		running_ = true;
		run();
		running_ = false;
	});
	return true;
}

void CaptureThread::stop() {
	stop_ = true;
	if (thread_.joinable()) {
		thread_.join();
	}
	running_ = false;
}

void CaptureThread::publish(const FrameBuffer& frame) {
	std::lock_guard<std::mutex> lock(mu_);
	latest_ = frame;
	has_frame_ = true;
	seq_.fetch_add(1, std::memory_order_release);
}

bool CaptureThread::latest(FrameBuffer& out) const {
	std::lock_guard<std::mutex> lock(mu_);
	if (!has_frame_) {
		return false;
	}
	out = latest_;
	return true;
}

bool DummyCapture::start(const CaptureConfig& cfg) {
	backend_ = "dummy";
	error_ = "no camera";
	return CaptureThread::start(cfg);
}

void DummyCapture::run() {
	// No invented pose. The Godot desktop fallback supplies AimSample.
	while (!stop_) {
		std::this_thread::sleep_for(std::chrono::milliseconds(20));
	}
}

#if defined(__linux__)

namespace {

std::int64_t now_us() {
	using clock = std::chrono::steady_clock;
	return std::chrono::duration_cast<std::chrono::microseconds>(clock::now().time_since_epoch())
		.count();
}

bool v4l2_set_ctrl(int fd, __u32 id, __s32 value) {
	struct v4l2_control ctrl;
	std::memset(&ctrl, 0, sizeof(ctrl));
	ctrl.id = id;
	ctrl.value = value;
	return ioctl(fd, VIDIOC_S_CTRL, &ctrl) == 0;
}

} // namespace

bool V4l2Capture::start(const CaptureConfig& cfg) {
	backend_ = "v4l2";
	return CaptureThread::start(cfg);
}

void V4l2Capture::run() {
	const int fd = ::open(cfg_.device.c_str(), O_RDWR | O_NONBLOCK);
	if (fd < 0) {
		error_ = "open failed: " + cfg_.device;
		backend_ = "dummy";
		while (!stop_) {
			std::this_thread::sleep_for(std::chrono::milliseconds(20));
		}
		return;
	}

	struct v4l2_format fmt;
	std::memset(&fmt, 0, sizeof(fmt));
	fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	fmt.fmt.pix.width = static_cast<__u32>(cfg_.width);
	fmt.fmt.pix.height = static_cast<__u32>(cfg_.height);
	fmt.fmt.pix.pixelformat = cfg_.prefer_yuy2 ? V4L2_PIX_FMT_YUYV : V4L2_PIX_FMT_MJPEG;
	fmt.fmt.pix.field = V4L2_FIELD_NONE;
	if (ioctl(fd, VIDIOC_S_FMT, &fmt) != 0 && cfg_.prefer_yuy2) {
		fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_MJPEG;
		if (ioctl(fd, VIDIOC_S_FMT, &fmt) != 0) {
			error_ = "VIDIOC_S_FMT failed";
			::close(fd);
			return;
		}
	}

	struct v4l2_streamparm parm;
	std::memset(&parm, 0, sizeof(parm));
	parm.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	parm.parm.capture.timeperframe.numerator = 1;
	parm.parm.capture.timeperframe.denominator = static_cast<__u32>(cfg_.fps);
	ioctl(fd, VIDIOC_S_PARM, &parm);

	if (cfg_.lock_exposure) {
		bool locked = false;
#ifdef V4L2_CID_EXPOSURE_AUTO
		locked = v4l2_set_ctrl(fd, V4L2_CID_EXPOSURE_AUTO, V4L2_EXPOSURE_MANUAL) ||
				 v4l2_set_ctrl(fd, V4L2_CID_EXPOSURE_AUTO, 1);
#endif
#ifdef V4L2_CID_EXPOSURE_AUTO_PRIORITY
		v4l2_set_ctrl(fd, V4L2_CID_EXPOSURE_AUTO_PRIORITY, 0);
#endif
		exposure_locked_ = locked;
	}
	if (cfg_.lock_awb) {
#ifdef V4L2_CID_AUTO_WHITE_BALANCE
		v4l2_set_ctrl(fd, V4L2_CID_AUTO_WHITE_BALANCE, 0);
#endif
	}

	// Request a single user-visible slot. The driver may keep a hidden
	// queue; we dequeue every pending buffer and keep only the newest.
	struct v4l2_requestbuffers req;
	std::memset(&req, 0, sizeof(req));
	req.count = 2;
	req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	req.memory = V4L2_MEMORY_MMAP;
	if (ioctl(fd, VIDIOC_REQBUFS, &req) != 0 || req.count < 1) {
		error_ = "VIDIOC_REQBUFS failed";
		::close(fd);
		return;
	}

	struct Mapping {
		void* start = nullptr;
		size_t len = 0;
	};
	std::vector<Mapping> maps(req.count);
	for (__u32 i = 0; i < req.count; ++i) {
		struct v4l2_buffer buf;
		std::memset(&buf, 0, sizeof(buf));
		buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
		buf.memory = V4L2_MEMORY_MMAP;
		buf.index = i;
		if (ioctl(fd, VIDIOC_QUERYBUF, &buf) != 0) {
			error_ = "VIDIOC_QUERYBUF failed";
			::close(fd);
			return;
		}
		maps[i].len = buf.length;
		maps[i].start = mmap(nullptr, buf.length, PROT_READ | PROT_WRITE, MAP_SHARED, fd, buf.m.offset);
		if (maps[i].start == MAP_FAILED) {
			error_ = "mmap failed";
			::close(fd);
			return;
		}
		if (ioctl(fd, VIDIOC_QBUF, &buf) != 0) {
			error_ = "VIDIOC_QBUF failed";
			::close(fd);
			return;
		}
	}

	enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	if (ioctl(fd, VIDIOC_STREAMON, &type) != 0) {
		error_ = "VIDIOC_STREAMON failed";
		::close(fd);
		return;
	}

	const bool yuy2 = fmt.fmt.pix.pixelformat == V4L2_PIX_FMT_YUYV;
	backend_ = yuy2 ? "v4l2-yuy2" : "v4l2-mjpeg";

	while (!stop_) {
		struct v4l2_buffer buf;
		std::memset(&buf, 0, sizeof(buf));
		buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
		buf.memory = V4L2_MEMORY_MMAP;

		// Drain to the latest queued frame.
		bool got = false;
		struct v4l2_buffer newest;
		while (ioctl(fd, VIDIOC_DQBUF, &buf) == 0) {
			newest = buf;
			got = true;
			// Keep dequeuing if another buffer is already waiting.
			struct v4l2_buffer peek;
			std::memset(&peek, 0, sizeof(peek));
			peek.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
			peek.memory = V4L2_MEMORY_MMAP;
			if (ioctl(fd, VIDIOC_DQBUF, &peek) != 0) {
				break;
			}
			ioctl(fd, VIDIOC_QBUF, &buf);
			buf = peek;
			newest = peek;
		}
		if (!got) {
			std::this_thread::sleep_for(std::chrono::milliseconds(2));
			continue;
		}

		if (!yuy2) {
			// MJPEG decode is optional (OpenCV). Until linked, skip the frame
			// rather than invent a pose.
			ioctl(fd, VIDIOC_QBUF, &newest);
			continue;
		}

		const Mapping& map = maps[newest.index];
		FrameBuffer frame;
		frame.width = static_cast<int>(fmt.fmt.pix.width);
		frame.height = static_cast<int>(fmt.fmt.pix.height);
		frame.stride = frame.width * 2;
		frame.format = PixelFormat::Yuy2;
		frame.t_hw = now_us();
		const size_t n = std::min(map.len, static_cast<size_t>(frame.stride * frame.height));
		frame.bytes.resize(n);
		std::memcpy(frame.bytes.data(), map.start, n);
		publish(frame);
		ioctl(fd, VIDIOC_QBUF, &newest);
	}

	ioctl(fd, VIDIOC_STREAMOFF, &type);
	for (Mapping& m : maps) {
		if (m.start && m.start != MAP_FAILED) {
			munmap(m.start, m.len);
		}
	}
	::close(fd);
}

#else

bool V4l2Capture::start(const CaptureConfig& cfg) {
	backend_ = "dummy";
	error_ = "V4L2 not available on this platform";
	return CaptureThread::start(cfg);
}

void V4l2Capture::run() {
	while (!stop_) {
		std::this_thread::sleep_for(std::chrono::milliseconds(20));
	}
}

#endif

#if !defined(__APPLE__)

bool AvfCapture::start(const CaptureConfig& cfg) {
	backend_ = "dummy";
	error_ = "AVFoundation not available on this platform";
	return CaptureThread::start(cfg);
}

void AvfCapture::on_sample_buffer(void*) {}

void AvfCapture::run() {
	while (!stop_) {
		std::this_thread::sleep_for(std::chrono::milliseconds(20));
	}
}

#endif

std::unique_ptr<CaptureThread> make_capture() {
#if defined(__APPLE__)
	return std::make_unique<AvfCapture>();
#elif defined(__linux__)
	return std::make_unique<V4l2Capture>();
#else
	return std::make_unique<DummyCapture>();
#endif
}

} // namespace sable
