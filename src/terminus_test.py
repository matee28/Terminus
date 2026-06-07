import pygame

import TerminusEngine
import TerminusEngine.World
import TerminusEngine.Economy
import TerminusEngine.Vehicles
import TerminusEngine.SaveLoad


import os
import math
import random
import heapq


GAME_SAVE_FILE = "game.json"

RAILWAY_MODE = False
RAILWAY_MODE_SNAP_DIST_PX = 20
ROUTE_MODE = False
SHOW_ROUTES = False
notification_text = ""
notification_timer = 0.0
current_route_stations = []
current_route_stop_flags = []
current_route_railways = []

INITIAL_BALANCE = 10000000000

RAILWAY_COST_PER_METER = 10
TRAIN_SELL_MULTIPLIER = 0.6

# výdělek
PASSENGER_REWARD = 25
CARGO_REWARD = 50

def main():

    world_boundary = 20000

    world = TerminusEngine.World.WorldGenerator(
        world_boundary=world_boundary,
        city_names=TerminusEngine.read_src("assets/names/CITIES").splitlines(),
        cities=10,
        small_city_max_population=500,
        large_city_max_population=5000,
        min_city_radius=500,
        max_city_boundary=1000,
        max_stations_per_city=3,
        passenger_station_names=TerminusEngine.read_src("assets/names/STATIONS_PASSENGER").splitlines(),
        cargo_station_names=TerminusEngine.read_src("assets/names/STATIONS_CARGO").splitlines(),
        large_city_cargo_capacity_range=(500.0, 5000.0),
        large_city_passenger_capacity_range=(200, 2000),
        large_city_max_tracks=4,
        small_city_passenger_capacity_range=(50, 300),
        small_city_cargo_capacity_range=(50.0, 300.0)
    )

    # print(world)



    camera = TerminusEngine.Camera(
        position=(0, 0),
        max_distance=world_boundary,
        move_speed=1.0,
        zoom=1.0,
        max_zoom=2.5,
        min_zoom=0.001,
        zoom_speed=1.5
    )

    game = TerminusEngine.Game(
        camera=camera,
        width=800,
        height=600,
        font_name="Arial"
    )

    economy = TerminusEngine.Economy.Economy(initial_balance=INITIAL_BALANCE, currency_symbol=" Kč")


    game.load_image("terrain", "assets/terrain/seamless_2048.png")
    game.load_image("rail_tile", "assets/rails/rail_tile_1.png", rotation=90)

    # textury lokomotiv
    game.load_image("loco_ce", "assets/vehicles/locomotives/cityelefant.png", rotation=-90)
    game.load_image("loco_742", "assets/vehicles/locomotives/742.png", rotation=-90)
    game.load_image("loco_vectron", "assets/vehicles/locomotives/vectron.png", rotation=-90)

    # textury osobních vagonů
    game.load_image("wagon_p_ce", "assets/vehicles/passenger_wagons/cityelefant.png", rotation=-90)
    game.load_image("wagon_p_b", "assets/vehicles/passenger_wagons/b.png", rotation=-90)

    # textury nákladních vagonů
    game.load_image("wagon_c_single", "assets/vehicles/cargo_wagons/single_container.png", rotation=-90)
    game.load_image("wagon_c_double", "assets/vehicles/cargo_wagons/double_container.png", rotation=-90)

    # zvuky
    game.audio.load_sound("amb_p_station", "assets/sounds/amb_p_station_loop_stereo.ogg")
    game.audio.load_sound("amb_c_station", "assets/sounds/amb_c_station_loop_stereo.ogg")
    game.audio.load_sound("amb_train", "assets/sounds/amb_train_loop_stereo.ogg")
    game.audio.load_sound("diesel_loop", "assets/sounds/diesel_loop_stereo.ogg")
    game.audio.load_sound("electric_loop", "assets/sounds/electric_loop_stereo.ogg")
    game.audio.load_sound("gong", "assets/sounds/gong.ogg")
    game.audio.load_sound("horn", "assets/sounds/horn.ogg")

    # přiřazení zvuků stanic
    for c in world.cities:
        for st in c.stations:
            if st.passenger_capacity > 0:
                game.audio.play_sound("amb_p_station", lambda s=st: s.position, loop=True, base_volume=0.3, panning=False)
            if st.cargo_capacity > 0:
                game.audio.play_sound("amb_c_station", lambda s=st: s.position, loop=True, base_volume=0.3, panning=False)

    # definice lokomotiv
    type_loco_ce = TerminusEngine.Vehicles.LocomotiveType("loco_ce", "CityElefant (lokomotiva)", max_speed=140.0, power=2000.0, weight=62.7, price=500000.0, texture_name="loco_ce", passenger_capacity=59, engine_sound_name="electric_loop")
    type_loco_742 = TerminusEngine.Vehicles.LocomotiveType("loco_742", "Lokomotiva řady 742", max_speed=90.0, power=883.0, weight=64.0, price=300000.0, texture_name="loco_742", engine_sound_name="diesel_loop")
    type_loco_vectron = TerminusEngine.Vehicles.LocomotiveType("loco_vectron", "Siemens Vectron", max_speed=180.0, power=6400.0, weight=90.0, price=1000000.0, texture_name="loco_vectron", engine_sound_name="electric_loop") # nákladní verze má max 160 km/h, osobní 200 km/h -> kompromis

    # definice osobních vagonů
    type_wagon_p_ce = TerminusEngine.Vehicles.PassengerWagonType("wagon_p_ce", "CityElefant (vložený vůz)", passenger_capacity=134, weight=45.4, price=150000.0, texture_name="wagon_p_ce")
    type_wagon_p_b = TerminusEngine.Vehicles.PassengerWagonType("wagon_p_b", "Vůz třídy B", passenger_capacity=80, weight=40.0, price=100000.0, texture_name="wagon_p_b")

    # definice nákladních vagonů
    type_wagon_c_single = TerminusEngine.Vehicles.CargoWagonType("wagon_c_single", "Kontejnerový vagon (Single)", cargo_capacity=30.0, weight=20.0, price=80000.0, texture_name="wagon_c_single")
    type_wagon_c_double = TerminusEngine.Vehicles.CargoWagonType("wagon_c_double", "Kontejnerový vagon (Double)", cargo_capacity=60.0, weight=30.0, price=140000.0, texture_name="wagon_c_double")

    # seznamy pro UI
    available_loco_types = [type_loco_ce, type_loco_742, type_loco_vectron]
    available_wagon_types = [type_wagon_p_ce, type_wagon_p_b, type_wagon_c_single, type_wagon_c_double]
    
    # inventář
    owned_locos = []
    owned_wagons = []
    assembled_trains = [] # {"name": str, "loco": loco, "wagons": list}
    
    menu_state = {"mode": "closed", "temp_loco": None, "temp_wagons": [], "temp_route": None}
    mouse_down_pos = (0, 0)


    game.camera.position = (0, 0)
    game.camera.zoom = game.camera.min_zoom


    def event_handler(event: pygame.event.Event):
        global RAILWAY_MODE, ROUTE_MODE, SHOW_ROUTES, notification_text, notification_timer
        nonlocal mouse_down_pos

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_down_pos = event.pos

        # zoom: zatím doprostřed obrazovky -> k myši?
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                camera.zoom_in()
            else:
                camera.zoom_out()

        # pohyb kamery
        if event.type == pygame.MOUSEMOTION:
            if event.buttons[0]:
                camera.move((-event.rel[0], +event.rel[1]))

        def find_railway_path(start_station, end_station):
            counter = 0
            queue = [(0.0, counter, start_station, [], [])]
            visited = set()
            
            while queue:
                dist, _, curr, p_st, p_rw = heapq.heappop(queue)
                
                if curr == end_station:
                    return p_st, p_rw
                    
                if curr in visited:
                    continue
                visited.add(curr)
                
                for rw in world.railways:
                    nxt = None
                    if rw.station_a == curr and rw.station_b is not None:
                        nxt = rw.station_b
                    elif rw.station_b == curr and rw.station_a is not None:
                        nxt = rw.station_a
                        
                    if nxt and nxt not in visited:
                        rw_dist = 0.0
                        if len(rw.points) > 1:
                            rw_dist = sum(math.dist(rw.points[i-1], rw.points[i]) for i in range(1, len(rw.points)))
                        else:
                            rw_dist = math.dist(curr.position, nxt.position)
                        
                        counter += 1
                        heapq.heappush(queue, (dist + rw_dist, counter, nxt, p_st + [nxt], p_rw + [rw]))
                        
            return None, None

        # stisk klávesy
        if event.type == pygame.KEYDOWN:
            if menu_state["mode"] != "closed":
                if event.key == pygame.K_ESCAPE:
                    if menu_state["mode"] in ["buy_loco", "buy_wagon", "assemble_loco", "inventory_main"]:
                        menu_state["mode"] = "main"
                    elif menu_state["mode"] == "assemble_wagons":
                        menu_state["mode"] = "assemble_loco"
                        if menu_state["temp_loco"] is not None:
                            owned_locos.append(menu_state["temp_loco"])
                        owned_wagons.extend(menu_state["temp_wagons"])
                        menu_state["temp_loco"] = None
                        menu_state["temp_wagons"] = []
                    elif menu_state["mode"] in ["inventory_locos", "inventory_wagons", "inventory_trains", "inventory_active"]:
                        menu_state["mode"] = "inventory_main"
                    else:
                        menu_state["mode"] = "closed"
                        menu_state["temp_route"] = None
                
                if pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_1
                    if menu_state["mode"] == "main":
                        if idx == 0: menu_state["mode"] = "buy_loco"
                        elif idx == 1: menu_state["mode"] = "buy_wagon"
                        elif idx == 2: 
                            menu_state["mode"] = "assemble_loco"
                            menu_state["temp_loco"] = None
                            menu_state["temp_wagons"] = []
                        elif idx == 3: menu_state["mode"] = "inventory_main"
                    elif menu_state["mode"] == "inventory_main":
                        if idx == 0: menu_state["mode"] = "inventory_locos"
                        elif idx == 1: menu_state["mode"] = "inventory_wagons"
                        elif idx == 2: menu_state["mode"] = "inventory_trains"
                        elif idx == 3: menu_state["mode"] = "inventory_active"
                    elif menu_state["mode"] == "inventory_locos":
                        types_in_inv = []
                        for l in owned_locos:
                            if l.type not in types_in_inv: types_in_inv.append(l.type)
                        if idx < len(types_in_inv) * 2:
                            item_idx = idx // 2
                            action = "sell" if idx % 2 == 0 else "repair"
                            t_to_act = types_in_inv[item_idx]
                            most_damaged_idx = -1
                            min_health = 2.0
                            for i, l in enumerate(owned_locos):
                                if l.type == t_to_act and l.health < min_health:
                                    min_health = l.health
                                    most_damaged_idx = i
                            if most_damaged_idx != -1:
                                l = owned_locos[most_damaged_idx]
                                if action == "sell":
                                    sold_l = owned_locos.pop(most_damaged_idx)
                                    economy.add(sold_l.get_sell_price() * TRAIN_SELL_MULTIPLIER)
                                else:
                                    repair_cost = l.get_repair_cost()
                                    if economy.can_afford(repair_cost):
                                        economy.deduct(repair_cost)
                                        l.repair()
                    elif menu_state["mode"] == "inventory_wagons":
                        types_in_inv = []
                        for w in owned_wagons:
                            if w.type not in types_in_inv: types_in_inv.append(w.type)
                        if idx < len(types_in_inv) * 2:
                            item_idx = idx // 2
                            action = "sell" if idx % 2 == 0 else "repair"
                            t_to_act = types_in_inv[item_idx]
                            most_damaged_idx = -1
                            min_health = 2.0
                            for i, w in enumerate(owned_wagons):
                                if w.type == t_to_act and w.health < min_health:
                                    min_health = w.health
                                    most_damaged_idx = i
                            if most_damaged_idx != -1:
                                w = owned_wagons[most_damaged_idx]
                                if action == "sell":
                                    sold_w = owned_wagons.pop(most_damaged_idx)
                                    economy.add(sold_w.get_sell_price() * TRAIN_SELL_MULTIPLIER)
                                else:
                                    repair_cost = w.get_repair_cost()
                                    if economy.can_afford(repair_cost):
                                        economy.deduct(repair_cost)
                                        w.repair()
                    elif menu_state["mode"] == "inventory_trains":
                        train_idx = idx // 3
                        action = "sell" if idx % 3 == 0 else ("disassemble" if idx % 3 == 1 else "repair")
                        if train_idx < len(assembled_trains):
                            tr = assembled_trains[train_idx]
                            if action == "sell":
                                assembled_trains.pop(train_idx)
                                sell_price = (tr["loco"].get_sell_price() + sum(w.get_sell_price() for w in tr["wagons"])) * TRAIN_SELL_MULTIPLIER
                                economy.add(sell_price)
                            elif action == "disassemble":
                                assembled_trains.pop(train_idx)
                                owned_locos.append(tr["loco"])
                                owned_wagons.extend(tr["wagons"])
                            elif action == "repair":
                                repair_cost = tr["loco"].get_repair_cost() + sum(w.get_repair_cost() for w in tr["wagons"])
                                if economy.can_afford(repair_cost):
                                    economy.deduct(repair_cost)
                                    tr["loco"].repair()
                                    for w in tr["wagons"]:
                                        w.repair()
                    elif menu_state["mode"] == "inventory_active":
                        train_idx = idx // 2
                        action = "withdraw" if idx % 2 == 0 else "repair"
                        if train_idx < len(world.active_trains):
                            at = world.active_trains[train_idx]
                            if action == "withdraw":
                                world.active_trains.pop(train_idx)
                                for src in at.audio_sources:
                                    game.audio.stop_source(src)
                                assembled_trains.append({
                                    "loco": at.train.locomotive,
                                    "wagons": at.train.wagons
                                })
                            elif action == "repair":
                                repair_cost = at.train.locomotive.get_repair_cost() + sum(w.get_repair_cost() for w in at.train.wagons)
                                if economy.can_afford(repair_cost):
                                    economy.deduct(repair_cost)
                                    at.train.locomotive.repair()
                                    for w in at.train.wagons:
                                        w.repair()
                    elif menu_state["mode"] == "buy_loco":
                        if idx < len(available_loco_types):
                            t = available_loco_types[idx]
                            if economy.can_afford(t.price):
                                economy.deduct(t.price)
                                owned_locos.append(TerminusEngine.Vehicles.Locomotive(t))
                    elif menu_state["mode"] == "buy_wagon":
                        if idx < len(available_wagon_types):
                            t = available_wagon_types[idx]
                            if economy.can_afford(t.price):
                                economy.deduct(t.price)
                                if isinstance(t, TerminusEngine.Vehicles.PassengerWagonType):
                                    owned_wagons.append(TerminusEngine.Vehicles.PassengerWagon(t))
                                else:
                                    owned_wagons.append(TerminusEngine.Vehicles.CargoWagon(t))
                    elif menu_state["mode"] == "assemble_loco":
                        if idx < len(owned_locos):
                            menu_state["temp_loco"] = owned_locos.pop(idx)
                            menu_state["mode"] = "assemble_wagons"
                    elif menu_state["mode"] == "assemble_wagons":
                        if idx < len(owned_wagons):
                            menu_state["temp_wagons"].append(owned_wagons.pop(idx))
                    elif menu_state["mode"] == "assign_train":
                        if idx < len(assembled_trains):
                            train_info = assembled_trains.pop(idx)
                            new_train = TerminusEngine.Vehicles.Train("Vlak", train_info["loco"], train_info["wagons"])
                            world.add_active_train(TerminusEngine.World.ActiveTrain(new_train, menu_state["temp_route"]))
                            menu_state["mode"] = "closed"
                            menu_state["temp_route"] = None
                
                if event.key == pygame.K_RETURN and menu_state["mode"] == "assemble_wagons":
                    if menu_state["temp_loco"] is not None:
                        assembled_trains.append({
                            "loco": menu_state["temp_loco"],
                            "wagons": menu_state["temp_wagons"].copy()
                        })
                    menu_state["mode"] = "main"

                return # nepokračovat ve zpracování hry, pokud v menu

            if event.key == pygame.K_m:
                menu_state["mode"] = "main"

            if event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                if TerminusEngine.SaveLoad.save_game(GAME_SAVE_FILE, economy, game, world, owned_locos, owned_wagons, assembled_trains):
                    notification_text = "hra byla úspěšně uložena"
                    notification_timer = 3.0

            if event.key == pygame.K_o and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                if TerminusEngine.SaveLoad.load_game(GAME_SAVE_FILE, economy, game, world, owned_locos, owned_wagons, assembled_trains, available_loco_types, available_wagon_types):
                    notification_text = "hra byla úspěšně načtena"
                    notification_timer = 3.0
                else:
                    notification_text = "soubor s uloženou hrou nenalezen"
                    notification_timer = 3.0

            # RAILWAY_MODE toggle = T
            if event.key == pygame.K_t:
                RAILWAY_MODE = not RAILWAY_MODE
                if RAILWAY_MODE:
                    ROUTE_MODE = False
                    current_route_stations.clear()
                    current_route_stop_flags.clear()
                    current_route_railways.clear()
                    world.add_railway(TerminusEngine.World.Railway(None, None, []))
                else:
                    if len(world.railways) > 0 and world.railways[-1].station_b is None:
                        world.railways.remove(world.railways[-1])

            # SHOW_ROUTES toggle = S
            if event.key == pygame.K_s and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                SHOW_ROUTES = not SHOW_ROUTES

            # ROUTE_MODE toggle = R
            if event.key == pygame.K_r:
                ROUTE_MODE = not ROUTE_MODE
                current_route_stations.clear()
                current_route_stop_flags.clear()
                current_route_railways.clear()
                if ROUTE_MODE:
                    RAILWAY_MODE = False
                    if len(world.railways) > 0 and world.railways[-1].station_b is None:
                        world.railways.remove(world.railways[-1])

            # smazání posledního bodu tratě = Z
            if event.key == pygame.K_z:
                if RAILWAY_MODE and len(world.railways) > 0:
                    if len(world.railways[-1].points) > 2:
                        del world.railways[-1].points[-2] # -2, protože poslední je poloha kurzoru
                    else:
                        world.railways.remove(world.railways[-1])
                        RAILWAY_MODE = False
                elif ROUTE_MODE and len(current_route_stations) > 0:
                    current_route_stations.pop()
                    current_route_stop_flags.pop()
                    if len(current_route_railways) > 0:
                        current_route_railways.pop()

            # pozastavení času = P
            if event.key == pygame.K_p:
                game.time_paused = not game.time_paused

        # ROUTE_MODE click handling
        if ROUTE_MODE:
            if event.type == pygame.MOUSEBUTTONUP and math.dist(mouse_down_pos, event.pos) < 5:
                if event.button == 1: # levé tlačítko = přidání stanice
                    point_position = game.world_position(event.pos)
                    closest_station, distance = world.get_closest_station(point_position)
                    if closest_station and game.screen_distance(distance) < RAILWAY_MODE_SNAP_DIST_PX:
                        if len(current_route_stations) == 0:
                            has_connection = any(rw.station_a == closest_station or rw.station_b == closest_station for rw in world.railways)
                            if has_connection:
                                current_route_stations.append(closest_station)
                                current_route_stop_flags.append(True)
                        else:
                            last_station = current_route_stations[-1]
                            if closest_station != last_station:
                                path_st, path_rw = find_railway_path(last_station, closest_station)
                                if path_st is not None:
                                    for i in range(len(path_st)):
                                        st = path_st[i]
                                        rw = path_rw[i]
                                        current_route_stations.append(st)
                                        current_route_railways.append(rw)
                                        current_route_stop_flags.append(i == len(path_st) - 1)
                elif event.button == 3: # pravé tlačítko = vytvoření spoje a nasazení vlaku
                    if len(current_route_stations) >= 2:
                        route = TerminusEngine.World.Route("Nový Spoj", current_route_stations.copy(), current_route_stop_flags.copy(), current_route_railways.copy())
                        menu_state["mode"] = "assign_train"
                        menu_state["temp_route"] = route
                        ROUTE_MODE = False
                        current_route_stations.clear()
                        current_route_stop_flags.clear()
                        current_route_railways.clear()



        # přidávání kolejí
        if RAILWAY_MODE:
            if event.type == pygame.MOUSEBUTTONUP and math.dist(mouse_down_pos, event.pos) < 5:
                if event.button == 1: # levé tlačítko
                    point_position = game.world_position(event.pos)
                    closest_station, distance = world.get_closest_station(point_position)
                    if len(world.railways[-1].points) == 0:
                        if closest_station and game.screen_distance(distance) < RAILWAY_MODE_SNAP_DIST_PX:
                            world.railways[-1].station_a = closest_station
                            world.railways[-1].add_point(closest_station.position)
                            world.railways[-1].add_point(closest_station.position) # dvakrát, aby se trať aktualizovala při pohybu myši
                    else:
                        if closest_station and game.screen_distance(distance) < RAILWAY_MODE_SNAP_DIST_PX and closest_station != world.railways[-1].station_a:
                            route_exists = False
                            for rw in world.railways[:-1]:
                                if (rw.station_a == world.railways[-1].station_a and rw.station_b == closest_station) or (rw.station_b == world.railways[-1].station_a and rw.station_a == closest_station):
                                    route_exists = True
                                    break

                            if route_exists:
                                notification_text = "trať mezi těmito stanicemi už existuje"
                                notification_timer = 3.0
                            else:
                                temp_points = world.railways[-1].points[:-1] + [closest_station.position]
                                total_cost = sum(math.dist(temp_points[i-1], temp_points[i]) for i in range(1, len(temp_points))) * RAILWAY_COST_PER_METER
                                if economy.can_afford(total_cost):
                                    economy.deduct(total_cost)
                                    world.railways[-1].remove_last_point() # odstranění posledního bodu (z pohybu myši)
                                    world.railways[-1].station_b = closest_station 
                                    world.railways[-1].add_point(closest_station.position)
                                    
                                    RAILWAY_MODE = False
                        else:
                            world.railways[-1].points.append(point_position)
            if len(world.railways) > 0:
                if len(world.railways[-1].points) > 0 and event.type == pygame.MOUSEMOTION:
                    world.railways[-1].points[-1] = game.world_position(event.pos)


    def loop():
        global notification_text, notification_timer
        
        game.render_image(
            texture_name="terrain",
            world_position=(0, 0),
            size=(0, 0),
            tiled=True
        )

        # game.draw_debug_dot(game.world_position(pygame.mouse.get_pos()))
        # game.draw_debug_dot(game.world_position((pygame.display.get_surface().get_width()/2, pygame.display.get_surface().get_height()/2)), 5)

        for city in world.cities:
            game.render_city(city.position, radius=city.radius)

            for station in city.stations:
                game.render_station(station.position)
                if camera.zoom > 0.01:
                    scr_pos = game.screen_position(station.position)
                    game.render_text(
                        station.name,
                        (scr_pos[0], scr_pos[1] - 15),
                        color=(255, 255, 255),
                        x_alignment="center",
                        y_alignment="bottom",
                        outline_color=(0, 0, 0),
                        outline_width=1
                    )
                    
                    # zobrazení kapacity stanice
                    cap_offset = 15
                    if station.passenger_capacity > 0:
                        game.render_text(
                            f"{int(station.passengers)}/{station.passenger_capacity}",
                            (scr_pos[0], scr_pos[1] + cap_offset),
                            color=(255, 255, 0),
                            font_size=16,
                            x_alignment="center",
                            y_alignment="top",
                            outline_color=(0, 0, 0),
                            outline_width=1
                        )
                        cap_offset += 20
                        
                    if station.cargo_capacity > 0:
                        game.render_text(
                            f"{int(station.cargo)}/{int(station.cargo_capacity)}",
                            (scr_pos[0], scr_pos[1] + cap_offset),
                            color=(255, 128, 0),
                            font_size=16,
                            x_alignment="center",
                            y_alignment="top",
                            outline_color=(0, 0, 0),
                            outline_width=1
                        )
            if camera.zoom <= 0.01:
                game.render_text(
                    city.name, # + " (" + str(int(city.radius)) + ")",
                    game.screen_position(city.position),
                    color=(255, 255, 255),
                    x_alignment="center",
                    y_alignment="center",
                    outline_color=(0, 0, 0),
                    outline_width=1
                )

        for i, railway in enumerate(world.railways):
            if len(railway.points) > 1:
                is_building = RAILWAY_MODE and (i == len(world.railways) - 1)
                cache =  not is_building
                game.render_image_path(
                    texture_name="rail_tile",
                    distance=TerminusEngine.px2m(game.images["rail_tile"].get_width()), # velikost textury / METERS_TO_PIXELS
                    path=railway.points,
                    cache=cache
                )

        if SHOW_ROUTES:
            for at in world.active_trains:
                if hasattr(at.route, 'color'):
                    for rw in at.route.railways:
                        if len(rw.points) > 1:
                            scr_pts = [game.screen_position(p) for p in rw.points]
                            pygame.draw.lines(game.screen, at.route.color, False, scr_pts, 4)

        # aktualizace a vykreslení vlaků
        dt_seconds = game.clock.get_time() / 1000.0
        if notification_timer > 0:
            notification_timer -= dt_seconds
        
        if not game.time_paused:
            world.update(dt_seconds, game.time_scale, game.train_speed_multiplier, game.passenger_generation_rate, game.cargo_generation_rate, game.get_point_on_path, economy, PASSENGER_REWARD, CARGO_REWARD)

        for at in world.active_trains:
            if len(at.route.railways) == 0: continue
            
            if at.audio_sources is None:
                at.audio_sources = []
                engine_snd = at.train.locomotive.type.engine_sound_name or "diesel_loop"
                at.audio_sources.append(game.audio.play_sound(
                    engine_snd, 
                    lambda at=at: at.position, 
                    loop=True, base_volume=0.8, panning=True,
                    get_volume_multiplier=lambda at=at: 0.0 if at.wait_timer > 0 else 1.0
                ))
                at.audio_sources.append(game.audio.play_sound(
                    "amb_train", 
                    lambda at=at: at.position, 
                    loop=True, base_volume=0.5, panning=True,
                    get_volume_multiplier=lambda at=at: 0.0 if at.wait_timer > 0 else 1.0
                ))

            rw = at.route.railways[at.current_leg_index]
            pts = rw.points
            if len(pts) < 2: continue
            
            all_parts = [at.train.locomotive] + at.train.wagons # zkombinování částí
            current_offset = 0.0
            prev_len = 0.0
            
            _, _, total_len = game.get_point_on_path(pts, 0)
            
            for i, part in enumerate(all_parts):
                part_len = TerminusEngine.px2m(game.images[part.type.texture_name].get_width())
                
                if i > 0:
                    current_offset += (prev_len / 2) + (part_len / 2) + game.train_gap
                prev_len = part_len
                
                part_dist = at.leg_distance - current_offset
                
                if at.railway_dir == 1:
                    raw_dist = part_dist
                else:
                    raw_dist = total_len - part_dist
                    
                pos, heading, _ = game.get_point_on_path(pts, raw_dist)
                
                render_heading = heading + (180 if at.railway_dir == -1 else 0)
                game.render_image(part.type.texture_name, pos, size=(0,0), rotation=render_heading)
                
                # počet cestujících/nákladu a debug dot na pozici vlaku
                if i == 0:
                    at.position = pos
                    if at.just_stopped_for_passengers:
                        at.just_stopped_for_passengers = False
                        game.audio.play_sound("gong", lambda at=at: at.position, loop=False, base_volume=1.0, panning=True)
                    if at.wait_timer <= 0 and random.random() < 0.0001 * game.time_scale * dt_seconds:
                        game.audio.play_sound("horn", lambda at=at: at.position, loop=False, base_volume=1.0, panning=True)

                    game.draw_debug_dot(pos, size=5)
                    if at.get_passenger_capacity() > 0:
                        game.render_text(
                            f"{int(at.passengers)}/{at.get_passenger_capacity()}",
                            game.screen_position((pos[0], pos[1] - 30)),
                            color=(0, 200, 255),
                            font_size=16,
                            x_alignment="center",
                            y_alignment="bottom"
                        )
                    if at.get_cargo_capacity() > 0:
                        game.render_text(
                            f"{int(at.cargo)}/{int(at.get_cargo_capacity())}",
                            game.screen_position((pos[0], pos[1] - 15)),
                            color=(255, 128, 0),
                            font_size=16,
                            x_alignment="center",
                            y_alignment="bottom"
                        )

        # game.draw_debug_dot((0, 0))
        game.render_text("pos: " + str(camera.position), (0, 0), color=(255, 0, 0))
        game.render_text("zoom: " + str(camera.zoom), (0, 20), color=(255, 0, 0))
        game.render_text("mouse pos: " + str(game.world_position(pygame.mouse.get_pos())), (0, 40), color=(255, 0, 0))
        game.render_text("stavba tratě: " + str(RAILWAY_MODE), (0, 60), color=(255, 0, 0))
        game.render_text("plánování spoje: " + str(ROUTE_MODE), (0, 80), color=(255, 0, 0))
        game.render_text("zobrazení spojů: " + str(SHOW_ROUTES), (0, 100), color=(255, 0, 0))
        game.render_text("balance: " + str(int(economy.balance)) + economy.currency_symbol, (0, 120), color=(255, 0, 0))
        game.render_text("(ctrl+s) uložit hru | (ctrl+o) načíst hru", (0, 140), color=(255, 255, 0))

        if RAILWAY_MODE and len(world.railways) > 0 and len(world.railways[-1].points) > 1:
            pts = world.railways[-1].points
            
            for point in pts[:-1]:
                game.draw_debug_dot(point, 3)

            current_cost = sum(math.dist(pts[i-1], pts[i]) for i in range(1, len(pts))) * RAILWAY_COST_PER_METER
            mouse_pos = pygame.mouse.get_pos()
            color = (0, 255, 0) if economy.can_afford(current_cost) else (255, 0, 0)
            game.render_text(str(int(current_cost)) + economy.currency_symbol, (mouse_pos[0] + 15, mouse_pos[1] + 15), color=color)

        if ROUTE_MODE:
            if len(current_route_stations) > 0:
                for i in range(len(current_route_stations) - 1):
                    p1 = game.screen_position(current_route_stations[i].position)
                    p2 = game.screen_position(current_route_stations[i+1].position)
                    pygame.draw.line(game.screen, (0, 255, 255), p1, p2, 5)
                
                for i, st in enumerate(current_route_stations):
                    if current_route_stop_flags[i]:
                        pygame.draw.circle(game.screen, (255, 255, 0), game.screen_position(st.position), 8, 3)

                p_last = game.screen_position(current_route_stations[-1].position)
                pygame.draw.line(game.screen, (0, 255, 255), p_last, pygame.mouse.get_pos(), 2)

        time_str = game.get_time_string()
        if game.time_paused:
            time_str += " (pozastaveno)"
        
        screen_w = game.screen.get_width()
        screen_h = game.screen.get_height()
        game.render_text(time_str, (screen_w - 10, screen_h - 10), color=(255, 255, 255), x_alignment="right", y_alignment="bottom", font_size=24)

        if notification_timer > 0:
            game.render_text(notification_text, (screen_w / 2, screen_h - 30), color=(255, 255, 255), x_alignment="center", y_alignment="bottom", font_size=32)

        if menu_state["mode"] != "closed":
            menu_surface = pygame.Surface((400, 400))
            menu_surface.fill((50, 50, 50))
            game.screen.blit(menu_surface, (screen_w/2 - 200, screen_h/2 - 200))
            
            y_offset = screen_h/2 - 180
            x_offset = screen_w/2 - 180
            
            game.render_text(f"MENU: {menu_state['mode']} (ESC zrušit)", (x_offset, y_offset), color=(255, 255, 0))
            y_offset += 30
            
            if menu_state["mode"] == "main":
                opts = ["1: Koupit lokomotivu", "2: Koupit vagon", "3: Sestavit soupravu (z inventáře)", "4: Inventář (zobrazení a prodej)"]
                for o in opts:
                    game.render_text(o, (x_offset, y_offset))
                    y_offset += 25
                y_offset += 15
                game.render_text(f"Zůstatek: {int(economy.balance)}{economy.currency_symbol}", (x_offset, y_offset), color=(0,255,0))
                y_offset += 25
                game.render_text(f"Volné lokomotivy: {len(owned_locos)}", (x_offset, y_offset))
                y_offset += 25
                game.render_text(f"Volné vagony: {len(owned_wagons)}", (x_offset, y_offset))
                y_offset += 25
                game.render_text(f"Sestavené soupravy: {len(assembled_trains)}", (x_offset, y_offset))
                
            elif menu_state["mode"] == "buy_loco":
                for i, t in enumerate(available_loco_types):
                    color = (0,255,0) if economy.can_afford(t.price) else (255,0,0)
                    game.render_text(f"{i+1}: {t.name} - {int(t.price)}{economy.currency_symbol}", (x_offset, y_offset), color=color)
                    y_offset += 25
            elif menu_state["mode"] == "buy_wagon":
                for i, t in enumerate(available_wagon_types):
                    color = (0,255,0) if economy.can_afford(t.price) else (255,0,0)
                    game.render_text(f"{i+1}: {t.name} - {int(t.price)}{economy.currency_symbol}", (x_offset, y_offset), color=color)
                    y_offset += 25
            elif menu_state["mode"] == "assemble_loco":
                game.render_text("Vyberte lokomotivu pro novou soupravu:", (x_offset, y_offset), color=(255,255,255))
                y_offset += 25
                for i, loc in enumerate(owned_locos):
                    health_pct = int(loc.health * 100)
                    game.render_text(f"{i+1}: {loc.type.name} [zdraví: {health_pct}%]", (x_offset, y_offset))
                    y_offset += 25
            elif menu_state["mode"] == "assemble_wagons":
                game.render_text(f"Loko: {menu_state['temp_loco'].type.name}", (x_offset, y_offset), color=(0,255,255))
                y_offset += 25
                game.render_text(f"Vagony: {len(menu_state['temp_wagons'])}", (x_offset, y_offset), color=(0,255,255))
                y_offset += 25
                game.render_text("Přidejte vagony a stiskněte ENTER", (x_offset, y_offset), color=(255,255,0))
                y_offset += 25
                for i, wag in enumerate(owned_wagons):
                    if y_offset > screen_h/2 + 180:
                        game.render_text("... další nezobrazeny", (x_offset, y_offset))
                        break
                    health_pct = int(wag.health * 100)
                    game.render_text(f"{i+1}: {wag.type.name} [zdraví: {health_pct}%]", (x_offset, y_offset))
                    y_offset += 25
            elif menu_state["mode"] == "inventory_main":
                game.render_text("1: Volné lokomotivy", (x_offset, y_offset))
                y_offset += 25
                game.render_text("2: Volné vagony", (x_offset, y_offset))
                y_offset += 25
                game.render_text("3: Sestavené soupravy", (x_offset, y_offset))
                y_offset += 25
                game.render_text("4: Aktivní soupravy na tratích", (x_offset, y_offset))
                y_offset += 25
            elif menu_state["mode"] == "inventory_locos":
                types_in_inv = []
                for l in owned_locos:
                    if l.type not in types_in_inv: types_in_inv.append(l.type)
                if not types_in_inv:
                    game.render_text("Žádné volné lokomotivy", (x_offset, y_offset), color=(255,0,0))
                for i, t in enumerate(types_in_inv):
                    if y_offset > screen_h/2 + 180: break
                    count = sum(1 for l in owned_locos if l.type == t)
                    first_loco = min((l for l in owned_locos if l.type == t), key=lambda x: x.health)
                    sell_p = int(first_loco.get_sell_price() * TRAIN_SELL_MULTIPLIER)
                    repair_c = int(first_loco.get_repair_cost())
                    health_pct = int(first_loco.health * 100)
                    game.render_text(f"{t.name} ({count}x) [zdraví: {health_pct}%] - [{i*2+1}] prodat (1ks) za {sell_p}{economy.currency_symbol} | [{i*2+2}] opravit za {repair_c}{economy.currency_symbol}", (x_offset, y_offset))
                    y_offset += 25
            elif menu_state["mode"] == "inventory_wagons":
                types_in_inv = []
                for w in owned_wagons:
                    if w.type not in types_in_inv: types_in_inv.append(w.type)
                if not types_in_inv:
                    game.render_text("Žádné volné vagony", (x_offset, y_offset), color=(255,0,0))
                for i, t in enumerate(types_in_inv):
                    if y_offset > screen_h/2 + 180: break
                    count = sum(1 for w in owned_wagons if w.type == t)
                    first_wagon = min((w for w in owned_wagons if w.type == t), key=lambda x: x.health)
                    sell_p = int(first_wagon.get_sell_price() * TRAIN_SELL_MULTIPLIER)
                    repair_c = int(first_wagon.get_repair_cost())
                    health_pct = int(first_wagon.health * 100)
                    game.render_text(f"{t.name} ({count}x) [zdraví: {health_pct}%] - [{i*2+1}] prodat (1ks) za {sell_p}{economy.currency_symbol} | [{i*2+2}] opravit za {repair_c}{economy.currency_symbol}", (x_offset, y_offset))
                    y_offset += 25
            elif menu_state["mode"] == "inventory_trains":
                if not assembled_trains:
                    game.render_text("Žádné sestavené soupravy", (x_offset, y_offset), color=(255,0,0))
                for i, tr in enumerate(assembled_trains):
                    if y_offset > screen_h/2 + 180: break
                    sell_p = int((tr["loco"].get_sell_price() + sum(w.get_sell_price() for w in tr["wagons"])) * TRAIN_SELL_MULTIPLIER)
                    repair_c = int(tr["loco"].get_repair_cost() + sum(w.get_repair_cost() for w in tr["wagons"]))
                    health_pct = int((tr["loco"].health + sum(w.health for w in tr["wagons"])) / (1 + len(tr["wagons"])) * 100)
                    game.render_text(f"{tr['loco'].type.name} + {len(tr['wagons'])} vagonů [průměrné zdraví: {health_pct}%]:", (x_offset, y_offset), color=(200, 200, 200))
                    y_offset += 20
                    game.render_text(f"  [{i*3+1}] prodat za {sell_p}{economy.currency_symbol} | [{i*3+2}] rozložit | [{i*3+3}] opravit za {repair_c}{economy.currency_symbol}", (x_offset, y_offset))
                    y_offset += 25
            elif menu_state["mode"] == "inventory_active":
                if not world.active_trains:
                    game.render_text("Žádné aktivní soupravy na tratích", (x_offset, y_offset), color=(255,0,0))
                for i, at in enumerate(world.active_trains):
                    if y_offset > screen_h/2 + 180: break
                    repair_c = int(at.train.locomotive.get_repair_cost() + sum(w.get_repair_cost() for w in at.train.wagons))
                    health_pct = int((at.train.locomotive.health + sum(w.health for w in at.train.wagons)) / (1 + len(at.train.wagons)) * 100)
                    game.render_text(f"{at.train.locomotive.type.name} + {len(at.train.wagons)} vagonů na cestě k {at.route.stations[-1].name} [zdraví: {health_pct}%]:", (x_offset, y_offset), color=(200, 200, 200))
                    y_offset += 20
                    game.render_text(f"  [{i*2+1}] stáhnout do depa | [{i*2+2}] opravit za {repair_c}{economy.currency_symbol}", (x_offset, y_offset))
                    y_offset += 25
            elif menu_state["mode"] == "assign_train":
                game.render_text("Vyberte sestavenou soupravu pro spoj:", (x_offset, y_offset), color=(255,255,255))
                y_offset += 25
                for i, tr in enumerate(assembled_trains):
                    if y_offset > screen_h/2 + 180:
                        break
                    game.render_text(f"{i+1}: Lokomotiva {tr['loco'].type.name} + {len(tr['wagons'])} vagonů", (x_offset, y_offset))
                    y_offset += 25
                if len(assembled_trains) == 0:
                    game.render_text("Žádné volné sestavené soupravy!", (x_offset, y_offset), color=(255,0,0))

    game.run(
        loop=loop,
        event_handler=event_handler
    )

if __name__ == "__main__":
    main()