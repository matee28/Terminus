import random
import math


class City:
    """
    Reprezentuje město.
    """
    def __init__(self, name: str, position: tuple[float, float], radius: float, population: int):
        """
        Inicializuje město.

        Args:
            name (str): název
            position (tuple[float, float]): pozice (x, y)
            radius (float): poloměr města
            population (int): počet obyvatel
        """
        self.name = name
        self.position = position
        self.radius = radius
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



class World:
    """
    Reprezentuje svět.
    """
    def __init__(self, cities: list[City]):
        """
        Inicializuje svět.

        Args:
            cities (list[City]): seznam měst
        """
        self.cities = cities

    def __str__(self):
        return "Města:\n" + "\n".join(["\t{} (populace: {}, pozice: {}\n\t\t{})".format(
            city.name, 
            city.population, 
            city.position, 
            '\n\t\t'.join([f'{s.name} {s.position}' for s in city.stations])
        ) for city in self.cities])


# TODO: stále jsou hardcoded hodnoty jako kapacita stanic a počet kolejí
def WorldGenerator(
        world_boundary: int,

        city_names: list[str],
        cities: int,
        small_city_max_population: int,
        large_city_max_population: int,
        max_city_boundary: int,

        max_stations_per_city: int,
        passenger_station_names: list[str],
        cargo_station_names: list[str]
    ):

    """
    Generuje svět.

    Args:
        world_boundary (int): velikost hranice světa v metrech (pro generování měst atd.)
        city_names (list[str]): seznam názvů pro města
        cities (int): počet měst, které se mají vygenerovat
        small_city_max_population (int): maximální počet obyvatel v malém městě
        large_city_max_population (int): maximální počet obyvatel v velkém městě
        max_city_boundary (int): maximální velikost města v metrech (pro generování stanic atd.)
        max_stations_per_city (int): maximální počet stanic, které mohou být v jednom městě
        passenger_station_names (list[str]): seznam názvů pro osobní stanice
        cargo_station_names (list[str]): seznam názvů pro nákladní stanice
    """

    if (len(city_names) < cities) or (len(passenger_station_names) < max_stations_per_city) or (len(cargo_station_names) < max_stations_per_city):
        raise ValueError("Není dostatek názvů pro generování světa.")
    
    if small_city_max_population < 1:
        raise ValueError("Maximální počet obyvatel v malém městě musí být alespoň 1.")
    
    if small_city_max_population >= large_city_max_population:
        raise ValueError("Maximální počet obyvatel v malém městě musí být menší než ve velkém městě.")
    
    if max_stations_per_city < 1:
        raise ValueError("Maximální počet stanic v městě musí být alespoň 1.")

    def generate_station_position(position: tuple[float, float]):
        return (position[0] + random.randint(-max_city_boundary, max_city_boundary), position[1] + random.randint(-max_city_boundary, max_city_boundary))

    # rozdělení mapy do mřížky pro rovnoměrné rozprostření měst (= Jittered Grid)
    grid_size = math.ceil(math.sqrt(cities))
    cell_size = (2 * world_boundary) / grid_size
    available_cells = [(x, y) for x in range(grid_size) for y in range(grid_size)]
    random.shuffle(available_cells)

    # výběr náhodných měst
    selected_city_names = random.sample(city_names, cities)
    
    generated_cities = []
    for i, city_name in enumerate(selected_city_names):

        # rozhodnutí, zda je město velké nebo malé
        is_large = random.choice([True, False])

        if is_large:
            population = random.randint(small_city_max_population + 1, large_city_max_population)
        else:
            population = random.randint(1, small_city_max_population)

        city_radius = population / large_city_max_population * max_city_boundary

        # získání nezabrané buňky z mřížky
        cell_x, cell_y = available_cells[i]
        
        # střed buňky
        center_x = -world_boundary + cell_x * cell_size + cell_size / 2
        center_y = -world_boundary + cell_y * cell_size + cell_size / 2
        
        # o kolik se město může náhodně odchýlit od středu, aby nezasáhlo do sousední buňky
        jitter = max(0.0, (cell_size / 2) - city_radius)
        
        position = (
            center_x + random.uniform(-jitter, jitter),
            center_y + random.uniform(-jitter, jitter)
        )

        city = City(name=city_name, position=position, radius=city_radius, population=population)

        if is_large: # velké město -> více stanic
            if max_stations_per_city > 1:
                num_stations = random.randint(2, max_stations_per_city)
            else:
                num_stations = 1

            city_pass_names = random.sample(passenger_station_names, num_stations)
            city_cargo_names = random.sample(cargo_station_names, num_stations)
            city_station_types = [True] + random.choices([True, False], k=num_stations-1) # zaručuje alespoň jednu osobní stanici
            
            for i in range(num_stations):
                # rozhodnutí, zda je stanice nákladní nebo osobní
                is_cargo = not city_station_types[i]
                
                station_position = generate_station_position(city.position)

                if is_cargo:
                    station_name = f"{city_name}-{city_cargo_names[i].capitalize()}"
                    Station(city=city, name=station_name, position=station_position, passenger_capacity=0, cargo_capacity=random.uniform(500, 5000), tracks=random.randint(1, 4))
                else:
                    station_name = f"{city_name}-{city_pass_names[i].capitalize()}"
                    Station(city=city, name=station_name, position=station_position, passenger_capacity=random.randint(200, 2000), cargo_capacity=0, tracks=random.randint(1, 4))

        else: # malé město
            Station(city=city, name=city_name, position=generate_station_position(city.position), passenger_capacity=random.randint(50, 300), cargo_capacity=random.uniform(50, 300), tracks=1)
            
        generated_cities.append(city)

    return World(cities=generated_cities)