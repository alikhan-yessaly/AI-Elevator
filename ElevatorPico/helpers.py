from machine import Timer

def periodic(freq):
    def decorator(func):
        t = Timer()
        t.init(freq=freq, mode=Timer.PERIODIC, callback=func)
        return t   # caller holds the timer handle for deinit
    return decorator