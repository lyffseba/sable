class_name HudChip
extends RefCounted


static func format_mode(name: String, confidence: float) -> String:
	if confidence < 0.35 and name != "DESKTOP":
		return "SEEKING"
	return name
