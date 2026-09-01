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
#include "sable/pipeline.hpp"

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

	Dictionary peek() const { return to_dict(pipeline_.peek()); }
	Dictionary fire() const { return to_dict(pipeline_.fire()); }

	void process_missing(int64_t t_hw, float dt_s) { pipeline_.process_missing(t_hw, dt_s); }

protected:
	static void _bind_methods() {
		ClassDB::bind_method(D_METHOD("set_calib_hsv", "h", "s", "v"), &CvInput::set_calib_hsv);
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
