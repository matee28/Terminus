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

    def add_station(self, station):
        """
        Přidá stanici k městu.
        """
        self.stations.append(station)

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
        self.passengers = 0
        self.cargo_capacity = cargo_capacity
        self.tracks = tracks
        
        self.city.add_station(self)

class Railway:
    """
    Reprezentuje železniční trať.
    """
    def __init__(self, station_a: Station, station_b: Station, points: list[tuple[float, float]] = []):
        """
        Inicializuje železniční trať.

        Args:
            station_a (Station): počáteční stanice
            station_b (Station): konečná stanice
            points (list[tuple[float, float]]): seznam bodů trati
        """
        self.station_a = station_a
        self.station_b = station_b
        self.points = points

    def replace_points(self, new_points: list[tuple[float, float]]):
        """
        Nahradí body trati.

        Args:
            new_points (list[tuple[float, float]]): nový seznam bodů trati
        """
        self.points = new_points

    def add_point(self, point: tuple[float, float]):
        """
        Přidá bod na konec trati.

        Args:
            point (tuple[float, float]): bod, který se má přidat
        """
        self.points.append(point)

    def remove_last_point(self):
        """
        Odstraní poslední bod z trati.
        """
        if len(self.points) > 0:
            self.points.pop()


class Route:
    """
    Reprezentuje vlakový spoj.
    """
    def __init__(self, name: str, stations: list[Station], stop_flags: list[bool], railways: list[Railway]):
        """
        Inicializuje spoj.

        Args:
            name (str): název spoje
            stations (list[Station]): seznam stanic (od počáteční po koncovou)
            stop_flags (list[bool]): zda ve stanici vlak zastavuje
            railways (list[Railway]): tratě spojující stanice
        """
        self.name = name
        self.stations = stations
        self.stop_flags = stop_flags
        self.railways = railways


class ActiveTrain:
    """
    Reprezentuje aktivní vlak na spoji.
    """
    def __init__(self, train, route: Route):
        """
        Inicializuje aktivní vlak.
        
        Args:
            train (Train): vlaková souprava
            route (Route): spoj, po kterém vlak jede
        """
        self.train = train
        self.route = route
        self.current_leg_index = 0
        self.forward = True
        self.leg_distance = 0.0
        self.passengers = 0
        self.railway_dir = 1
        self.wait_timer = 0.0
        self.current_stop_station = None
        
        self._setup_leg()

    def _setup_leg(self):
        if len(self.route.railways) == 0:
            return
            
        rw = self.route.railways[self.current_leg_index]
        if self.forward:
            from_station = self.route.stations[self.current_leg_index]
        else:
            from_station = self.route.stations[self.current_leg_index + 1]
            
        if rw.station_a == from_station:
            self.railway_dir = 1
        else:
            self.railway_dir = -1
        self.leg_distance = 0.0

    def get_passenger_capacity(self):
        """Vrátí celkovou kapacitu osobního vlaku."""
        cap = getattr(self.train.locomotive.type, "passenger_capacity", 0)
        for wagon in self.train.wagons:
            cap += getattr(wagon.type, "passenger_capacity", 0)
        return cap

