WORLD_SCALE_M_PX = 8 # kolik px je 1 metr

class WorldGenerator:
    """
    Generuje svět.
    """
    def __init__(self, boundary_radius: float, ):
        """
        Inicializuje generátor světa.

        Args:
            boundary_radius (float): poloměr hranice světa v metrech
        """
        self.boundary_radius = boundary_radius

class City:
    """
    Reprezentuje město.
    """
    def __init__(self, name: str, position: tuple[float, float], population: int):
        """
        Inicializuje město.

        Args:
            name (str): název
            position (tuple[float, float]): pozice (x, y)
            population (int): počet obyvatel
        """
        self.name = name
        self.position = position
        self.population = population
        self.stations = []

class Station:
    """
    Reprezentuje stanici.
    """
    def __init__(self, city: City, name: str, position: tuple[float, float], passenger_capacity: int, cargo_capacity: float, tracks: int):
        """
        Inicializuje stanici.

        Args:
            city (City): město, ve kterém se stanice nachází
            name (str): název
            position (tuple[float, float]): pozice (x, y)
            passenger_capacity (int): kapacita stanice pro osoby
            cargo_capacity (float): kapacita stanice pro nákladní
            tracks (int): počet kolejí ve stanici = počet vlaků, které mohou být ve stanici současně
        """
        self.city = city
        self.name = name
        self.position = position
        self.passenger_capacity = passenger_capacity
        self.cargo_capacity = cargo_capacity
        self.tracks = tracks
        
        self.city.stations.append(self)

class Railway:
    """
    Reprezentuje železniční trať.
    """
    def __init__(self, name: str, stations: list[Station]):
        """
        Inicializuje železniční trať.

        Args:
            name (str): název
            stations (list[Station]): seznam stanic, kterými trať prochází
        """
        self.name = name
        self.stations = stations