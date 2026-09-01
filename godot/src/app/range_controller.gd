extends Node3D

## 30-second Range loop. AimSample is the gun — this file only stages orbs and HUD.

enum Phase { PAD, GUN, DROP }

const PAD_END := 3.0
const GUN_END := 27.0
const LOOP_END := 30.0
const POP_S := 0.08
const SPAWN_DELAY_S := 0.18
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


func _ready() -> void:
	_booth_xform = _camera.global_transform
	_camera.current = true
	_first_ever = not FileAccess.file_exists(FIRST_HIT_PATH)
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
	_update_phase()
	_try_flush_spawn()


func _process(_delta: float) -> void:
	_lock_booth_cam()
	_refresh_hud()
	var sample: AimSample = AimBus.peek()
	var size: Vector2 = get_viewport().get_visible_rect().size
	_cross.position = Vector2(sample.uv.x * size.x, sample.uv.y * size.y) - _cross.size * 0.5


func _lock_booth_cam() -> void:
	_camera.global_transform = _booth_xform
	_camera.h_offset = 0.0
	_camera.v_offset = 0.0


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
	_lift.visible = false
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
	_lift.visible = false
	_hide_orb()


func _refresh_hud() -> void:
	var sample: AimSample = AimBus.peek()
	_score_label.text = "SCORE  %d" % _score
	_phase_label.text = _phase_name()
	_conf_label.text = "CONF  %.2f" % sample.confidence
	var remain := maxf(0.0, LOOP_END - _elapsed)
	_countdown.text = "%d" % int(ceil(remain))
	_lift.visible = _phase == Phase.PAD
	if _phase == Phase.PAD and not sample.lifted:
		_phase_label.modulate.a = 0.45 + 0.55 * (0.5 + 0.5 * sin(Time.get_ticks_msec() * 0.009))
	else:
		_phase_label.modulate.a = 1.0


func _phase_name() -> String:
	match _phase:
		Phase.PAD:
			return "PAD"
		Phase.GUN:
			return "GUN"
		_:
			return "DROP"


func _fire(sample: AimSample) -> void:
	# HID peek of the latest AimSample. Miss is a dry tick: no flinch, no VFX.
	if _phase == Phase.DROP:
		return
	if not _orb_live or _popping:
		return
	var vp := get_viewport()
	var size: Vector2 = vp.get_visible_rect().size
	var screen := Vector2(sample.uv.x * size.x, sample.uv.y * size.y)
	var origin: Vector3 = _camera.project_ray_origin(screen)
	var dir: Vector3 = _camera.project_ray_normal(screen)
	if not _ray_hits_sphere(origin, dir, _orb.global_position, _orb_radius):
		return
	_score += 1
	_start_pop()
	if _fat_orb:
		_on_fat_hit()
	else:
		_queue_grid_spawn()
	_refresh_hud()


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
	_orb.visible = true
	_lift.visible = true


func _spawn_grid_orb() -> void:
	_fat_orb = false
	_orb_live = true
	_popping = false
	_orb_radius = GRID_HIT_RADIUS
	_orb.scale = Vector3.ONE
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