class World:
    """
    Reprezentuje svět.
    """
    def __init__(self, cities: list[City], railways: list[Railway] = [], active_trains: list[ActiveTrain] = []):
        """
        Inicializuje svět.

        Args:
            cities (list[City]): seznam měst
            railways (list[Railway]): seznam železničních tratí
            active_trains (list[ActiveTrain]): seznam aktivních vlaků
        """
        self.cities = cities
        self.railways = railways
        self.active_trains = active_trains

    def update(self, dt_seconds: float, time_scale: float, train_speed_multiplier: float, passenger_generation_rate: float, get_point_func: callable):
        """
        Aktualizuje stav světa, generování cestujících a pohyb vlaků.
        """
        # aktualizace stanic; generování cestujících ve stanicích (kde reálně zastavuje nějaký spoj)
        served_stations = set()
        for at in self.active_trains:
            for i, st in enumerate(at.route.stations):
                if at.route.stop_flags[i]:
                    served_stations.add(st)
            
        for city in self.cities:
            for station in city.stations:
                if station in served_stations and station.passenger_capacity > 0:
                    if station.passengers < station.passenger_capacity:
                        generated = passenger_generation_rate * dt_seconds * time_scale
                        station.passengers = min(station.passenger_capacity, station.passengers + generated)
        
        # aktualizace vlaků
        for at in self.active_trains:
            if len(at.route.railways) == 0:
                continue
                
            if at.wait_timer > 0:
                at.wait_timer -= dt_seconds * time_scale
                
                if at.current_stop_station:
                    capacity = at.get_passenger_capacity()
                    free_space = capacity - at.passengers
                    if free_space > 0 and at.current_stop_station.passengers >= 1:
                        to_load = min(free_space, int(at.current_stop_station.passengers))
                        at.current_stop_station.passengers -= to_load
                        at.passengers += to_load

                if at.wait_timer > 0:
                    continue

            speed_m_s = at.train.locomotive.type.max_speed / 3.6
            moved_dist = speed_m_s * dt_seconds * time_scale * train_speed_multiplier
            at.leg_distance += moved_dist
            
            rw = at.route.railways[at.current_leg_index]
            pts = rw.points
            if len(pts) < 2:
                continue
            
            _, _, total_len = get_point_func(pts, 0)
            
            if at.leg_distance >= total_len:
                at.leg_distance = total_len
                
                # vlak dojel na konec úseku (do stanice)
                if at.forward:
                    target_station_idx = at.current_leg_index + 1
                else:
                    target_station_idx = at.current_leg_index
                    
                target_station = at.route.stations[target_station_idx]
                stop_here = at.route.stop_flags[target_station_idx]
                
                if stop_here:
                    at.wait_timer = 300.0
                    at.passengers = 0
                    at.current_stop_station = target_station
                        
                # přepnutí na další úsek
                if at.forward:
                    at.current_leg_index += 1
                    if at.current_leg_index >= len(at.route.railways):
                        at.forward = False
                        at.current_leg_index = len(at.route.railways) - 1
                else:
                    at.current_leg_index -= 1
                    if at.current_leg_index < 0:
                        at.forward = True
                        at.current_leg_index = 0
                        
                at._setup_leg()

    def __str__(self):
        return "Města:\n" + "\n".join(["\t{} (populace: {}, pozice: {}\n\t\t{})".format(
            city.name, 
            city.population, 
            city.position, 
            '\n\t\t'.join([f'{s.name} {s.position}' for s in city.stations])
        ) for city in self.cities])
    
    def add_railway(self, railway: Railway):
        """
        Přidá železniční trať do světa.

        Args:
            railway (Railway): trať, která se má přidat
        """
        self.railways.append(railway)
    
    def add_active_train(self, train: ActiveTrain):
        """
        Přidá aktivní vlak do světa.

        Args:
            train (ActiveTrain): vlak, který se má přidat
        """
        self.active_trains.append(train)
    
    def remove_railway(self, railway: Railway):
        """
        Odstraní železniční trať ze světa.

        Args:
            railway (Railway): trať, která se má odstranit
        """
        self.railways.remove(railway)

    def get_closest_station(self, point: tuple[float, float]):
        """
        Najde stanici, která je nejblíže k zadanému bodu.

        Args:
            tuple[float, float]: zadaný bod (x, y)

        Returns:
            tuple[Station, float]: nejbližší stanice a její vzdálenost (v metrech)
        """
        closest_station = None
        min_distance = float("inf") # https://stackoverflow.com/questions/34264710/what-is-the-point-of-floatinf-in-python

        for city in self.cities:
            for station in city.stations:
                distance = math.dist(station.position, point)
                if distance < min_distance:
                    min_distance = distance
                    closest_station = station
                    
        return closest_station, min_distance


