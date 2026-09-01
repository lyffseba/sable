extends Node3D

## Bay 1v1. AimSample is the gun. CANCHO is a capsule tell, not a scan.

enum Phase { PAD, GUN, FREEZE, MATCH }

const TO_WIN := 5
const SPEED := 4.2
const EXPOSE_S := 0.12
const FREEZE_PAD_S := 0.45
const VO_S := 0.70
const EYE_H := 1.64
const HEIGHT := 1.78
const SPAWN_A := Vector3(0.0, 0.0, 10.0)
const SPAWN_B := Vector3(0.0, 0.89, -10.0)
const MINT := Color(0.35, 0.95, 0.78, 1)
const BONE := Color(0.90, 0.88, 0.82, 1)
const VO_LIFT := "Al aire."
const VO_HIT := "Claro."
const VO_DROP := "Al suelo."
const VO_WIN := "Se escribió."

@onready var _player: CharacterBody3D = $Player
@onready var _camera: Camera3D = $Player/Camera3D
@onready var _gun_arm: Node3D = $Player/Camera3D/GunArm
@onready var _foe: MeshInstance3D = $Foe
@onready var _score_label: Label = $HUD/Score
@onready var _phase_label: Label = $HUD/ModeChip
@onready var _cover_label: Label = $HUD/CoverChip
@onready var _vo_label: Label = $HUD/VoChip
@onready var _hint: Label = $HUD/Hint
@onready var _cross: Control = $HUD/Crosshair
@onready var _miss_tick: ColorRect = $HUD/MissTick
@onready var _boot_btn: Button = $HUD/Boot
@onready var _tick_player: AudioStreamPlayer = $TickPlayer

var _you: int = 0
var _them: int = 0
var _round: int = 1
var _phase: int = Phase.PAD
var _frozen: bool = false
var _freeze_t: float = 0.0
var _expose: float = 0.0
var _was_lifted: bool = false
var _vo_t: float = 0.0
var _miss_t: float = 0.0
var _match_over: bool = false
var _pending_drop_vo: bool = false


func _ready() -> void:
	_camera.current = true
	_tick_player.stream = _make_tick(1850.0, 0.028, 0.22)
	_boot_btn.visible = false
	_place_round()
	_refresh_hud()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("fire"):
		_fire(HidFire.shot_from_bus(AimBus))
		get_viewport().set_input_as_handled()


func _physics_process(delta: float) -> void:
	var sample: AimSample = AimBus.peek()
	_note_lift(sample)
	_move_pad(delta, sample)
	_tick_open_middle(delta)
	_tick_freeze(delta, sample)
	if _vo_t > 0.0:
		_vo_t = maxf(0.0, _vo_t - delta)
	if _miss_t > 0.0:
		_miss_t = maxf(0.0, _miss_t - delta)
		_miss_tick.modulate.a = clampf(_miss_t / 0.055, 0.0, 1.0)
		if _miss_t <= 0.0:
			_miss_tick.visible = false


func _process(_delta: float) -> void:
	_refresh_hud()
	var sample: AimSample = AimBus.peek()
	var size: Vector2 = get_viewport().get_visible_rect().size
	_cross.position = Vector2(sample.uv.x * size.x, sample.uv.y * size.y) - _cross.size * 0.5
	_gun_arm.visible = sample.lifted and not _match_over


func _note_lift(sample: AimSample) -> void:
	if _match_over:
		_was_lifted = sample.lifted
		return
	if sample.lifted and not _was_lifted:
		_vo(VO_LIFT)
	if _was_lifted and not sample.lifted:
		if _pending_drop_vo or _phase != Phase.FREEZE:
			_vo(VO_DROP)
			_pending_drop_vo = false
	_was_lifted = sample.lifted
	if _frozen:
		return
	_phase = Phase.GUN if sample.lifted else Phase.PAD


func _move_pad(_delta: float, sample: AimSample) -> void:
	if _frozen or _match_over:
		_player.velocity.x = 0.0
		_player.velocity.z = 0.0
		_player.velocity.y -= 18.0 * _delta_safe(_delta)
		_player.move_and_slide()
		return
	# WASD only on the mat. Lift locks walk. Superlight is the gun.
	var wish := Vector3.ZERO
	if not sample.lifted:
		wish.x = Input.get_axis("move_left", "move_right")
		wish.z = Input.get_axis("move_back", "move_forward")
	_player.velocity.x = wish.x * SPEED
	_player.velocity.z = -wish.z * SPEED
	_player.velocity.y -= 18.0 * _delta_safe(_delta)
	_player.move_and_slide()


func _delta_safe(delta: float) -> float:
	return delta if delta > 0.0 else (1.0 / 64.0)


func _tick_open_middle(delta: float) -> void:
	if _frozen or _match_over:
		return
	if _in_open_middle(_player.global_position):
		_expose += delta
		if _expose >= EXPOSE_S:
			_die()
	else:
		_expose = 0.0


