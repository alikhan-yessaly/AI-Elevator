from machine import Timer

def periodic(freq):
    def decorator(func):
        t = Timer()
        t.init(freq=freq, mode=Timer.PERIODIC, callback=func)
        return func
    return decorator