"""AimSample — shared aim contract in Mojo 1.0."""

@fieldwise_init
struct AimSample(Copyable, Movable, ImplicitlyCopyable):
    var uv_x: Float32
    var uv_y: Float32
    var valid: Bool
    var lifted: Bool
    var confidence: Float32
    var t_hw: Int64

    def is_equal(self, other: AimSample) -> Bool:
        return (
            self.uv_x == other.uv_x
            and self.uv_y == other.uv_y
            and self.valid == other.valid
            and self.lifted == other.lifted
            and self.confidence == other.confidence
            and self.t_hw == other.t_hw
        )

def main():
    var s = AimSample(0.5, 0.5, True, True, 0.95, 42)
    print("Mojo AimSample initialized: uv_x=", s.uv_x, " valid=", s.valid)
