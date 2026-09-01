class_name HidFire
extends RefCounted

## Click is always HID / Raw Input against the latest AimSample.
## Never gate fire on a camera frame. Never wait for the next sample.


static func shot_from_bus(bus: Node) -> AimSample:
	if bus == null:
		return AimSample.new()
	return bus.fire()


static func uses_latest_only() -> bool:
	return true
