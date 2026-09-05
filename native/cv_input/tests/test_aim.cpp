#include "sable/aim_bus.hpp"
#include "sable/aim_sample.hpp"
#include "sable/color.hpp"
#include "sable/constants.hpp"
#include "sable/one_euro.hpp"
#include "sable/pipeline.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

namespace {

int g_fails = 0;

void check(bool cond, const char* msg) {
	if (!cond) {
		std::fprintf(stderr, "FAIL: %s\n", msg);
		++g_fails;
	} else {
		std::printf("ok  %s\n", msg);
	}
}

// Cyan gaussian blob on a dark frame. Optional AE pop and extra flash blob.
sable::FrameBuffer make_frame(int w, int h, float cx, float cy, float radius, float peak,
							  float ae_gain, bool extra_flash, std::int64_t t_hw) {
	sable::FrameBuffer frame;
	frame.width = w;
	frame.height = h;
	frame.stride = w * 3;
	frame.format = sable::PixelFormat::Rgb24;
	frame.t_hw = t_hw;
	frame.bytes.assign(static_cast<size_t>(w * h * 3), 12);

	const float r2 = radius * radius * 2.2f;
	for (int y = 0; y < h; ++y) {
		for (int x = 0; x < w; ++x) {
			const float dx = (static_cast<float>(x) + 0.5f) - cx;
			const float dy = (static_cast<float>(y) + 0.5f) - cy;
			const float d2 = dx * dx + dy * dy;
			float a = std::exp(-d2 / r2) * peak;
			if (a < 0.02f) {
				a = 0.0f;
			}
			std::uint8_t* p = frame.bytes.data() + (y * w + x) * 3;
			float r = 12.0f + 40.0f * a;
			float g = 12.0f + 255.0f * a;
			float b = 12.0f + 230.0f * a;
			if (extra_flash) {
				// AE / rolling-shutter pop: a bright patch far from the sleeve.
				const float fx = static_cast<float>(x) - 40.0f;
				const float fy = static_cast<float>(y) - 40.0f;
				const float flash = std::exp(-(fx * fx + fy * fy) / 80.0f);
				r += 255.0f * flash;
				g += 255.0f * flash;
				b += 255.0f * flash;
			}
			r = std::min(255.0f, r * ae_gain);
			g = std::min(255.0f, g * ae_gain);
			b = std::min(255.0f, b * ae_gain);
			p[0] = static_cast<std::uint8_t>(r);
			p[1] = static_cast<std::uint8_t>(g);
			p[2] = static_cast<std::uint8_t>(b);
		}
	}
	return frame;
}

unsigned rng_state = 0xC0FFEEu;

float rng_uniform() {
	rng_state = rng_state * 1664525u + 1013904223u;
	return (rng_state >> 8) * (1.0f / 16777216.0f);
}

float rng_gauss() {
	// Box-Muller
	const float u1 = std::max(1e-6f, rng_uniform());
	const float u2 = rng_uniform();
	return std::sqrt(-2.0f * std::log(u1)) * std::cos(6.28318530718f * u2);
}

void test_one_euro_steady() {
	sable::OneEuro f(1.0, 0.007, 1.0, 30.0);
	double last = 0.0;
	for (int i = 0; i < 40; ++i) {
		const double t = i / 30.0;
		last = f.filter(10.0 + 0.4 * rng_gauss(), t);
	}
	check(std::fabs(last - 10.0) < 0.8, "one euro holds a noisy constant");
}

void test_hid_fire_uses_last_sample() {
	sable::AimPipeline pipe;
	sable::Hsv cyan;
	cyan.h = 175.0f;
	cyan.s = 0.85f;
	cyan.v = 0.90f;
	pipe.set_calib_hsv(cyan);

	auto frame = make_frame(320, 240, 200.0f, 90.0f, 9.0f, 1.0f, 1.0f, false, 1'000'000);
	const sable::AimSample seen = pipe.process(frame.view());
	check(seen.valid, "pipeline locks onto a synthetic blob");

	// Two missing camera frames. Fire must still return the last sample,
	// never wait, never snap UV to 0,0.
	pipe.process_missing(1'033'333, 1.0f / 30.0f);
	pipe.process_missing(1'066'666, 1.0f / 30.0f);
	const sable::AimSample shot = pipe.fire();
	check(shot.uv_x == pipe.peek().uv_x && shot.uv_y == pipe.peek().uv_y,
		  "HID fire peeks latest AimSample");
	check(shot.uv_x > 0.2f && shot.uv_y > 0.1f, "HID fire does not snap to 0,0");
	check(std::fabs(shot.uv_x - seen.uv_x) < 0.15f, "HID fire stays near last pose");
}

void test_two_frame_dropout_coasts() {
	sable::AimPipeline pipe;
	sable::Hsv cyan;
	cyan.h = 175.0f;
	cyan.s = 0.85f;
	cyan.v = 0.90f;
	pipe.set_calib_hsv(cyan);

	const int w = 320;
	const int h = 240;
	const float vx = 90.0f; // px/s
	std::vector<sable::AimSample> samples;
	for (int i = 0; i < 20; ++i) {
		const float t = static_cast<float>(i) / 30.0f;
		const float x = 80.0f + vx * t;
		const float y = 120.0f;
		auto frame = make_frame(w, h, x, y, 8.0f, 1.0f, 1.0f, false, static_cast<std::int64_t>(t * 1e6));
		samples.push_back(pipe.process(frame.view()));
	}
	const sable::AimSample before = samples.back();
	check(before.valid, "motion lock before dropout");

	// Exactly two dropped frames at 30 Hz = 66.6 ms < 100 ms coast window.
	const sable::AimSample c1 = pipe.process_missing(20 * 33333, 1.0f / 30.0f);
	const sable::AimSample c2 = pipe.process_missing(21 * 33333, 1.0f / 30.0f);

	check(c1.uv_x != 0.0f || c1.uv_y != 0.0f, "coast frame 1 does not jump to 0,0");
	check(c2.uv_x != 0.0f || c2.uv_y != 0.0f, "coast frame 2 does not jump to 0,0");
	check(std::fabs(c2.uv_x - before.uv_x) < 0.20f, "2-frame dropout UV continues");
	check(c2.uv_x >= before.uv_x - 0.01f, "coast follows last velocity, not a reverse snap");
	check(pipe.debug().state == sable::TrackState::Coasting || c2.valid,
		  "2-frame dropout stays in coast window");
}

void test_synthetic_path_rms() {
	// Documented bound (camera space, after One Euro + coast):
	//   30 Hz, 150 frames, circular orbit r=70px around (160, 120)
	//   gaussian noise σ=1.6 px, 1-frame dropouts every 18 frames
	//   AE-like gain pops every 22 frames, plus a 1-frame corner flash
	//   First 20 frames are settle. RMS vs ground-truth < 7.0 px
	//   (g++ 13 / -O0 observed ~5.8 px; 7.0 leaves compiler slack)
	constexpr double kRmsBoundPx = 7.0;
	constexpr int kW = 320;
	constexpr int kH = 240;
	constexpr int kN = 150;
	constexpr float kHz = 30.0f;
	constexpr float kR = 70.0f;
	constexpr float kCx = 160.0f;
	constexpr float kCy = 120.0f;

	sable::AimPipeline pipe;
	sable::Hsv cyan;
	cyan.h = 175.0f;
	cyan.s = 0.85f;
	cyan.v = 0.90f;
	pipe.set_calib_hsv(cyan);

	double err2 = 0.0;
	int n = 0;
	rng_state = 0xA11E11u;

	for (int i = 0; i < kN; ++i) {
		const float t = static_cast<float>(i) / kHz;
		const float ang = t * 2.0f * 3.14159265f / 5.0f; // 0.2 Hz
		const float gx = kCx + kR * std::cos(ang);
		const float gy = kCy + kR * std::sin(ang);
		const float nx = gx + 1.6f * rng_gauss();
		const float ny = gy + 1.6f * rng_gauss();
		const bool dropout = (i > 12) && (i % 18 == 0);
		const bool ae = (i > 8) && (i % 22 == 0);
		const float gain = ae ? 2.4f : 1.0f;
		const std::int64_t t_hw = static_cast<std::int64_t>(t * 1e6);

		if (dropout) {
			pipe.process_missing(t_hw, 1.0f / kHz);
		} else {
			auto frame = make_frame(kW, kH, nx, ny, 8.5f, 1.0f, gain, ae, t_hw);
			pipe.process(frame.view());
		}

		const float mx = pipe.debug().cam_x;
		const float my = pipe.debug().cam_y;
		if (i >= 20 && pipe.debug().state != sable::TrackState::Lost) {
			const double dx = mx - gx;
			const double dy = my - gy;
			err2 += dx * dx + dy * dy;
			++n;
		}
	}

	const double rms = (n > 0) ? std::sqrt(err2 / n) : 1e9;
	std::printf("synthetic RMS = %.3f px over %d frames (bound %.1f)\n", rms, n, kRmsBoundPx);
	check(n > 100, "synthetic path produced enough in-track samples");
	check(rms < kRmsBoundPx, "RMS after One Euro + coast is under 7.0 px");
}

void test_never_snaps_origin_after_loss() {
	sable::AimPipeline pipe;
	sable::Hsv cyan;
	cyan.h = 175.0f;
	cyan.s = 0.85f;
	cyan.v = 0.90f;
	pipe.set_calib_hsv(cyan);
	auto frame = make_frame(320, 240, 220.0f, 80.0f, 9.0f, 1.0f, 1.0f, false, 2'000'000);
	pipe.process(frame.view());
	const sable::AimSample locked = pipe.peek();
	for (int i = 0; i < 12; ++i) {
		pipe.process_missing(2'000'000 + (i + 1) * 33333, 1.0f / 30.0f);
	}
	const sable::AimSample lost = pipe.peek();
	check(!lost.valid, "valid drops after 100ms hole");
	check(std::fabs(lost.uv_x - locked.uv_x) < 0.25f, "lost tracker holds last UV");
	check(!(lost.uv_x == 0.0f && lost.uv_y == 0.0f), "lost tracker does not snap to 0,0");
}

void test_bus_fire_without_new_frame() {
	sable::AimBus bus;
	sable::AimSample a;
	a.uv_x = 0.41f;
	a.uv_y = 0.62f;
	a.valid = true;
	a.confidence = 0.8f;
	a.t_hw = 42;
	bus.publish(a);
	const sable::AimSample shot = bus.fire();
	check(shot == a, "AimBus.fire returns last published sample");
	const sable::AimSample again = bus.fire();
	check(again.t_hw == 42, "second fire without a frame still uses last sample");
}

void test_pad_click_while_lift_coasts() {
	// MacBook verb: raise hand (area jump), leave the lid cam to reach
	// the trackpad, click. HID motion must not drop lifted. Fire peeks.
	sable::AimPipeline pipe;
	sable::Hsv cyan;
	cyan.h = 175.0f;
	cyan.s = 0.85f;
	cyan.v = 0.90f;
	pipe.set_calib_hsv(cyan);
	pipe.set_hid_idle(true);

	std::int64_t t = 5'000'000;
	const std::int64_t dt = 33333;
	// Pad baseline: small blob.
	for (int i = 0; i < 12; ++i) {
		auto frame = make_frame(320, 240, 160.0f, 200.0f, 5.0f, 1.0f, 1.0f, false, t);
		pipe.process(frame.view());
		t += dt;
	}
	// Raise: much larger mass than the pad baseline.
	sable::AimSample raised;
	for (int i = 0; i < 10; ++i) {
		auto frame = make_frame(320, 240, 200.0f, 80.0f, 18.0f, 1.0f, 1.0f, false, t);
		raised = pipe.process(frame.view());
		t += dt;
	}
	check(raised.lifted, "area jump charges lift before the pad reach");

	// Hand leaves the frame. Finger is on the trackpad (HID not idle).
	pipe.set_hid_idle(false);
	sable::AimSample coast;
	for (int i = 0; i < 10; ++i) {
		coast = pipe.process_missing(t, 1.0f / 30.0f);
		t += dt;
	}
	const sable::AimSample shot = pipe.fire();
	check(coast.lifted, "lift sticks through ~330 ms hole while pad moves");
	check(shot.lifted, "HID fire peeks sticky lift, does not wait on a frame");
	check(shot.uv_x > 0.15f && shot.uv_y > 0.05f, "pad-click shot holds last UV");

	// After sticky + hid-hold expire, rest on the pad drops lift.
	for (int i = 0; i < 28; ++i) {
		coast = pipe.process_missing(t, 1.0f / 30.0f);
		t += dt;
	}
	check(!pipe.fire().lifted, "lift drops after sticky window, not forever");
}

} // namespace

int main() {
	test_one_euro_steady();
	test_bus_fire_without_new_frame();
	test_hid_fire_uses_last_sample();
	test_two_frame_dropout_coasts();
	test_synthetic_path_rms();
	test_never_snaps_origin_after_loss();
	test_pad_click_while_lift_coasts();
	if (g_fails != 0) {
		std::fprintf(stderr, "\n%d test(s) failed\n", g_fails);
		return 1;
	}
	std::printf("\nall aim tests passed\n");
	return 0;
}