def WorldGenerator(
        world_boundary: int,

        city_names: list[str],
        cities: int,
        small_city_max_population: int,
        large_city_max_population: int,
        min_city_radius: int,
        max_city_boundary: int,

        max_stations_per_city: int,
        passenger_station_names: list[str],
        cargo_station_names: list[str],

        large_city_cargo_capacity_range: tuple[float, float],
        large_city_passenger_capacity_range: tuple[int, int],
        large_city_max_tracks: int,
        small_city_passenger_capacity_range: tuple[int, int],
        small_city_cargo_capacity_range: tuple[float, float]
    ):

    """
    Generuje svět.

    Args:
        world_boundary (int): velikost hranice světa v metrech (pro generování měst atd.)
        city_names (list[str]): seznam názvů pro města
        cities (int): počet měst, které se mají vygenerovat
        small_city_max_population (int): maximální počet obyvatel v malém městě
        large_city_max_population (int): maximální počet obyvatel v velkém městě
        min_city_radius (int): minimální poloměr města v metrech
        max_city_boundary (int): maximální velikost města v metrech (pro generování stanic atd.)
        max_stations_per_city (int): maximální počet stanic, které mohou být v jednom městě
        passenger_station_names (list[str]): seznam názvů pro osobní stanice
        cargo_station_names (list[str]): seznam názvů pro nákladní stanice
        large_city_cargo_capacity_range (tuple[float, float]): rozsah kapacity pro nákladní stanice ve velkých městech
        large_city_passenger_capacity_range (tuple[int, int]): rozsah kapacity pro osobní stanice ve velkých městech
        large_city_max_tracks (int): maximální počet kolejí ve stanicích ve velkých městech (minimum je 1)
        small_city_passenger_capacity_range (tuple[int, int]): rozsah kapacity pro osobní stanice v malých městech
        small_city_cargo_capacity_range (tuple[float, float]): rozsah kapacity pro nákladní stanice v malých městech
    """

    if (len(city_names) < cities) or (len(passenger_station_names) < max_stations_per_city) or (len(cargo_station_names) < max_stations_per_city):
        raise ValueError("Není dostatek názvů pro generování světa.")
    
    if small_city_max_population < 1:
        raise ValueError("Maximální počet obyvatel v malém městě musí být alespoň 1.")
    
    if small_city_max_population >= large_city_max_population:
        raise ValueError("Maximální počet obyvatel v malém městě musí být menší než ve velkém městě.")
    
    if max_stations_per_city < 1:
        raise ValueError("Maximální počet stanic v městě musí být alespoň 1.")

    def generate_station_position(city_pass: City): # generuje pozici stanice náhodně uvnitř města
        angle = random.uniform(0, 2 * math.pi)
        r = random.uniform(city_pass.radius * 0.2, city_pass.radius)
        return (city_pass.position[0] + r * math.cos(angle), city_pass.position[1] + r * math.sin(angle))

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

        city_radius = math.sqrt(population / large_city_max_population) * max_city_boundary # plocha roste lineárně s populací
        city_radius = max(city_radius, min_city_radius) # minimální poloměr

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
                
                station_position = generate_station_position(city)

                if is_cargo:
                    station_name = f"{city_name}-{city_cargo_names[i].capitalize()}"
                    Station(city=city, name=station_name, position=station_position, passenger_capacity=0, cargo_capacity=random.uniform(*large_city_cargo_capacity_range), tracks=random.randint(1, large_city_max_tracks))
                else:
                    station_name = f"{city_name}-{city_pass_names[i].capitalize()}"
                    Station(city=city, name=station_name, position=station_position, passenger_capacity=random.randint(*large_city_passenger_capacity_range), cargo_capacity=0, tracks=random.randint(1, large_city_max_tracks))

        else: # malé město
            Station(city=city, name=city_name, position=generate_station_position(city), passenger_capacity=random.randint(*small_city_passenger_capacity_range), cargo_capacity=random.uniform(*small_city_cargo_capacity_range), tracks=1)
            
        generated_cities.append(city)

    return World(cities=generated_cities)