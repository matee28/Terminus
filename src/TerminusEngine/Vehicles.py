import uuid

class LocomotiveType:
    """
    Reprezentuje typ lokomotivy.
    """
    def __init__(self, id: str, name: str, max_speed: float, power: float, weight: float, price: float = 0.0, texture_name: str = "", passenger_capacity: int = 0):
        """
        Inicializuje typ lokomotivy.

        Args:
            id (str): unikátní identifikátor typu
            name (str): název
            max_speed (float): maximální rychlost
            power (float): výkon
            weight (float): hmotnost v tunách
            price (float): cena
            texture_name (str): název textury
            passenger_capacity (int; default: 0): kapacita cestujících
        """
        self.id = id
        self.name = name
        self.max_speed = max_speed
        self.power = power
        self.price = price
        self.texture_name = texture_name
        self.passenger_capacity = passenger_capacity
        self.weight = weight

class PassengerWagonType:
    """
    Reprezentuje typ osobního vagonu.
    """
    def __init__(self, id: str, name: str, passenger_capacity: int, weight: float, price: float = 0.0, texture_name: str = ""):
        """
        Inicializuje typ osobního vagonu.

        Args:
            id (str): unikátní identifikátor typu
            name (str): název
            passenger_capacity (int): kapacita
            weight (float): hmotnost v tunách
            price (float): cena
            texture_name (str): název textury
        """
        self.id = id
        self.name = name
        self.passenger_capacity = passenger_capacity
        self.price = price
        self.texture_name = texture_name
        self.weight = weight

class CargoWagonType:
    """
    Reprezentuje typ nákladního vagonu.
    """
    def __init__(self, id: str, name: str, cargo_capacity: float, weight: float, price: float = 0.0, texture_name: str = ""):
        """
        Inicializuje typ nákladního vagonu.

        Args:
            id (str): unikátní identifikátor typu
            name (str): název
            cargo_capacity (float): kapacita
            weight (float): hmotnost v tunách
            price (float): cena
            texture_name (str): název textury
        """
        self.id = id
        self.name = name
        self.cargo_capacity = cargo_capacity
        self.price = price
        self.texture_name = texture_name
        self.weight = weight

class Locomotive:
    """
    Reprezentuje instanci lokomotivy.
    """
    def __init__(self, type_: LocomotiveType):
        """
        Inicializuje instanci lokomotivy z daného typu.

        Args:
            type_ (LocomotiveType): typ lokomotivy
        """
        self.type = type_
        self.health = 100.0
        self.id = uuid.uuid4().hex

class PassengerWagon:
    """
    Reprezentuje instanci osobního vagonu.
    """
    def __init__(self, type_: PassengerWagonType):
        """
        Inicializuje instanci osobního vagonu z daného typu.

        Args:
            type_ (PassengerWagonType): typ vagonu
        """
        self.type = type_
        self.health = 100.0
        self.id = uuid.uuid4().hex

class CargoWagon:
    """
    Reprezentuje instanci nákladního vagonu.
    """
    def __init__(self, type_: CargoWagonType):
        """
        Inicializuje instanci nákladního vagonu z daného typu.

        Args:
            type_ (CargoWagonType): typ vagonu
        """
        self.type = type_
        self.health = 100.0
        self.id = uuid.uuid4().hex

class Train:
    """
    Reprezentuje instanci vlakové soupravy.
    """
    def __init__(self, name: str, locomotive: Locomotive, wagons: list[PassengerWagon | CargoWagon]):
        """
        Inicializuje vlakovou soupravu (instanci).

        Args:
            name (str): název soupravy
            locomotive (Locomotive): připojená lokomotiva (instance)
            wagons (list[PassengerWagon | CargoWagon]): připojené vagony (instance)
        """
        self.name = name
        self.locomotive = locomotive
        self.wagons = wagons
        self.health = 100.0
        self.id = uuid.uuid4().hex