func _in_left_window(p: Vector3) -> bool:
	return p.x < -4.8 and p.x > -7.5 and p.z > 2.4 and p.z < 5.6


func _in_right_angle(p: Vector3) -> bool:
	return p.x > 4.6 and p.x < 7.5 and p.z > 1.6 and p.z < 5.8


func _in_open_middle(p: Vector3) -> bool:
	if _in_left_window(p) or _in_right_angle(p):
		return false
	if p.z > 0.65:
		return false
	return p.z > -12.5 and absf(p.x) < 7.6


func _fire(sample: AimSample) -> void:
	var vp := get_viewport()
	var size: Vector2 = vp.get_visible_rect().size
	var screen := Hitscan.screen_from_sample(sample, size)
	if _frozen or _match_over:
		_play_miss(screen)
		return
	var origin: Vector3 = _camera.project_ray_origin(screen)
	var dir: Vector3 = _camera.project_ray_normal(screen)
	if not _ray_hits_sphere(origin, dir, _foe.global_position, 0.46):
		_play_miss(screen)
		return
	_you += 1
	_vo(VO_HIT)
	if _you >= TO_WIN:
		_end_match()
		return
	_begin_freeze(true)


func _die() -> void:
	_them += 1
	_expose = 0.0
	if _them >= TO_WIN:
		_end_match()
		return
	_begin_freeze(false)


func _begin_freeze(you_scored: bool) -> void:
	_frozen = true
	_freeze_t = 0.0
	_phase = Phase.FREEZE
	_foe.visible = you_scored
	if AimBus.peek().lifted:
		_pending_drop_vo = true
	else:
		_pending_drop_vo = false


func _tick_freeze(delta: float, sample: AimSample) -> void:
	if not _frozen or _match_over:
		return
	_freeze_t += delta
	# Death freezes. Drop (not lifted) returns you to PAD for the next round.
	if _freeze_t >= FREEZE_PAD_S and not sample.lifted:
		_next_round()


func _next_round() -> void:
	_frozen = false
	_round += 1
	_phase = Phase.PAD
	_place_round()


func _place_round() -> void:
	_player.global_position = SPAWN_A
	_player.velocity = Vector3.ZERO
	_foe.global_position = SPAWN_B
	_foe.visible = true
	_expose = 0.0


func _end_match() -> void:
	_match_over = true
	_frozen = true
	_phase = Phase.MATCH
	_boot_btn.visible = true
	_vo(VO_WIN)


func _vo(line: String) -> void:
	_vo_label.text = line
	_vo_t = VO_S


func _play_miss(screen: Vector2) -> void:
	_miss_t = 0.055
	_miss_tick.visible = true
	_miss_tick.modulate.a = 1.0
	_miss_tick.position = screen - _miss_tick.size * 0.5
	if _tick_player.playing:
		_tick_player.stop()
	_tick_player.play()


func _refresh_hud() -> void:
	var sample: AimSample = AimBus.peek()
	_score_label.text = "CANCHO  %d   —   %d" % [_you, _them]
	_phase_label.text = _phase_name()
	_phase_label.add_theme_color_override("font_color", MINT)
	_score_label.add_theme_color_override("font_color", BONE)
	_vo_label.visible = _vo_t > 0.0
	_vo_label.add_theme_color_override("font_color", BONE)
	if _in_open_middle(_player.global_position) and not _frozen:
		_cover_label.text = "OPEN"
	elif _in_left_window(_player.global_position):
		_cover_label.text = "WINDOW"
	elif _in_right_angle(_player.global_position):
		_cover_label.text = "ANGLE"
	elif sample.lifted:
		_cover_label.text = "LIFT"
	else:
		_cover_label.text = "PAD"
	_hint.text = "WASD on the mat   Space lift   click fires AimSample   first to 5"
	if _match_over:
		_hint.text = VO_WIN + "   first to 5"


func _phase_name() -> String:
	match _phase:
		Phase.PAD:
			return "PAD"
		Phase.GUN:
			return "GUN"
		Phase.FREEZE:
			return "DROP"
		_:
			return "DROP"


func _on_boot() -> void:
	App.go(App.State.BOOT)


func _make_tick(hz: float, seconds: float, vol: float) -> AudioStreamWAV:
	var rate := 22050
	var n := maxi(8, int(float(rate) * seconds))
	var bytes := PackedByteArray()
	bytes.resize(n * 2)
	for i in n:
		var env := 1.0 - float(i) / float(n)
		var s := int(clampf(sin(TAU * hz * float(i) / float(rate)) * env * vol, -1.0, 1.0) * 32767.0)
		bytes[i * 2] = s & 0xFF
		bytes[i * 2 + 1] = (s >> 8) & 0xFF
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = rate
	stream.data = bytes
	return stream


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
