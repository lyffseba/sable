extends Node

enum State { BOOT, MARKER, CALIB, RANGE, BAY, RESULTS, SERVER }

const SCENE := {
	State.BOOT: "res://scenes/boot/Boot.tscn",
	State.MARKER: "res://scenes/boot/Marker.tscn",
	State.CALIB: "res://scenes/boot/Calib.tscn",
	State.RANGE: "res://scenes/range/Range.tscn",
	State.BAY: "res://scenes/bay/Bay.tscn",
	State.RESULTS: "res://scenes/boot/Results.tscn",
}

var state: int = State.BOOT


func _ready() -> void:
	if _is_headless():
		state = State.SERVER
		await _run_headless()
		return


func _is_headless() -> bool:
	if OS.has_feature("dedicated_server"):
		return true
	if DisplayServer.get_name() == "headless":
		return true
	return "--server" in OS.get_cmdline_user_args() or "--server" in OS.get_cmdline_args()


func go(next: int) -> void:
	state = next
	if next == State.SERVER:
		_run_headless()
		return
	var path: String = SCENE.get(next, SCENE[State.BOOT])
	get_tree().change_scene_to_file(path)


func _run_headless() -> void:
	print("SABLE dedicated server boot")
	print("tick=64 Hz  net=ENet  aim=HID+cv_input")
	var ticks := 0
	while ticks < 8:
		await get_tree().physics_frame
		ticks += 1
	print("SABLE headless tick ok ticks=", ticks)
	if "--stay" in OS.get_cmdline_args() or "--stay" in OS.get_cmdline_user_args():
		return
	get_tree().quit(0)
