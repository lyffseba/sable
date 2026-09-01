extends Node

enum Mode { PAD, GUN, DESKTOP }

const SEEKING_CONFIDENCE := 0.35

var mode: int = Mode.DESKTOP
var camera_enabled: bool = false
var force_gun: bool = false
var _cv = null
var _hid_idle: bool = false
var _last_mouse := Vector2.ZERO
var _idle_ms: float = 0.0


func _ready() -> void:
	_try_bind_cv()
	_publish_desktop()


func _try_bind_cv() -> void:
	if ClassDB.class_exists("CvInput"):
		_cv = ClassDB.instantiate("CvInput")
	else:
		_cv = null


func enable_camera() -> bool:
	camera_enabled = true
	_try_bind_cv()
	if _cv != null:
		if _cv.has_method("start_capture"):
			_cv.start_capture("")
		mode = Mode.PAD
		return true
	mode = Mode.DESKTOP
	return false


func force_desktop() -> void:
	mode = Mode.DESKTOP
	force_gun = false


func toggle_force_gun() -> void:
	force_gun = not force_gun
	if force_gun:
		mode = Mode.GUN


func mode_name() -> String:
	if is_seeking() and mode != Mode.DESKTOP:
		return "SEEKING"
	match mode:
		Mode.PAD:
			return "PAD"
		Mode.GUN:
			return "GUN"
		_:
			return "DESKTOP"


func is_seeking() -> bool:
	return AimBus.peek().is_seeking() and mode != Mode.DESKTOP


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("desktop_aim"):
		force_desktop()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("force_gun"):
		toggle_force_gun()
		get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	_update_hid_idle(delta)
	if mode == Mode.DESKTOP or _cv == null:
		_publish_desktop()
		return
	_poll_cv()


func _update_hid_idle(delta: float) -> void:
	var mouse := Vector2.ZERO
	var vp := get_viewport()
	if vp != null:
		mouse = vp.get_mouse_position()
	var moved := (mouse - _last_mouse).length() > 0.4
	_last_mouse = mouse
	if moved:
		_idle_ms = 0.0
		_hid_idle = false
	else:
		_idle_ms += delta * 1000.0
		_hid_idle = _idle_ms >= 15.0 and _idle_ms <= 400.0


func _publish_desktop() -> void:
	var sample := AimSample.new()
	var vp := get_viewport()
	if vp != null:
		var size: Vector2 = vp.get_visible_rect().size
		if size.x > 1.0 and size.y > 1.0:
			var mouse: Vector2 = vp.get_mouse_position()
			sample.uv = Vector2(mouse.x / size.x, mouse.y / size.y)
	sample.valid = true
	sample.confidence = 1.0
	sample.lifted = force_gun
	sample.t_hw = Time.get_ticks_usec()
	if force_gun:
		mode = Mode.GUN
	elif mode != Mode.DESKTOP and _cv == null:
		mode = Mode.DESKTOP
	AimBus.publish(sample)


func _poll_cv() -> void:
	if _cv == null:
		_publish_desktop()
		return
	# Reticle may poll the newest frame. HID fire never does.
	if _cv.has_method("poll_capture"):
		_cv.poll_capture()
	var d: Dictionary = _cv.peek()
	var sample := AimSample.new()
	sample.uv = d.get("uv", Vector2(0.5, 0.5))
	sample.valid = bool(d.get("valid", false))
	sample.lifted = bool(d.get("lifted", false)) or force_gun
	sample.confidence = float(d.get("confidence", 0.0))
	sample.t_hw = int(d.get("t_hw", Time.get_ticks_usec()))
	if force_gun:
		sample.lifted = true
		mode = Mode.GUN
	elif sample.lifted:
		mode = Mode.GUN
	else:
		mode = Mode.PAD
	AimBus.publish(sample)
