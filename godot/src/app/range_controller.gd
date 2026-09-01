extends Node3D

## 30-second Range loop. AimSample is the gun — this file only stages orbs and HUD.

enum Phase { PAD, GUN, DROP }

const PAD_END := 3.0
const GUN_END := 27.0
const LOOP_END := 30.0
const POP_S := 0.08
const SPAWN_DELAY_S := 0.18
const PING_S := 0.10
const MISS_TICK_S := 0.055
const MEDAL_S := 0.40
const FIRST_HIT_PATH := "user://range_first_hit.flag"

const FAT_SCALE := 1.85
const FAT_HIT_RADIUS := 0.70
const GRID_HIT_RADIUS := 0.38
const ORB_Y := 1.4
const FAT_POS := Vector3(0.0, 1.4, -1.6)
const LANE_X := [-2.5, 0.0, 2.5]
const DEPTH_Z := [2.0, -1.4, -5.0]

@onready var _camera: Camera3D = $Camera3D
@onready var _orb: MeshInstance3D = $DummyOrb
@onready var _score_label: Label = $HUD/Score
@onready var _phase_label: Label = $HUD/ModeChip
@onready var _conf_label: Label = $HUD/Confidence
@onready var _cross: Control = $HUD/Crosshair
@onready var _countdown: Label = $HUD/Countdown
@onready var _lift: Label = $HUD/LiftPrompt
@onready var _hit_ping: ColorRect = $HUD/HitPing
@onready var _miss_tick: ColorRect = $HUD/MissTick
@onready var _tick_player: AudioStreamPlayer = $TickPlayer

var _score: int = 0
var _elapsed: float = 0.0
var _phase: int = Phase.PAD
var _orb_live: bool = true
var _orb_radius: float = FAT_HIT_RADIUS
var _fat_orb: bool = true
var _fat_hit: bool = false
var _first_ever: bool = true
var _last_lane: int = 1
var _last_depth: int = 1
var _cell_step: int = 0
var _booth_xform := Transform3D.IDENTITY
var _popping: bool = false
var _pop_t: float = 0.0
var _pop_base := Vector3.ONE
var _pending_grid: bool = false
var _spawn_at: float = -1.0
var _ping_t: float = 0.0
var _miss_t: float = 0.0
var _medal_t: float = 0.0
var _saw_lift: bool = false
var _was_lifted: bool = false


func _ready() -> void:
	_booth_xform = _camera.global_transform
	_camera.current = true
	_first_ever = not FileAccess.file_exists(FIRST_HIT_PATH)
	_tick_player.stream = _make_tick(1850.0, 0.028, 0.22)
	_hit_ping.visible = false
	_miss_tick.visible = false
	_show_fat_orb()
	_refresh_hud()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("fire"):
		_fire(HidFire.shot_from_bus(AimBus))
		get_viewport().set_input_as_handled()


func _physics_process(delta: float) -> void:
	_lock_booth_cam()
	if _elapsed < LOOP_END:
		_elapsed = minf(_elapsed + delta, LOOP_END)
	_tick_pop(delta)
	_tick_juice(delta)
	_update_phase()
	_try_flush_spawn()


func _process(_delta: float) -> void:
	_lock_booth_cam()
	_refresh_hud()
	var sample: AimSample = AimBus.peek()
	var size: Vector2 = get_viewport().get_visible_rect().size
	_cross.position = Vector2(sample.uv.x * size.x, sample.uv.y * size.y) - _cross.size * 0.5
	_note_lift(sample)
	if _hit_ping.visible:
		_place_hit_ping()


func _lock_booth_cam() -> void:
	_camera.global_transform = _booth_xform
	_camera.h_offset = 0.0
	_camera.v_offset = 0.0


func _note_lift(sample: AimSample) -> void:
	# First lifted this run is the medal: the existing LIFT chip, 400ms.
	if sample.lifted and not _was_lifted and not _saw_lift:
		_saw_lift = true
		_medal_t = MEDAL_S
	_was_lifted = sample.lifted


func _tick_juice(delta: float) -> void:
	if _ping_t > 0.0:
		_ping_t = maxf(0.0, _ping_t - delta)
		var u := clampf(_ping_t / PING_S, 0.0, 1.0)
		_hit_ping.modulate.a = u
		_hit_ping.scale = Vector2(1.0 + 0.8 * (1.0 - u), 1.0 + 0.8 * (1.0 - u))
		if _ping_t <= 0.0:
			_hit_ping.visible = false
			_orb.modulate = Color.WHITE
	if _miss_t > 0.0:
		_miss_t = maxf(0.0, _miss_t - delta)
		_miss_tick.modulate.a = clampf(_miss_t / MISS_TICK_S, 0.0, 1.0)
		if _miss_t <= 0.0:
			_miss_tick.visible = false
	if _medal_t > 0.0:
		_medal_t = maxf(0.0, _medal_t - delta)


func _update_phase() -> void:
	if _phase != Phase.DROP and _elapsed >= GUN_END:
		_enter_drop()
		return
	if _phase == Phase.PAD and _can_leave_pad():
		_enter_gun()


func _can_leave_pad() -> bool:
	if _elapsed < PAD_END:
		return false
	if _first_ever and not _fat_hit:
		return false
	return true


func _enter_gun() -> void:
	_phase = Phase.GUN
	if _orb_live and _fat_orb:
		_hide_orb()
		_spawn_grid_orb()
		return
	_try_flush_spawn()
	if not _orb_live and not _pending_grid and not _popping:
		_spawn_grid_orb()


func _enter_drop() -> void:
	_phase = Phase.DROP
	_pending_grid = false
	_spawn_at = -1.0
	_popping = false
	_hide_orb()


