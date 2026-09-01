extends Control

@export var title_text: String = "STUB"
@export var next_state: int = 0


func _ready() -> void:
	$Center/Column/Title.text = title_text


func _on_continue() -> void:
	App.go(next_state)
