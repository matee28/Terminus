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
    def __init__(self, city: City, name: str, position: tuple[float, float], capacity: int, tracks: int):
        """
        Inicializuje stanici.

        Args:
            city (City): město, ve kterém se stanice nachází
            name (str): název
            position (tuple[float, float]): pozice (x, y)
            capacity (int): kapacita stanice
            tracks (int): počet kolejí ve stanici
        """
        self.city = city
        self.name = name
        self.position = position
        self.capacity = capacity
        self.tracks = tracks
        
        self.city.stations.append(self)