func _refresh_hud() -> void:
	var sample: AimSample = AimBus.peek()
	_score_label.text = "SCORE  %d" % _score
	_phase_label.text = _phase_name()
	_conf_label.text = "CONF  %.2f" % sample.confidence
	var remain := maxf(0.0, LOOP_END - _elapsed)
	_countdown.text = "%d" % int(ceil(remain))
	var medal := _medal_t > 0.0
	_lift.visible = _phase == Phase.PAD or medal
	if _phase == Phase.PAD and not sample.lifted:
		_phase_label.modulate.a = 0.45 + 0.55 * (0.5 + 0.5 * sin(Time.get_ticks_msec() * 0.009))
	else:
		_phase_label.modulate.a = 1.0
	if _phase == Phase.DROP:
		_countdown.modulate.a = 0.40 + 0.60 * (0.5 + 0.5 * sin(Time.get_ticks_msec() * 0.014))
	else:
		_countdown.modulate.a = 1.0
	if medal:
		_lift.modulate.a = 1.0
	else:
		_lift.modulate.a = 1.0 if _phase == Phase.PAD else 0.0


func _phase_name() -> String:
	match _phase:
		Phase.PAD:
			return "PAD"
		Phase.GUN:
			return "GUN"
		_:
			return "DROP"


func _fire(sample: AimSample) -> void:
	# HID peek of the latest AimSample. Miss is a dry tick that must read.
	var vp := get_viewport()
	var size: Vector2 = vp.get_visible_rect().size
	var screen := Vector2(sample.uv.x * size.x, sample.uv.y * size.y)
	if _phase == Phase.DROP:
		_play_miss(screen)
		return
	if not _orb_live or _popping:
		_play_miss(screen)
		return
	var origin: Vector3 = _camera.project_ray_origin(screen)
	var dir: Vector3 = _camera.project_ray_normal(screen)
	if not _ray_hits_sphere(origin, dir, _orb.global_position, _orb_radius):
		_play_miss(screen)
		return
	_score += 1
	_start_pop()
	_play_hit_ping()
	if _fat_orb:
		_on_fat_hit()
	else:
		_queue_grid_spawn()
	_refresh_hud()


func _play_hit_ping() -> void:
	_ping_t = PING_S
	_orb.modulate = Color(1.55, 1.55, 1.45)
	_hit_ping.visible = true
	_hit_ping.modulate.a = 1.0
	_hit_ping.scale = Vector2.ONE
	_place_hit_ping()


func _place_hit_ping() -> void:
	var sp: Vector2 = _camera.unproject_position(_orb.global_position)
	_hit_ping.position = sp - _hit_ping.size * 0.5 * _hit_ping.scale


func _play_miss(screen: Vector2) -> void:
	_miss_t = MISS_TICK_S
	_miss_tick.visible = true
	_miss_tick.modulate.a = 1.0
	_miss_tick.position = screen - _miss_tick.size * 0.5
	if _tick_player.playing:
		_tick_player.stop()
	_tick_player.play()


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


func _start_pop() -> void:
	_orb_live = false
	_popping = true
	_pop_t = 0.0
	_pop_base = _orb.scale


func _tick_pop(delta: float) -> void:
	if not _popping:
		return
	_pop_t += delta
	var u := clampf(_pop_t / POP_S, 0.0, 1.0)
	_orb.scale = _pop_base * (1.0 + 0.4 * sin(PI * u))
	if _pop_t >= POP_S:
		_popping = false
		_orb.visible = false
		_orb.scale = _pop_base
		_orb.modulate = Color.WHITE


func _on_fat_hit() -> void:
	_fat_hit = true
	_mark_first_hit()
	_first_ever = false
	_fat_orb = false
	_queue_grid_spawn()
	if _elapsed >= PAD_END:
		_enter_gun()


func _queue_grid_spawn() -> void:
	_pending_grid = true
	_spawn_at = _elapsed + SPAWN_DELAY_S


func _try_flush_spawn() -> void:
	if not _pending_grid:
		return
	if _elapsed < _spawn_at:
		return
	if _phase != Phase.GUN:
		return
	_pending_grid = false
	_spawn_at = -1.0
	if _elapsed >= GUN_END:
		return
	_spawn_grid_orb()


func _show_fat_orb() -> void:
	_fat_orb = true
	_orb_live = true
	_orb_radius = FAT_HIT_RADIUS
	_orb.scale = Vector3(FAT_SCALE, FAT_SCALE, FAT_SCALE)
	_orb.position = FAT_POS
	_orb.modulate = Color.WHITE
	_orb.visible = true
	_lift.visible = true


func _spawn_grid_orb() -> void:
	_fat_orb = false
	_orb_live = true
	_popping = false
	_orb_radius = GRID_HIT_RADIUS
	_orb.scale = Vector3.ONE
	_orb.modulate = Color.WHITE
	var cell := _next_cell()
	_orb.position = Vector3(LANE_X[cell.x], ORB_Y, DEPTH_Z[cell.y])
	_orb.visible = true


func _next_cell() -> Vector2i:
	# L/C/R × near/mid/far. Step so the Superlight has to move.
	_cell_step += 1
	var idx := _cell_step % 9
	var lane := idx % 3
	var depth := int(idx / 3)
	if lane == _last_lane and depth == _last_depth:
		_cell_step += 1
		idx = _cell_step % 9
		lane = idx % 3
		depth = int(idx / 3)
	_last_lane = lane
	_last_depth = depth
	return Vector2i(lane, depth)


func _hide_orb() -> void:
	_orb_live = false
	_fat_orb = false
	_popping = false
	_orb.visible = false
	_orb.modulate = Color.WHITE


func _mark_first_hit() -> void:
	var f := FileAccess.open(FIRST_HIT_PATH, FileAccess.WRITE)
	if f != null:
		f.store_string("1")


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
