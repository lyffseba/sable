"""OneEuro — Adaptive low-pass pointing filter in Mojo 1.0.

Casiez, Roussel, Vogel 2012. Tuned for physical light-gun aiming.
"""

comptime PI: Float64 = 3.141592653589793

struct LowPass(Copyable, Movable, ImplicitlyCopyable):
    var hat: Float64
    var initialized: Bool

    def __init__(out self, init_val: Float64 = 0.0):
        self.hat = init_val
        self.initialized = False

    def reset(mut self, init_val: Float64 = 0.0):
        self.hat = init_val
        self.initialized = False

    def filter(mut self, value: Float64, alpha: Float64) -> Float64:
        if not self.initialized:
            self.hat = value
            self.initialized = True
            return self.hat

        var a = alpha
        if a < 0.0:
            a = 0.0
        elif a > 1.0:
            a = 1.0
        self.hat = a * value + (1.0 - a) * self.hat
        return self.hat

struct OneEuro(Copyable, Movable, ImplicitlyCopyable):
    var mincutoff: Float64
    var beta: Float64
    var dcutoff: Float64
    var freq: Float64
    var x: LowPass
    var dx: LowPass
    var last_t_s: Float64

    def __init__(
        out self,
        mincutoff: Float64 = 3.0,
        beta: Float64 = 0.03,
        dcutoff: Float64 = 1.0,
        freq: Float64 = 60.0,
    ):
        self.mincutoff = mincutoff
        self.beta = beta
        self.dcutoff = dcutoff
        self.freq = freq
        self.x = LowPass(0.0)
        self.dx = LowPass(0.0)
        self.last_t_s = -1.0

    def reset(mut self):
        self.x.reset()
        self.dx.reset()
        self.last_t_s = -1.0

    def alpha(self, cutoff: Float64, dt: Float64) -> Float64:
        var tau = 1.0 / (2.0 * PI * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def filter(mut self, value: Float64, t_s: Float64) -> Float64:
        var dt = 1.0 / self.freq
        if self.last_t_s >= 0.0 and t_s > self.last_t_s:
            dt = t_s - self.last_t_s
        if dt <= 1e-6:
            dt = 1.0 / self.freq

        var rate = 1.0 / dt
        var dvalue = Float64(0.0)
        if self.x.initialized:
            dvalue = (value - self.x.hat) * rate

        var edvalue = self.dx.filter(dvalue, self.alpha(self.dcutoff, dt))
        var abs_edv = edvalue if edvalue >= 0 else -edvalue
        var cutoff = self.mincutoff + self.beta * abs_edv
        var result = self.x.filter(value, self.alpha(cutoff, dt))
        self.last_t_s = t_s
        return result

def main():
    var f = OneEuro(3.0, 0.03, 1.0, 60.0)
    var out = f.filter(100.0, 0.016)
    print("Mojo OneEuro step 1:", out)
    var out2 = f.filter(102.0, 0.032)
    print("Mojo OneEuro step 2:", out2)
