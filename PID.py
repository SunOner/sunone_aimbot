class PID:
    def __init__(self, dt, max, min, Kp, Ki, Kd):
        self.dt = dt
        self.max = max
        self.min = min
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.integral = 0
        self.pre_error = 0

    def calculate(self, setPoint, pv):
        output = self.Kp * setPoint - pv + self.Ki + self.Kd

        if (output > self.max):
            output = self.max
        elif (output < self.min):
            output = self.min

        # self.pre_error = error
        return output


