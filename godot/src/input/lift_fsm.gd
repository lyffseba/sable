class_name LiftFsm
extends RefCounted

## HID idle (15–30 ms of near-zero dx/dy) AND a camera size-jump.
## Hysteresis 80–150 ms. Camera half lives in native/cv_input.

const HID_IDLE_MS := 22.0
const HYSTERESIS_MS := 110.0

var lifted: bool = false
var _idle_ms: float = 0.0
var _hold_ms: float = 0.0


func tick(delta_s: float, hid_dx: float, hid_dy: float, cam_size_jump: bool) -> bool:
	var idle := absf(hid_dx) < 0.35 and absf(hid_dy) < 0.35
	if idle:
		_idle_ms += delta_s * 1000.0
	else:
		_idle_ms = 0.0
	var hid_idle := _idle_ms >= 15.0
	var want := hid_idle and cam_size_jump
	if want:
		_hold_ms += delta_s * 1000.0
	else:
		_hold_ms -= delta_s * 1000.0
	_hold_ms = clampf(_hold_ms, 0.0, HYSTERESIS_MS * 2.0)
	lifted = _hold_ms >= HYSTERESIS_MS
	return lifted
