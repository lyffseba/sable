class_name AimSample
extends RefCounted

## Shared aim contract. No engine-only fields beyond Vector2 for UV.
var uv: Vector2 = Vector2(0.5, 0.5)
var valid: bool = false
var lifted: bool = false
var confidence: float = 0.0
var t_hw: int = 0


func duplicate_sample() -> AimSample:
	var copy := AimSample.new()
	copy.uv = uv
	copy.valid = valid
	copy.lifted = lifted
	copy.confidence = confidence
	copy.t_hw = t_hw
	return copy


func is_seeking() -> bool:
	return (not valid) or confidence < 0.35
