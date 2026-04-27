from PWMExt import PWM

SERVO_PERIOD_MS = 20

def angle2duty(angle):
    pulse_width = (angle / 180) * 2 + 0.5
    duty = pulse_width / SERVO_PERIOD_MS
    return duty


class Servo:
    def __init__(self, pin):
        self.servo = PWM(pin)
        self.servo.freq(1000//SERVO_PERIOD_MS)
        self._angle = None


    def angle(self, angle=None):
        if angle is None:
            return self._angle
        else:
            self._angle = angle
            duty = angle2duty(angle)
            self.servo.duty(duty)
    # TODO: Check how those work
    def on(self):
        self.servo.init()
        
    def off(self):
        self.servo.deinit()