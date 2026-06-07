import json
import os
import TerminusEngine.World
import TerminusEngine.Vehicles
import TerminusEngine.Economy

def get_loco_type_by_id(type_id, available_loco_types):
    """
    Vyhledá typ lokomotivy podle jeho ID v seznamu dostupných typů.
    Pokud nenalezne, vrátí první dostupný typ, jinak None.
    
    Args:
        type_id (str): hledané ID
        available_loco_types (list): seznam dostupných typů
    """
    for t in available_loco_types:
        if t.id == type_id:
            return t
    if available_loco_types:
        return available_loco_types[0]
    return None

def get_wagon_type_by_id(type_id, available_wagon_types):
    """
    Vyhledá typ vagonu podle jeho ID v seznamu dostupných typů.
    Pokud nenalezne, vrátí první dostupný typ, jinak None.
    
    Args:
        type_id (str): hledané ID
        available_wagon_types (list): seznam dostupných typů
    """
    for t in available_wagon_types:
        if t.id == type_id:
            return t
    if available_wagon_types:
        return available_wagon_types[0]
    return None

def save_game(filename, economy, game, world, owned_locos, owned_wagons, assembled_trains):
    """
    Uloží aktuální stav hry (ekonomika, čas, inventář a kompletní mapu) jako JSON do souboru.
    
    Args:
        filename (str): cesta k souboru k uložení
        economy (Economy): instance ekonomiky
        game (Game): instance hry
        world (World): instance světa
        owned_locos (list): seznam vlastněných lokomotiv
        owned_wagons (list): seznam vlastněných vagonů
        assembled_trains (list): seznam sestavených souprav
    """
    data = {
        "economy": {
            "balance": economy.balance
        },
        "game": {
            "time": game.time
        },
        "world": {
            "cities": [],
            "railways": [],
            "active_trains": []
        },
        "inventory": {
            "owned_locos": [{"type": loco.type.id, "health": loco.health, "id": loco.id} for loco in owned_locos],
            "owned_wagons": [{"type": w.type.id, "health": w.health, "id": w.id} for w in owned_wagons],
            "assembled_trains": []
        }
    }


    for city in world.cities:
        city_data = {
            "id": city.id,
            "name": city.name,
            "position": city.position,
            "radius": city.radius,
            "population": city.population,
            "stations": []
        }
        for st in city.stations:
            st_data = {
                "id": st.id,
                "name": st.name,
                "position": st.position,
                "passenger_capacity": st.passenger_capacity,
                "cargo_capacity": st.cargo_capacity,
                "tracks": st.tracks,
                "passengers": st.passengers,
                "cargo": st.cargo
            }
            city_data["stations"].append(st_data)
        data["world"]["cities"].append(city_data)


    for rw in world.railways:
        data["world"]["railways"].append({
            "id": rw.id,
            "station_a": rw.station_a.id if rw.station_a else None,
            "station_b": rw.station_b.id if rw.station_b else None,
            "points": rw.points
        })
        

    for at in world.active_trains:
        at_data = {
            "id": at.id,
            "train": {
                "id": at.train.id,
                "name": at.train.name,
                "health": at.train.health,
                "loco": {"type": at.train.locomotive.type.id, "health": at.train.locomotive.health, "id": at.train.locomotive.id},
                "wagons": [{"type": w.type.id, "health": w.health, "id": w.id} for w in at.train.wagons]
            },
            "route": {
                "id": at.route.id,
                "name": at.route.name,
                "stations": [st.id for st in at.route.stations],
                "stop_flags": at.route.stop_flags,
                "railways": [rw.id for rw in at.route.railways],
                "color": at.route.color if hasattr(at.route, 'color') else (255, 255, 255)
            },
            "state": {
                "current_leg_index": at.current_leg_index,
                "forward": at.forward,
                "leg_distance": at.leg_distance,
                "passengers": at.passengers,
                "cargo": at.cargo,
                "railway_dir": at.railway_dir,
                "wait_timer": at.wait_timer,
                "current_stop_station": at.current_stop_station.id if at.current_stop_station else None
            }
        }
        data["world"]["active_trains"].append(at_data)
        

    for tr in assembled_trains:
        data["inventory"]["assembled_trains"].append({
            "loco": {"type": tr["loco"].type.id, "health": tr["loco"].health, "id": tr["loco"].id},
            "wagons": [{"type": w.type.id, "health": w.health, "id": w.id} for w in tr["wagons"]]
        })
        
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return True


