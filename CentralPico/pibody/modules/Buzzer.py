from machine import Timer
from PWMExt import PWM
from math import e
from time import sleep


class OneShotTimer:
    is_available = True

    def __init__(self, period, callback):
        if not OneShotTimer.is_available:
            return
        OneShotTimer.is_available = False
        self._callback = callback
        self._timer = Timer()
        self._timer.init(
            mode=Timer.ONE_SHOT,
            period=int(period * 1000),
            callback=self._isr
        )

    def _isr(self, t):
        self._timer.deinit()
        OneShotTimer.is_available = True
        self._callback()


class Buzzer(PWM):
    def __init__(self, pin, volume=0.5, freq=560):
        super().__init__(pin)
        self._volume = volume
        self.freq(freq)
        self._is_playing = False
        self._is_muted = False
        self._queue = []

    def volume(self, volume=None):
        if volume is None:
            return self._volume
        self._volume = self._set_duty_by_volume(volume)
    

    MAX_QUEUE = 100
    def make_sound(self, freq, volume, duration, blocking=True):
        if blocking:
            self.freq(freq)
            self._set_duty_by_volume(volume)
            sleep(duration)
            self.duty(0)
        else:
            if(len(self._queue) >= self.MAX_QUEUE):
                return
            self._queue.append((freq, volume, duration))
            if not self._is_playing:
                self._play_next()


    def _play_next(self):
        if not self._queue:
            return
        freq, volume, duration = self._queue.pop(0)
        self._is_playing = True
        self.freq(freq)
        self._set_duty_by_volume(volume)
        OneShotTimer(
            period=duration,
            callback=self._on_timer
        )

    def _on_timer(self):
        self.duty(0)
        self._is_playing = False
        self._play_next()  

    def beep(self):
        self.make_sound(1000, self._volume, 0.1)
    
    def boop(self):
        self.make_sound(500, self._volume, 0.1)
        
    def on(self):
        self._is_muted = False

    def off(self):
        self._is_muted = True

    def _set_duty_by_volume(self, volume):
        volume = max(0, volume)
        volume = min(1, volume)
        volume *= int(not self._is_muted)
        self.duty((volume ** 1.25) / 2)
        return volume
