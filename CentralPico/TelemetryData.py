
class ElevatorData:
    def __init__(self, temperature: int = 0, humidity: int = 0, volume: int = 0, weight: int = 0,
                 cooling: bool = False, heating: bool = False) -> None:
        self.temperature = temperature
        self.humidity    = humidity
        self.volume      = volume
        self.weight      = weight
        self.cooling     = cooling
        self.heating     = heating
        
class ScalesData:
    def __init__(self, weight: int = 0, car_presence: bool = False):
        """
            Initialize telemetry values

            Args:
            weight (int): Weight in grams
            car_presence (bool): Whether car is at the gate or not
        """
        self.weight = weight
        self.car_presence = car_presence
