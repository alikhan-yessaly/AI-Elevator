
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
    def __init__(self, weight: int = 0, car_presence: bool = False, last_net_weight: int = 0, last_car_id: int = 0):
        self.weight = weight
        self.car_presence = car_presence
        self.last_net_weight = last_net_weight
        self.last_car_id = last_car_id
