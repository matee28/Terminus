class Locomotive:
    """
    Reprezentuje lokomotivu.
    """
    def __init__(self, name: str, max_speed: float, power: float):
        """
        Inicializuje lokomotivu.

        Args:
            name (str): název
            max_speed (float): maximální rychlost
            power (float): výkon
        """
        self.name = name
        self.max_speed = max_speed
        self.power = power

class PassengerWagon:
    """
    Reprezentuje osobní vagon.
    """
    def __init__(self, name: str, passenger_capacity: int):
        """
        Inicializuje osobní vagon.

        Args:
            name (str): název
            passenger_capacity (int): kapacita
        """
        self.name = name
        self.passenger_capacity = passenger_capacity

class CargoWagon:
    """
    Reprezentuje nákladní vagon.
    """
    def __init__(self, name: str, cargo_capacity: float):
        """
        Inicializuje nákladní vagon.

        Args:
            name (str): název
            cargo_capacity (float): kapacita
        """
        self.name = name
        self.cargo_capacity = cargo_capacity

class Train:
    """
    Reprezentuje vlakovou soupravu.
    """
    def __init__(self, name: str, locomotive: Locomotive, wagons: list[PassengerWagon | CargoWagon]):
        """
        Inicializuje vlakovou soupravu.

        Args:
            name (str): název
            locomotive (Locomotive): lokomotiva
            wagons (list[PassengerWagon  |  CargoWagon]): seznam vozů
        """
        self.name = name
        self.locomotive = locomotive
        self.wagons = wagons
        self.health = 100.0