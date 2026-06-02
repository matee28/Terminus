import pygame

import TerminusEngine
import TerminusEngine.World
import TerminusEngine.Economy
import TerminusEngine.Vehicles


import os
import math

import heapq


RAILWAY_MODE = False
RAILWAY_MODE_SNAP_DIST_PX = 20
ROUTE_MODE = False
current_route_stations = []
current_route_stop_flags = []
current_route_railways = []

INITIAL_BALANCE = 10000000000

RAILWAY_COST_PER_METER = 10
TRAIN_SELL_MULTIPLIER = 0.6

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

    print(world)



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

    # definice lokomotiv
    type_loco_ce = TerminusEngine.Vehicles.LocomotiveType("CityElefant (lokomotiva)", max_speed=140.0, power=2000.0, price=500000.0, texture_name="loco_ce", passenger_capacity=59)
    type_loco_742 = TerminusEngine.Vehicles.LocomotiveType("Lokomotiva řady 742", max_speed=90.0, power=883.0, price=300000.0, texture_name="loco_742")
    type_loco_vectron = TerminusEngine.Vehicles.LocomotiveType("Siemens Vectron", max_speed=180.0, power=6400.0, price=1000000.0, texture_name="loco_vectron") # nákladní verze má max 160 km/h, osobní 200 km/h -> kompromis

    # definice osobních vagonů
    type_wagon_p_ce = TerminusEngine.Vehicles.PassengerWagonType("CityElefant (vložený vůz)", passenger_capacity=134, price=150000.0, texture_name="wagon_p_ce")
    type_wagon_p_b = TerminusEngine.Vehicles.PassengerWagonType("Vůz třídy B", passenger_capacity=80, price=100000.0, texture_name="wagon_p_b")

    # definice nákladních vagonů
    type_wagon_c_single = TerminusEngine.Vehicles.CargoWagonType("Kontejnerový vagon (Single)", cargo_capacity=30.0, price=80000.0, texture_name="wagon_c_single")
    type_wagon_c_double = TerminusEngine.Vehicles.CargoWagonType("Kontejnerový vagon (Double)", cargo_capacity=60.0, price=140000.0, texture_name="wagon_c_double")

    # seznamy pro UI
    available_loco_types = [type_loco_ce, type_loco_742, type_loco_vectron]
    available_wagon_types = [type_wagon_p_ce, type_wagon_p_b, type_wagon_c_single, type_wagon_c_double]
    
    # inventář
    owned_locos = []
    owned_wagons = []
    assembled_trains = [] # {"name": str, "loco": loco, "wagons": list}
    
    menu_state = {"mode": "closed", "temp_loco": None, "temp_wagons": [], "temp_route": None}


    def event_handler(event: pygame.event.Event):
        global RAILWAY_MODE, ROUTE_MODE

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
                        menu_state["temp_loco"] = None
                        menu_state["temp_wagons"] = []
                    elif menu_state["mode"] in ["inventory_locos", "inventory_wagons", "inventory_trains"]:
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
                    elif menu_state["mode"] == "inventory_locos":
                        types_in_inv = []
                        for l in owned_locos:
                            if l.type not in types_in_inv: types_in_inv.append(l.type)
                        if idx < len(types_in_inv):
                            t_to_sell = types_in_inv[idx]
                            for i, l in enumerate(owned_locos):
                                if l.type == t_to_sell:
                                    owned_locos.pop(i)
                                    economy.add(t_to_sell.price * TRAIN_SELL_MULTIPLIER)
                                    break
                    elif menu_state["mode"] == "inventory_wagons":
                        types_in_inv = []
                        for w in owned_wagons:
                            if w.type not in types_in_inv: types_in_inv.append(w.type)
                        if idx < len(types_in_inv):
                            t_to_sell = types_in_inv[idx]
                            for i, w in enumerate(owned_wagons):
                                if w.type == t_to_sell:
                                    owned_wagons.pop(i)
                                    economy.add(t_to_sell.price * TRAIN_SELL_MULTIPLIER)
                                    break
                    elif menu_state["mode"] == "inventory_trains":
                        if idx < len(assembled_trains):
                            tr = assembled_trains.pop(idx)
                            sell_price = (tr["loco"].type.price + sum(w.type.price for w in tr["wagons"])) * TRAIN_SELL_MULTIPLIER
                            economy.add(sell_price)
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
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # levé tlačítko = přidání stanice
                    point_position = game.world_position(event.pos)
                    closest_station, distance = world.get_closest_station(point_position)
                    if closest_station and game.screen_distance(distance) < RAILWAY_MODE_SNAP_DIST_PX:
                        if len(current_route_stations) == 0:
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
            if event.type == pygame.MOUSEBUTTONDOWN:
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
        game.render_image(
            texture_name="terrain",
            world_position=(0, 0),
            size=(0, 0),
            tiled=True
        )

        game.draw_debug_dot(game.world_position(pygame.mouse.get_pos()))
        game.draw_debug_dot(game.world_position((pygame.display.get_surface().get_width()/2, pygame.display.get_surface().get_height()/2)), 5)

        for city in world.cities:
            game.draw_debug_dot(city.position, size=city.radius, text=city.name + " (" + str(int(city.radius)) + ")")
            for station in city.stations:
                game.draw_debug_dot(station.position, size=0, text=station.name)
                
                # zobrazení kapacity stanice
                if station.passenger_capacity > 0:
                    game.render_text(
                        f"{int(station.passengers)}/{station.passenger_capacity}",
                        game.screen_position((station.position[0], station.position[1] - 50)),
                        color=(255, 255, 0),
                        font_size=16,
                        x_alignment="center",
                        y_alignment="bottom"
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

        # aktualizace a vykreslení vlaků
        dt_seconds = game.clock.get_time() / 1000.0
        
        if not game.time_paused:
            world.update(dt_seconds, game.time_scale, game.train_speed_multiplier, game.passenger_generation_rate, game.get_point_on_path)

        for at in world.active_trains:
            if len(at.route.railways) == 0: continue
            
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
                
                # počet cestujících a debug dot na pozici vlaku
                if i == 0:
                    game.draw_debug_dot(pos, size=5)
                    game.render_text(
                        f"{int(at.passengers)}/{at.get_passenger_capacity()}",
                        game.screen_position((pos[0], pos[1] - 30)),
                        color=(0, 200, 255),
                        font_size=16,
                        x_alignment="center",
                        y_alignment="bottom"
                    )

        game.draw_debug_dot((0, 0))
        game.render_text("pos: " + str(camera.position), (0, 0), color=(255, 0, 0))
        game.render_text("zoom: " + str(camera.zoom), (0, 20), color=(255, 0, 0))
        game.render_text("mouse pos: " + str(game.world_position(pygame.mouse.get_pos())), (0, 40), color=(255, 0, 0))
        game.render_text("stavba tratě: " + str(RAILWAY_MODE), (0, 60), color=(255, 0, 0))
        game.render_text("plánování spoje: " + str(ROUTE_MODE), (0, 80), color=(255, 0, 0))
        game.render_text("balance: " + str(int(economy.balance)) + economy.currency_symbol, (0, 100), color=(255, 0, 0))

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
                    game.render_text(f"{i+1}: {loc.type.name}", (x_offset, y_offset))
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
                    game.render_text(f"{i+1}: {wag.type.name}", (x_offset, y_offset))
                    y_offset += 25
            elif menu_state["mode"] == "inventory_main":
                game.render_text("1: Volné lokomotivy", (x_offset, y_offset))
                y_offset += 25
                game.render_text("2: Volné vagony", (x_offset, y_offset))
                y_offset += 25
                game.render_text("3: Sestavené soupravy", (x_offset, y_offset))
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
                    sell_p = int(t.price * TRAIN_SELL_MULTIPLIER)
                    game.render_text(f"{i+1}: {t.name} ({count}x) - prodat 1ks za {sell_p}{economy.currency_symbol}", (x_offset, y_offset))
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
                    sell_p = int(t.price * TRAIN_SELL_MULTIPLIER)
                    game.render_text(f"{i+1}: {t.name} ({count}x) - prodat 1ks za {sell_p}{economy.currency_symbol}", (x_offset, y_offset))
                    y_offset += 25
            elif menu_state["mode"] == "inventory_trains":
                if not assembled_trains:
                    game.render_text("Žádné sestavené soupravy", (x_offset, y_offset), color=(255,0,0))
                for i, tr in enumerate(assembled_trains):
                    if y_offset > screen_h/2 + 180: break
                    sell_p = int((tr["loco"].type.price + sum(w.type.price for w in tr["wagons"])) * TRAIN_SELL_MULTIPLIER)
                    game.render_text(f"{i+1}: {tr['loco'].type.name} + {len(tr['wagons'])} vagonů - prodat za {sell_p}{economy.currency_symbol}", (x_offset, y_offset))
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