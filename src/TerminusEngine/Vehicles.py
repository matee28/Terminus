class Locomotive:
    """
    Reprezentuje lokomotivu.
    """
    def __init__(self, name: str, max_speed: float, power: float, texture_name: str = "", passenger_capacity: int = 0):
        """
        Inicializuje lokomotivu.

        Args:
            name (str): název
            max_speed (float): maximální rychlost
            power (float): výkon
            texture_name (str): název textury
            passenger_capacity (int; default: 0): kapacita cestujících
        """
        self.name = name
        self.max_speed = max_speed
        self.power = power
        self.texture_name = texture_name
        self.passenger_capacity = passenger_capacity

class PassengerWagon:
    """
    Reprezentuje osobní vagon.
    """
    def __init__(self, name: str, passenger_capacity: int, texture_name: str = ""):
        """
        Inicializuje osobní vagon.

        Args:
            name (str): název
            passenger_capacity (int): kapacita
            texture_name (str): název textury
        """
        self.name = name
        self.passenger_capacity = passenger_capacity
        self.texture_name = texture_name

class CargoWagon:
    """
    Reprezentuje nákladní vagon.
    """
    def __init__(self, name: str, cargo_capacity: float, texture_name: str = ""):
        """
        Inicializuje nákladní vagon.

        Args:
            name (str): název
            cargo_capacity (float): kapacita
            texture_name (str): název textury
        """
        self.name = name
        self.cargo_capacity = cargo_capacity
        self.texture_name = texture_name

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
            wagons (list[PassengerWagon | CargoWagon]): seznam vagonů
        """
        self.name = name
        self.locomotive = locomotive
        self.wagons = wagons
        self.health = 100.0