def load_game(filename, economy, game, world, owned_locos, owned_wagons, assembled_trains, available_loco_types, available_wagon_types):
    """
    Načte stav hry ze souboru s JSONem a zrekonstruuje všechny herní objekty.
    
    Args:
        filename (str): cesta k načítanému souboru
        economy (Economy): instance ekonomiky (výstupní)
        game (Game): instance hry (výstupní)
        world (World): instance světa (výstupní)
        owned_locos (list): seznam vlastněných lokomotiv (výstupní)
        owned_wagons (list): seznam vlastněných vagonů (výstupní)
        assembled_trains (list): seznam sestavených souprav (výstupní)
        available_loco_types (list): seznam dostupných typů lokomotiv (pro spárování načtených dat)
        available_wagon_types (list): seznam dostupných typů vagonů (pro spárování načtených dat)
        
    Returns:
        bool: True pokud se hra úspěšně načetla, False pokud soubor neexistuje.
    """
    if not os.path.exists(filename):
        return False

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    economy.balance = data["economy"]["balance"]
    game.time = data["game"]["time"]
    
    owned_locos.clear()
    owned_wagons.clear()
    assembled_trains.clear()
    
    # helper funkce
    def load_loco(l_data):
        """Pomocná funkce pro načtení jedné lokomotivy ze slovníku dat."""
        t = get_loco_type_by_id(l_data["type"], available_loco_types)
        if not t:
            return None
        l = TerminusEngine.Vehicles.Locomotive(t)
        l.health = l_data["health"]
        l.id = l_data["id"]
        return l
        
    def load_wagon(w_data):
        """Pomocná funkce pro načtení jednoho vagonu ze slovníku dat."""
        t = get_wagon_type_by_id(w_data["type"], available_wagon_types)
        if not t:
            return None
        if isinstance(t, TerminusEngine.Vehicles.PassengerWagonType):
            w = TerminusEngine.Vehicles.PassengerWagon(t)
        else:
            w = TerminusEngine.Vehicles.CargoWagon(t)
        w.health = w_data["health"]
        w.id = w_data["id"]
        return w

    for l_data in data["inventory"]["owned_locos"]:
        loco = load_loco(l_data)
        if loco:
            owned_locos.append(loco)
        
    for w_data in data["inventory"]["owned_wagons"]:
        wagon = load_wagon(w_data)
        if wagon:
            owned_wagons.append(wagon)
            
    for tr_data in data["inventory"]["assembled_trains"]:
        loco = load_loco(tr_data["loco"])
        wagons = []
        for w_data in tr_data["wagons"]:
            wagon = load_wagon(w_data)
            if wagon:
                wagons.append(wagon)
                
        if loco:
            assembled_trains.append({
                "loco": loco,
                "wagons": wagons
            })
        
    world.cities.clear()
    world.railways.clear()
    world.active_trains.clear()
    game.path_cache.clear() # vyčištění cache tratí na překreslení
    
    stations_by_id = {}
    railways_by_id = {}
    
    for city_data in data["world"]["cities"]:
        city = TerminusEngine.World.City(city_data["name"], tuple(city_data["position"]), city_data["radius"], city_data["population"])
        city.id = city_data["id"]
        for st_data in city_data["stations"]:
            st = TerminusEngine.World.Station(city, st_data["name"], tuple(st_data["position"]), st_data["passenger_capacity"], st_data["cargo_capacity"], st_data["tracks"])
            st.passengers = st_data["passengers"]
            st.cargo = st_data["cargo"]
            st.id = st_data["id"]
            stations_by_id[st.id] = st
        world.cities.append(city)
        
    for rw_data in data["world"]["railways"]:
        st_a = stations_by_id[rw_data["station_a"]] if rw_data["station_a"] else None
        st_b = stations_by_id[rw_data["station_b"]] if rw_data["station_b"] else None
            
        pts = [tuple(p) for p in rw_data["points"]]
        rw = TerminusEngine.World.Railway(st_a, st_b, pts)
        rw.id = rw_data["id"]
        railways_by_id[rw.id] = rw
        world.add_railway(rw)
        
    for at_data in data["world"]["active_trains"]:
        loco = load_loco(at_data["train"]["loco"])
        if not loco:
            continue
        wagons = []
        for w_data in at_data["train"]["wagons"]:
            wagon = load_wagon(w_data)
            if wagon:
                wagons.append(wagon)
        train = TerminusEngine.Vehicles.Train(at_data["train"]["name"], loco, wagons)
        train.health = at_data["train"]["health"]
        train.id = at_data["train"]["id"]
        
        # stanice ve spoji
        route_stations = [stations_by_id[sid] for sid in at_data["route"]["stations"]]
                
        # tratě ve spoji
        route_railways = [railways_by_id[rid] for rid in at_data["route"]["railways"]]
            
        route = TerminusEngine.World.Route(at_data["route"]["name"], route_stations, at_data["route"]["stop_flags"], route_railways)
        if "color" in at_data["route"]:
            route.color = tuple(at_data["route"]["color"])
        route.id = at_data["route"]["id"]
            
        at = TerminusEngine.World.ActiveTrain(train, route)
        at.id = at_data["id"]
        
        state = at_data["state"]
        at.current_leg_index = state["current_leg_index"]
        at.forward = state["forward"]
        at.leg_distance = state["leg_distance"]
        at.passengers = state["passengers"]
        at.cargo = state["cargo"]
        at.railway_dir = state["railway_dir"]
        at.wait_timer = state["wait_timer"]
        
        stop_st = state["current_stop_station"]
        at.current_stop_station = stations_by_id[stop_st] if stop_st else None
        
        world.add_active_train(at)

    return True