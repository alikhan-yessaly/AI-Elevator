from machine import Timer

def periodic(freq):
    def decorator(func):
        t = Timer()
        t.init(freq=freq, mode=Timer.PERIODIC, callback=func)
        func.deinit = t.deinit
        return func
    return decorator