// GDExtension entry. Compiles only when godot-cpp headers are on the
// include path (see README). The C ABI in cv_input_c_api.cpp is the
// always-built contract; Godot loads this module after godot-cpp is linked.

#if defined(SABLE_WITH_GODOT_CPP)

#include <gdextension_interface.h>
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/core/defs.hpp>
#include <godot_cpp/godot.hpp>
#include <godot_cpp/variant/dictionary.hpp>
#include <godot_cpp/variant/vector2.hpp>

#include "sable/aim_sample.hpp"
#include "sable/capture.hpp"
#include "sable/pipeline.hpp"

#include <cstdint>
#include <memory>

using namespace godot;

class CvInput : public RefCounted {
	GDCLASS(CvInput, RefCounted)

public:
	void set_calib_hsv(float h, float s, float v) {
		sable::Hsv hsv;
		hsv.h = h;
		hsv.s = s;
		hsv.v = v;
		pipeline_.set_calib_hsv(hsv);
	}

	bool start_capture(const String& device) {
		capture_ = sable::make_capture();
		last_seq_ = 0;
		sable::CaptureConfig cfg;
		if (!device.is_empty()) {
			const CharString utf = device.utf8();
			cfg.device = utf.get_data();
		}
		return capture_->start(cfg);
	}

	void stop_capture() {
		if (capture_) {
			capture_->stop();
		}
	}

	// Feed the newest camera frame into the pipeline. Does not wait.
	// Fire must not call this.
	int poll_capture() {
		if (!capture_) {
			return 0;
		}
		const std::uint64_t seq = capture_->seq();
		if (seq == 0 || seq == last_seq_) {
			return 0;
		}
		sable::FrameBuffer frame;
		if (!capture_->latest(frame) || frame.bytes.empty()) {
			return 0;
		}
		last_seq_ = seq;
		pipeline_.set_exposure_locked(capture_->exposure_locked());
		pipeline_.process(frame.view());
		return 1;
	}

	Dictionary peek() const { return to_dict(pipeline_.peek()); }
	// HID fire peeks. Never polls capture. Never waits on a frame.
	Dictionary fire() const { return to_dict(pipeline_.fire()); }

	void process_missing(int64_t t_hw, float dt_s) { pipeline_.process_missing(t_hw, dt_s); }

protected:
	static void _bind_methods() {
		ClassDB::bind_method(D_METHOD("set_calib_hsv", "h", "s", "v"), &CvInput::set_calib_hsv);
		ClassDB::bind_method(D_METHOD("start_capture", "device"), &CvInput::start_capture);
		ClassDB::bind_method(D_METHOD("stop_capture"), &CvInput::stop_capture);
		ClassDB::bind_method(D_METHOD("poll_capture"), &CvInput::poll_capture);
		ClassDB::bind_method(D_METHOD("peek"), &CvInput::peek);
		ClassDB::bind_method(D_METHOD("fire"), &CvInput::fire);
		ClassDB::bind_method(D_METHOD("process_missing", "t_hw", "dt_s"), &CvInput::process_missing);
	}

private:
	static Dictionary to_dict(const sable::AimSample& s) {
		Dictionary d;
		d["uv"] = Vector2(s.uv_x, s.uv_y);
		d["valid"] = s.valid;
		d["lifted"] = s.lifted;
		d["confidence"] = s.confidence;
		d["t_hw"] = s.t_hw;
		return d;
	}

	sable::AimPipeline pipeline_;
	std::unique_ptr<sable::CaptureThread> capture_;
	std::uint64_t last_seq_ = 0;
};

static void initialize_cv_input(ModuleInitializationLevel level) {
	if (level != MODULE_INITIALIZATION_LEVEL_SCENE) {
		return;
	}
	GDREGISTER_CLASS(CvInput);
}

static void uninitialize_cv_input(ModuleInitializationLevel level) {
	if (level != MODULE_INITIALIZATION_LEVEL_SCENE) {
		return;
	}
}

extern "C" {
GDExtensionBool GDE_EXPORT cv_input_library_init(GDExtensionInterfaceGetProcAddress get_proc_address,
												 const GDExtensionClassLibraryPtr library,
												 GDExtensionInitialization* initialization) {
	godot::GDExtensionBinding::InitObject init_obj(get_proc_address, library, initialization);
	init_obj.register_initializer(initialize_cv_input);
	init_obj.register_terminator(uninitialize_cv_input);
	init_obj.set_minimum_library_initialization_level(MODULE_INITIALIZATION_LEVEL_SCENE);
	return init_obj.init();
}
}

#endif
