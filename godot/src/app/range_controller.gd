extends Node3D

@onready var _camera: Camera3D = $Camera3D
@onready var _orb: Node3D = $DummyOrb
@onready var _score_label: Label = $HUD/Score
@onready var _mode_label: Label = $HUD/ModeChip
@onready var _conf_label: Label = $HUD/Confidence
@onready var _cross: Control = $HUD/Crosshair

var _score: int = 0
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.randomize()
	_place_orb()
	_refresh_hud()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("fire"):
		_fire(HidFire.shot_from_bus(AimBus))
		get_viewport().set_input_as_handled()


func _process(_delta: float) -> void:
	_refresh_hud()
	var sample: AimSample = AimBus.peek()
	var size: Vector2 = get_viewport().get_visible_rect().size
	_cross.position = Vector2(sample.uv.x * size.x, sample.uv.y * size.y) - _cross.size * 0.5


func _refresh_hud() -> void:
	var sample: AimSample = AimBus.peek()
	_score_label.text = "SCORE  %d" % _score
	var chip := AimService.mode_name()
	if AimService.mode != AimService.Mode.DESKTOP and sample.is_seeking():
		chip = "SEEKING"
	_mode_label.text = chip
	_conf_label.text = "CONF  %.2f" % sample.confidence


func _fire(sample: AimSample) -> void:
	# Shot uses the latest AimSample right now. Reticle may lag; the shot does not.
	var vp := get_viewport()
	var size: Vector2 = vp.get_visible_rect().size
	var screen := Vector2(sample.uv.x * size.x, sample.uv.y * size.y)
	var origin: Vector3 = _camera.project_ray_origin(screen)
	var dir: Vector3 = _camera.project_ray_normal(screen)
	if _ray_hits_sphere(origin, dir, _orb.global_position, 0.38):
		_score += 1
		_place_orb()
	_refresh_hud()


func _place_orb() -> void:
	var x := _rng.randf_range(-2.4, 2.4)
	var y := _rng.randf_range(0.7, 2.4)
	var z := _rng.randf_range(-3.2, -1.2)
	_orb.position = Vector3(x, y, z)


func _ray_hits_sphere(origin: Vector3, dir: Vector3, center: Vector3, radius: float) -> bool:
	var oc := origin - center
	var a := dir.dot(dir)
	var b := 2.0 * oc.dot(dir)
	var c := oc.dot(oc) - radius * radius
	var disc := b * b - 4.0 * a * c
	if disc < 0.0:
		return false
	var t := (-b - sqrt(disc)) / (2.0 * a)
	return t > 0.0
