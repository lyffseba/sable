#pragma once

#include <mutex>

#include "sable/aim_sample.hpp"

namespace sable {

// Latest-sample mailbox. HID fire peeks; it never blocks on capture.
class AimBus {
public:
	void publish(const AimSample& sample) {
		std::lock_guard<std::mutex> lock(mu_);
		latest_ = sample;
	}

	AimSample peek() const {
		std::lock_guard<std::mutex> lock(mu_);
		return latest_;
	}

	// Fire contract: return the last published sample even if the
	// current camera frame is missing. Do not wait.
	AimSample fire() const { return peek(); }

private:
	mutable std::mutex mu_;
	AimSample latest_{};
};

} // namespace sable
