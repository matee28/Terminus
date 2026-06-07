import math
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
            cargo_capacity (float; default: 0.0): kapacita nákladu
        """
        self.id = id
        self.name = name
        self.max_speed = max_speed
        self.power = power
        self.price = price
        self.texture_name = texture_name
        self.passenger_capacity = passenger_capacity
        self.cargo_capacity = 0.0
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
        self.cargo_capacity = 0.0
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
        self.passenger_capacity = 0
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
        self.health = 1.0
        self.id = uuid.uuid4().hex

    def get_max_speed(self):
        """Vrátí aktuální maximální rychlost s ohledem na poškození."""
        return self.type.max_speed * self.health

    def get_power(self):
        """Vrátí aktuální výkon s ohledem na poškození."""
        return self.type.power * self.health
        
    def get_passenger_capacity(self):
        """Vrátí aktuální kapacitu cestujících s ohledem na poškození."""
        return math.floor(self.type.passenger_capacity * self.health)

    def get_cargo_capacity(self):
        """Vrátí aktuální kapacitu nákladu s ohledem na poškození."""
        return self.type.cargo_capacity * self.health

    def get_repair_cost(self):
        """Vypočítá cenu opravy."""
        return (1.0 - self.health) * (0.25 * self.type.price)

    def get_sell_price(self):
        """Vrátí prodejní cenu s ohledem na poškození."""
        return self.type.price * self.health

    def repair(self):
        """Opraví lokomotivu."""
        self.health = 1.0

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
        self.health = 1.0
        self.id = uuid.uuid4().hex

    def get_passenger_capacity(self):
        """Vrátí aktuální kapacitu cestujících s ohledem na poškození."""
        return math.floor(self.type.passenger_capacity * self.health)

    def get_cargo_capacity(self):
        """Vrátí aktuální kapacitu nákladu s ohledem na poškození."""
        return self.type.cargo_capacity * self.health

    def get_repair_cost(self):
        """Vypočítá cenu opravy."""
        return (1.0 - self.health) * (0.25 * self.type.price)

    def get_sell_price(self):
        """Vrátí prodejní cenu s ohledem na poškození."""
        return self.type.price * self.health

    def repair(self):
        """Opraví vagon."""
        self.health = 1.0

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
        self.health = 1.0
        self.id = uuid.uuid4().hex

    def get_cargo_capacity(self):
        """Vrátí aktuální kapacitu nákladu s ohledem na poškození."""
        return self.type.cargo_capacity * self.health

    def get_passenger_capacity(self):
        """Vrátí aktuální kapacitu cestujících s ohledem na poškození."""
        return math.floor(self.type.passenger_capacity * self.health)

    def get_repair_cost(self):
        """Vypočítá cenu opravy."""
        return (1.0 - self.health) * (0.25 * self.type.price)

    def get_sell_price(self):
        """Vrátí prodejní cenu s ohledem na poškození."""
        return self.type.price * self.health

    def repair(self):
        """Opraví vagon."""
        self.health = 1.0

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
        self.health = 1.0
        self.id = uuid.uuid4().hex