class_name Hitscan
extends RefCounted

## Hitscan uses the AimSample already in the bus. It does not wait for cv.


static func screen_from_sample(sample: AimSample, view_size: Vector2) -> Vector2:
	if sample == null:
		return view_size * 0.5
	return Vector2(sample.uv.x * view_size.x, sample.uv.y * view_size.y)
