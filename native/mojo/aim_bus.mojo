"""AimBus — Latest-sample mailbox in Mojo 1.0."""

from aim_sample import AimSample

struct AimBus(Movable):
    var latest: AimSample

    def __init__(out self):
        self.latest = AimSample(0.5, 0.5, False, False, 0.0, 0)

    def publish(mut self, sample: AimSample):
        self.latest = sample

    def peek(self) -> AimSample:
        return self.latest

    def fire(self) -> AimSample:
        # Atomic peek against mailbox. Never waits on capture frame.
        return self.latest

def main():
    var bus = AimBus()
    var s = AimSample(0.42, 0.68, True, True, 0.98, 1000)
    bus.publish(s)
    var shot = bus.fire()
    print("Mojo AimBus fire:", shot.uv_x, shot.uv_y, "valid:", shot.valid)
