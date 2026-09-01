extends Node

## Latest AimSample mailbox. HID fire peeks this. It never waits on a camera frame.
var _latest: AimSample = AimSample.new()


func publish(sample: AimSample) -> void:
	if sample == null:
		return
	_latest = sample


func peek() -> AimSample:
	return _latest


## Fire contract: return the last published sample even if the current
## camera frame is missing. Do not wait. Do not poll capture.
func fire() -> AimSample:
	return _latest
