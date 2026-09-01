extends Control

@onready var _status: Label = $Center/Column/Status


func _ready() -> void:
	if OS.has_feature("dedicated_server") or DisplayServer.get_name() == "headless":
		return
	_status.text = "desktop aim ready  ·  T desktop  ·  Space force gun"


func _on_enable_camera() -> void:
	var ok: bool = AimService.enable_camera()
	if ok:
		_status.text = "cv_input bound"
	else:
		_status.text = "cv_input missing — DESKTOP aim"
	App.go(App.State.RANGE)


func _on_enter_range() -> void:
	App.go(App.State.RANGE)


func _on_enter_bay() -> void:
	App.go(App.State.BAY)
