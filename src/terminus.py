import pygame

import TerminusEngine
import TerminusEngine.World
import TerminusEngine.Economy
import TerminusEngine.Vehicles
import TerminusEngine.SaveLoad
import TerminusEngine.UI


import os
import math
import random
import heapq


GAME_SAVE_FILE = "game.json"

RAILWAY_MODE = False
RAILWAY_MODE_SNAP_DIST_PX = 20
ROUTE_MODE = False
SHOW_ROUTES = False
DEMOLISH_MODE = False
notification_text = ""
notification_timer = 0.0
current_route_stations = []
current_route_stop_flags = []
current_route_railways = []

INITIAL_BALANCE = 5000000.0

RAILWAY_COST_PER_METER = 10
TRAIN_SELL_MULTIPLIER = 0.6

# výdělek
PASSENGER_REWARD = 40
CARGO_REWARD = 80

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

    ui = TerminusEngine.UI.UIManager(game)


    game.load_image("terrain", "assets/terrain/seamless_2048.png")
    game.load_image("rail_tile", "assets/rails/rail_tile_1.png", rotation=90)
    game.load_image("station", "assets/buildings/station.png")

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
    
    menu_state = {"mode": "closed", "last_mode": "closed", "temp_loco": None, "temp_wagons": [], "temp_route": None, "scroll_y": 0, "max_scroll": 0}
    mouse_down_pos = (0, 0)


    game.camera.position = (0, 0)
    game.camera.zoom = game.camera.min_zoom

    def point_to_segment_dist(p, a, b):
        p = pygame.math.Vector2(p)
        a = pygame.math.Vector2(a)
        b = pygame.math.Vector2(b)
        ab = b - a
        ap = p - a
        if ab.length_squared() == 0:
            return ap.length()
        t = max(0, min(1, ap.dot(ab) / ab.length_squared()))
        proj = a + t * ab
        return (p - proj).length()

    def undo_action():
        global RAILWAY_MODE, ROUTE_MODE
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
    def event_handler(event: pygame.event.Event):
        global RAILWAY_MODE, ROUTE_MODE, SHOW_ROUTES, DEMOLISH_MODE, notification_text, notification_timer
        nonlocal mouse_down_pos

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_down_pos = event.pos

        # zoom nebo scroll
        if event.type == pygame.MOUSEWHEEL:
            if menu_state["mode"] != "closed":
                if menu_state["mode"] not in ["main", "inventory_main"]:
                    menu_state["scroll_y"] -= event.y * 40
                    if menu_state["scroll_y"] < 0:
                        menu_state["scroll_y"] = 0
                    elif menu_state["scroll_y"] > menu_state.get("max_scroll", 0):
                        menu_state["scroll_y"] = menu_state.get("max_scroll", 0)
            else:
                if event.y > 0:
                    camera.zoom_in()
                else:
                    camera.zoom_out()

        # pohyb kamery
        if event.type == pygame.MOUSEMOTION:
            if event.buttons[0] and menu_state["mode"] == "closed":
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
                
                return # nepokračovat ve zpracování hry, pokud v menu

            if event.key == pygame.K_m:
                menu_state["mode"] = "main"

            if event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                if TerminusEngine.SaveLoad.save_game(GAME_SAVE_FILE, economy, game, world, owned_locos, owned_wagons, assembled_trains):
                    notification_text = "Hra byla úspěšně uložena"
                    notification_timer = 3.0

            if event.key == pygame.K_o and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                if TerminusEngine.SaveLoad.load_game(GAME_SAVE_FILE, economy, game, world, owned_locos, owned_wagons, assembled_trains, available_loco_types, available_wagon_types):
                    notification_text = "Hra byla úspěšně načtena"
                    notification_timer = 3.0
                else:
                    notification_text = "Soubor s uloženou hrou nenalezen"
                    notification_timer = 3.0

            # RAILWAY_MODE toggle = T
            if event.key == pygame.K_t:
                RAILWAY_MODE = not RAILWAY_MODE
                if RAILWAY_MODE:
                    ROUTE_MODE = False
                    DEMOLISH_MODE = False
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
                    DEMOLISH_MODE = False
                    if len(world.railways) > 0 and world.railways[-1].station_b is None:
                        world.railways.remove(world.railways[-1])

            # DEMOLISH_MODE toggle = D
            if event.key == pygame.K_d:
                DEMOLISH_MODE = not DEMOLISH_MODE
                if DEMOLISH_MODE:
                    RAILWAY_MODE = False
                    ROUTE_MODE = False
                    current_route_stations.clear()
                    current_route_stop_flags.clear()
                    current_route_railways.clear()
                    if len(world.railways) > 0 and world.railways[-1].station_b is None:
                        world.railways.remove(world.railways[-1])

            # smazání posledního bodu tratě = Z
            if event.key == pygame.K_z:
                undo_action()

            # pozastavení času = P
            if event.key == pygame.K_p:
                game.time_paused = not game.time_paused

        # demolice a rušení spoju
        if DEMOLISH_MODE and event.type == pygame.MOUSEBUTTONUP and event.button == 1 and menu_state["mode"] == "closed":
            mpos = event.pos
            action_taken = False
            
            if SHOW_ROUTES and not ROUTE_MODE and not RAILWAY_MODE:
                route_clicked = -1
                for i, at in enumerate(world.active_trains):
                    if hasattr(at.route, 'railways'):
                        hit = False
                        for rw in at.route.railways:
                            for j in range(len(rw.points)-1):
                                p1 = game.screen_position(rw.points[j])
                                p2 = game.screen_position(rw.points[j+1])
                                if point_to_segment_dist(mpos, p1, p2) < RAILWAY_MODE_SNAP_DIST_PX:
                                    hit = True
                                    break
                            if hit: break
                        if hit:
                            route_clicked = i
                            break
                if route_clicked != -1:
                    at = world.active_trains.pop(route_clicked)
                    for src in at.audio_sources:
                        game.audio.stop_source(src)
                    assembled_trains.append({"loco": at.train.locomotive, "wagons": at.train.wagons})
                    notification_text = "Spoj byl zrušen a vlak se vrátil do depa"
                    notification_timer = 3.0
                    action_taken = True

            if DEMOLISH_MODE and not action_taken:
                rw_clicked = -1
                for i, rw in enumerate(world.railways):
                    if RAILWAY_MODE and i == len(world.railways) - 1:
                        continue
                    hit = False
                    for j in range(len(rw.points)-1):
                        p1 = game.screen_position(rw.points[j])
                        p2 = game.screen_position(rw.points[j+1])
                        if point_to_segment_dist(mpos, p1, p2) < RAILWAY_MODE_SNAP_DIST_PX:
                            hit = True
                            break
                    if hit:
                        rw_clicked = i
                        break
                        
                if rw_clicked != -1:
                    clicked_rw = world.railways[rw_clicked]
                    trains_to_remove = []
                    for i, at in enumerate(world.active_trains):
                        if clicked_rw in at.route.railways:
                            trains_to_remove.append(i)
                            
                    for i in reversed(trains_to_remove):
                        at = world.active_trains.pop(i)
                        for src in at.audio_sources:
                            game.audio.stop_source(src)
                        assembled_trains.append({"loco": at.train.locomotive, "wagons": at.train.wagons})
                        
                    world.railways.pop(rw_clicked)
                    notification_text = "Trať byla zbourána"
                    notification_timer = 3.0
                    action_taken = True

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
                                notification_text = "Trať mezi těmito stanicemi již existuje"
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
        global notification_text, notification_timer, RAILWAY_MODE, ROUTE_MODE, SHOW_ROUTES, DEMOLISH_MODE
        dt_seconds = game.clock.get_time() / 1000.0
        if notification_timer > 0:
            notification_timer -= dt_seconds
        
        if not game.time_paused:
            world.update(dt_seconds, game.time_scale, game.train_speed_multiplier, game.passenger_generation_rate, game.cargo_generation_rate, game.get_point_on_path, economy, PASSENGER_REWARD, CARGO_REWARD)

        hovered_route_idx = -1
        hovered_rw_idx = -1
        
        if menu_state["mode"] == "closed":
            mpos = pygame.mouse.get_pos()
            
            if SHOW_ROUTES and DEMOLISH_MODE and not ROUTE_MODE and not RAILWAY_MODE:
                for i, at in enumerate(world.active_trains):
                    if hasattr(at.route, 'railways'):
                        hit = False
                        for rw in at.route.railways:
                            for j in range(len(rw.points)-1):
                                p1 = game.screen_position(rw.points[j])
                                p2 = game.screen_position(rw.points[j+1])
                                if point_to_segment_dist(mpos, p1, p2) < RAILWAY_MODE_SNAP_DIST_PX:
                                    hit = True
                                    break
                            if hit: break
                        if hit:
                            hovered_route_idx = i
                            break
                            
            if DEMOLISH_MODE and hovered_route_idx == -1:
                for i, rw in enumerate(world.railways):
                    if RAILWAY_MODE and i == len(world.railways) - 1:
                        continue
                    hit = False
                    for j in range(len(rw.points)-1):
                        p1 = game.screen_position(rw.points[j])
                        p2 = game.screen_position(rw.points[j+1])
                        if point_to_segment_dist(mpos, p1, p2) < RAILWAY_MODE_SNAP_DIST_PX:
                            hit = True
                            break
                    if hit:
                        hovered_rw_idx = i
                        break

        game.render_image(
            texture_name="terrain",
            world_position=(0, 0),
            size=(0, 0),
            tiled=True
        )

        for city in world.cities:
            game.render_city(city.position, radius=city.radius)

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
                if i == hovered_rw_idx:
                    scr_pts = [game.screen_position(p) for p in railway.points]
                    pygame.draw.lines(game.screen, (255, 0, 0), False, scr_pts, 8)

        if SHOW_ROUTES:
            for i, at in enumerate(world.active_trains):
                if hasattr(at.route, 'color'):
                    for rw in at.route.railways:
                        if len(rw.points) > 1:
                            scr_pts = [game.screen_position(p) for p in rw.points]
                            color = (255, 0, 0) if i == hovered_route_idx else at.route.color
                            width = 8 if i == hovered_route_idx else 4
                            pygame.draw.lines(game.screen, color, False, scr_pts, width)

        for at in world.active_trains:
            if len(at.route.railways) == 0:
                continue
            
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
            if len(pts) < 2:
                continue
            
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

                    if camera.zoom <= 0.2:
                        pygame.draw.circle(game.screen, (255, 50, 50), game.screen_position(pos), 3)

        for city in world.cities:
            for station in city.stations:
                game.render_image("station", station.position)
                if camera.zoom <= 0.01:
                    game.render_station(station.position)

        for city in world.cities:
            if camera.zoom <= 0.01:
                game.render_text(
                    city.name,
                    game.screen_position(city.position),
                    color=(255, 255, 255),
                    x_alignment="center",
                    y_alignment="center",
                    outline_color=(0, 0, 0),
                    outline_width=1
                )
            if camera.zoom > 0.01:
                for station in city.stations:
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
                        
        for at in world.active_trains:
            if hasattr(at, 'position'):
                pos = at.position
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
        ui.label((10, game.screen.get_height() - 40), economy.format_money(economy.balance), color=(100, 255, 100), size="large")

        if RAILWAY_MODE and len(world.railways) > 0 and len(world.railways[-1].points) > 1:
            pts = world.railways[-1].points
            
            # for point in pts[:-1]:
            #    game.draw_debug_dot(point, 3)

            current_cost = sum(math.dist(pts[i-1], pts[i]) for i in range(1, len(pts))) * RAILWAY_COST_PER_METER
            mouse_pos = pygame.mouse.get_pos()
            color = (0, 255, 0) if economy.can_afford(current_cost) else (255, 0, 0)
            game.render_text(economy.format_money(current_cost), (mouse_pos[0] + 15, mouse_pos[1] + 15), color=color)

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

        ui.update()
        
        if menu_state["mode"] != menu_state.get("last_mode"):
            menu_state["scroll_y"] = 0
            menu_state["max_scroll"] = 0
            menu_state["last_mode"] = menu_state["mode"]
        
        if menu_state["mode"] == "closed":
            if ui.button((10, 10, 160, 40), "Stavba tratí (T)", color=(60, 160, 80) if RAILWAY_MODE else (50, 50, 50)):
                RAILWAY_MODE = not RAILWAY_MODE
                if RAILWAY_MODE:
                    ROUTE_MODE = False
                    DEMOLISH_MODE = False
                    current_route_stations.clear()
                    current_route_stop_flags.clear()
                    current_route_railways.clear()
                    world.add_railway(TerminusEngine.World.Railway(None, None, []))
                else:
                    if len(world.railways) > 0 and world.railways[-1].station_b is None:
                        world.railways.remove(world.railways[-1])
                        
            if ui.button((180, 10, 180, 40), "Plánování spojů (R)", color=(60, 160, 80) if ROUTE_MODE else (50, 50, 50)):
                ROUTE_MODE = not ROUTE_MODE
                current_route_stations.clear()
                current_route_stop_flags.clear()
                current_route_railways.clear()
                if ROUTE_MODE:
                    RAILWAY_MODE = False
                    DEMOLISH_MODE = False
                    if len(world.railways) > 0 and world.railways[-1].station_b is None:
                        world.railways.remove(world.railways[-1])

            if ui.button((370, 10, 180, 40), "Zobrazit spoje (S)", color=(60, 160, 80) if SHOW_ROUTES else (50, 50, 50)):
                SHOW_ROUTES = not SHOW_ROUTES

            if ui.button((560, 10, 140, 40), "Demolice (D)", color=(180, 60, 60) if DEMOLISH_MODE else (50, 50, 50)):
                DEMOLISH_MODE = not DEMOLISH_MODE
                if DEMOLISH_MODE:
                    RAILWAY_MODE = False
                    ROUTE_MODE = False
                    current_route_stations.clear()
                    current_route_stop_flags.clear()
                    current_route_railways.clear()
                    if len(world.railways) > 0 and world.railways[-1].station_b is None:
                        world.railways.remove(world.railways[-1])

            show_undo = False
            if RAILWAY_MODE and len(world.railways) > 0 and len(world.railways[-1].points) > 1:
                show_undo = True
            elif ROUTE_MODE and len(current_route_stations) > 0:
                show_undo = True
                
            if show_undo:
                if ui.button((710, 10, 100, 40), "Zpět (Z)", color=(180, 60, 60), hover_color=(200, 80, 80)):
                    undo_action()

            if ui.button((screen_w - 120, 10, 110, 40), "Menu (M)", color=(50, 50, 50)):
                menu_state["mode"] = "main"

        if menu_state["mode"] != "closed":
            ui.panel((screen_w/2 - 320, screen_h/2 - 270, 640, 540))
            
            y_offset = screen_h/2 - 250
            x_offset = screen_w/2 - 300
            
            title_map = {
                "main": "Hlavní menu",
                "buy_loco": "Nákup lokomotivy",
                "buy_wagon": "Nákup vagonu",
                "assemble_loco": "Sestavení soupravy (Výběr lokomotivy)",
                "assemble_wagons": "Sestavení soupravy (Přidávání vagonů)",
                "inventory_main": "Inventář",
                "inventory_locos": "Volné lokomotivy v depu",
                "inventory_wagons": "Volné vagony v depu",
                "inventory_trains": "Sestavené soupravy v depu",
                "inventory_active": "Aktivní soupravy na tratích",
                "assign_train": "Nasazení soupravy na spoj"
            }
            menu_title = title_map.get(menu_state['mode'], "Menu")
            
            ui.label((screen_w/2, y_offset + 15), menu_title, color=(220, 220, 220), align="center", size="normal")
            
            if menu_state["mode"] != "main" and menu_state["mode"] != "assign_train":
                if ui.button((x_offset, y_offset, 80, 30), "< Zpět", color=(60, 60, 60)):
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
            
            if ui.button((screen_w/2 + 270, y_offset, 30, 30), "X", color=(200, 50, 50), hover_color=(230, 70, 70)):
                menu_state["mode"] = "closed"
                menu_state["temp_route"] = None
                if menu_state.get("temp_loco") is not None:
                    owned_locos.append(menu_state["temp_loco"])
                    menu_state["temp_loco"] = None
                if menu_state.get("temp_wagons"):
                    owned_wagons.extend(menu_state["temp_wagons"])
                    menu_state["temp_wagons"] = []

            y_offset += 60
            
            start_y_offset = y_offset
            clip_rect = pygame.Rect(screen_w/2 - 310, start_y_offset, 620, screen_h/2 + 260 - start_y_offset)
            old_clip = game.screen.get_clip()
            game.screen.set_clip(clip_rect)
            
            if menu_state["mode"] not in ["main", "inventory_main"]:
                y_offset -= menu_state["scroll_y"]
            
            if menu_state["mode"] == "main":
                if ui.button((x_offset, y_offset, 290, 40), "Koupit lokomotivu"):
                    menu_state["mode"] = "buy_loco"
                if ui.button((x_offset + 310, y_offset, 290, 40), "Koupit vagon"):
                    menu_state["mode"] = "buy_wagon"
                y_offset += 50
                if ui.button((x_offset, y_offset, 290, 40), "Sestavit soupravu"):
                    menu_state["mode"] = "assemble_loco"
                    menu_state["temp_loco"] = None
                    menu_state["temp_wagons"] = []
                if ui.button((x_offset + 310, y_offset, 290, 40), "Inventář"):
                    menu_state["mode"] = "inventory_main"
                y_offset += 60
                
                ui.label((x_offset, y_offset), f"Zůstatek: {economy.format_money(economy.balance)}", color=(100, 255, 100))
                y_offset += 30
                ui.label((x_offset, y_offset), f"Volné lokomotivy: {len(owned_locos)}")
                y_offset += 30
                ui.label((x_offset, y_offset), f"Volné vagony: {len(owned_wagons)}")
                y_offset += 30
                ui.label((x_offset, y_offset), f"Sestavené soupravy: {len(assembled_trains)}")
                y_offset += 50
                
                if ui.button((x_offset, y_offset, 290, 40), "Uložit hru"):
                    if TerminusEngine.SaveLoad.save_game(GAME_SAVE_FILE, economy, game, world, owned_locos, owned_wagons, assembled_trains):
                        notification_text = "Hra byla úspěšně uložena"
                        notification_timer = 3.0
                if ui.button((x_offset + 310, y_offset, 290, 40), "Načíst hru"):
                    if TerminusEngine.SaveLoad.load_game(GAME_SAVE_FILE, economy, game, world, owned_locos, owned_wagons, assembled_trains, available_loco_types, available_wagon_types):
                        notification_text = "Hra byla úspěšně načtena"
                        notification_timer = 3.0
                    else:
                        notification_text = "Soubor s uloženou hrou nenalezen"
                        notification_timer = 3.0
                
            elif menu_state["mode"] == "buy_loco":
                for t in available_loco_types:
                    can_afford = economy.can_afford(t.price)
                    if ui.button((x_offset, y_offset, 600, 40), f"{t.name} - {economy.format_money(t.price)}", disabled=not can_afford):
                        if can_afford:
                            economy.deduct(t.price)
                            owned_locos.append(TerminusEngine.Vehicles.Locomotive(t))
                    y_offset += 45
            elif menu_state["mode"] == "buy_wagon":
                for t in available_wagon_types:
                    can_afford = economy.can_afford(t.price)
                    if ui.button((x_offset, y_offset, 600, 40), f"{t.name} - {economy.format_money(t.price)}", disabled=not can_afford):
                        if can_afford:
                            economy.deduct(t.price)
                            if isinstance(t, TerminusEngine.Vehicles.PassengerWagonType):
                                owned_wagons.append(TerminusEngine.Vehicles.PassengerWagon(t))
                            else:
                                owned_wagons.append(TerminusEngine.Vehicles.CargoWagon(t))
                    y_offset += 45
            elif menu_state["mode"] == "assemble_loco":
                ui.label((x_offset, y_offset), "Vyberte lokomotivu pro novou soupravu:", color=(255,255,255))
                y_offset += 30
                for i, loc in enumerate(owned_locos):
                    health_pct = int(loc.health * 100)
                    if ui.button((x_offset, y_offset, 600, 35), f"{loc.type.name} [zdraví: {health_pct}%]"):
                        menu_state["temp_loco"] = owned_locos.pop(i)
                        menu_state["mode"] = "assemble_wagons"
                        break
                    y_offset += 40
            elif menu_state["mode"] == "assemble_wagons":
                ui.label((x_offset, y_offset), f"Lokomotiva: {menu_state['temp_loco'].type.name}", color=(0,255,255))
                y_offset += 30
                ui.label((x_offset, y_offset), f"Vagony: {len(menu_state['temp_wagons'])}", color=(0,255,255))
                y_offset += 30
                if ui.button((x_offset, y_offset, 600, 40), "Dokončit soupravu", color=(50, 150, 50)):
                    assembled_trains.append({
                        "loco": menu_state["temp_loco"],
                        "wagons": menu_state["temp_wagons"].copy()
                    })
                    menu_state["mode"] = "main"
                y_offset += 50
                for i, wag in enumerate(owned_wagons):

                    health_pct = int(wag.health * 100)
                    if ui.button((x_offset, y_offset, 600, 35), f"Přidat: {wag.type.name} [zdraví: {health_pct}%]"):
                        menu_state["temp_wagons"].append(owned_wagons.pop(i))
                        break
                    y_offset += 40
            elif menu_state["mode"] == "inventory_main":
                if ui.button((x_offset, y_offset, 600, 40), "Volné lokomotivy"):
                    menu_state["mode"] = "inventory_locos"
                y_offset += 50
                if ui.button((x_offset, y_offset, 600, 40), "Volné vagony"):
                    menu_state["mode"] = "inventory_wagons"
                y_offset += 50
                if ui.button((x_offset, y_offset, 600, 40), "Sestavené soupravy"):
                    menu_state["mode"] = "inventory_trains"
                y_offset += 50
                if ui.button((x_offset, y_offset, 600, 40), "Aktivní soupravy na tratích"):
                    menu_state["mode"] = "inventory_active"
                y_offset += 50
            elif menu_state["mode"] == "inventory_locos":
                types_in_inv = list(set(l.type for l in owned_locos))
                if not types_in_inv:
                    ui.label((x_offset, y_offset), "Žádné volné lokomotivy", color=(255,100,100))
                for t in types_in_inv:

                    count = sum(1 for l in owned_locos if l.type == t)
                    first_loco = min((l for l in owned_locos if l.type == t), key=lambda x: x.health)
                    sell_p = int(first_loco.get_sell_price() * TRAIN_SELL_MULTIPLIER)
                    repair_c = int(first_loco.get_repair_cost())
                    health_pct = int(first_loco.health * 100)
                    ui.label((x_offset, y_offset), f"{t.name} ({count}x) [zdraví: {health_pct}%]")
                    y_offset += 30
                    if ui.button((x_offset, y_offset, 290, 30), f"Prodat: {economy.format_money(sell_p)}"):
                        owned_locos.remove(first_loco)
                        economy.add(sell_p)
                        break
                    if ui.button((x_offset + 310, y_offset, 290, 30), f"Opravit: {economy.format_money(repair_c)}", disabled=not economy.can_afford(repair_c) or first_loco.health == 1.0):
                        if economy.can_afford(repair_c):
                            economy.deduct(repair_c)
                            first_loco.repair()
                            break
                    y_offset += 40
            elif menu_state["mode"] == "inventory_wagons":
                types_in_inv = list(set(w.type for w in owned_wagons))
                if not types_in_inv:
                    ui.label((x_offset, y_offset), "Žádné volné vagony", color=(255,100,100))
                for t in types_in_inv:

                    count = sum(1 for w in owned_wagons if w.type == t)
                    first_wagon = min((w for w in owned_wagons if w.type == t), key=lambda x: x.health)
                    sell_p = int(first_wagon.get_sell_price() * TRAIN_SELL_MULTIPLIER)
                    repair_c = int(first_wagon.get_repair_cost())
                    health_pct = int(first_wagon.health * 100)
                    ui.label((x_offset, y_offset), f"{t.name} ({count}x) [zdraví: {health_pct}%]")
                    y_offset += 30
                    if ui.button((x_offset, y_offset, 290, 30), f"Prodat: {economy.format_money(sell_p)}"):
                        owned_wagons.remove(first_wagon)
                        economy.add(sell_p)
                        break
                    if ui.button((x_offset + 310, y_offset, 290, 30), f"Opravit: {economy.format_money(repair_c)}", disabled=not economy.can_afford(repair_c) or first_wagon.health == 1.0):
                        if economy.can_afford(repair_c):
                            economy.deduct(repair_c)
                            first_wagon.repair()
                            break
                    y_offset += 40
            elif menu_state["mode"] == "inventory_trains":
                if not assembled_trains:
                    ui.label((x_offset, y_offset), "Žádné sestavené soupravy", color=(255,100,100))
                for i, tr in enumerate(assembled_trains):

                    sell_p = int((tr["loco"].get_sell_price() + sum(w.get_sell_price() for w in tr["wagons"])) * TRAIN_SELL_MULTIPLIER)
                    repair_c = int(tr["loco"].get_repair_cost() + sum(w.get_repair_cost() for w in tr["wagons"]))
                    health_pct = int((tr["loco"].health + sum(w.health for w in tr["wagons"])) / (1 + len(tr["wagons"])) * 100)
                    ui.label((x_offset, y_offset), f"{tr['loco'].type.name} + {len(tr['wagons'])} vagonů [zdraví: {health_pct}%]", color=(200, 200, 200))
                    y_offset += 30
                    if ui.button((x_offset, y_offset, 190, 30), f"Prodat: {economy.format_money(sell_p)}"):
                        assembled_trains.pop(i)
                        economy.add(sell_p)
                        break
                    if ui.button((x_offset + 205, y_offset, 190, 30), "Rozložit"):
                        assembled_trains.pop(i)
                        owned_locos.append(tr["loco"])
                        owned_wagons.extend(tr["wagons"])
                        break
                    if ui.button((x_offset + 410, y_offset, 190, 30), f"Opravit: {economy.format_money(repair_c)}", disabled=not economy.can_afford(repair_c) or health_pct == 100):
                        if economy.can_afford(repair_c):
                            economy.deduct(repair_c)
                            tr["loco"].repair()
                            for w in tr["wagons"]:
                                w.repair()
                            break
                    y_offset += 40
            elif menu_state["mode"] == "inventory_active":
                if not world.active_trains:
                    ui.label((x_offset, y_offset), "Žádné aktivní soupravy", color=(255,100,100))
                for i, at in enumerate(world.active_trains):

                    repair_c = int(at.train.locomotive.get_repair_cost() + sum(w.get_repair_cost() for w in at.train.wagons))
                    health_pct = int((at.train.locomotive.health + sum(w.health for w in at.train.wagons)) / (1 + len(at.train.wagons)) * 100)
                    ui.label((x_offset, y_offset), f"{at.train.locomotive.type.name} -> {at.route.stations[-1].name} [zdraví: {health_pct}%]", color=(200, 200, 200))
                    y_offset += 30
                    if ui.button((x_offset, y_offset, 290, 30), "Stáhnout do depa"):
                        world.active_trains.pop(i)
                        for src in at.audio_sources:
                            game.audio.stop_source(src)
                        assembled_trains.append({"loco": at.train.locomotive, "wagons": at.train.wagons})
                        break
                    if ui.button((x_offset + 310, y_offset, 290, 30), f"Opravit: {economy.format_money(repair_c)}", disabled=not economy.can_afford(repair_c) or health_pct == 100):
                        if economy.can_afford(repair_c):
                            economy.deduct(repair_c)
                            at.train.locomotive.repair()
                            for w in at.train.wagons:
                                w.repair()
                            break
                    y_offset += 40
            elif menu_state["mode"] == "assign_train":
                ui.label((x_offset, y_offset), "Vyberte sestavenou soupravu pro spoj:", color=(255,255,255))
                y_offset += 40
                if not assembled_trains:
                    ui.label((x_offset, y_offset), "Žádné volné sestavené soupravy!", color=(255,100,100))
                for i, tr in enumerate(assembled_trains):

                    if ui.button((x_offset, y_offset, 600, 35), f"{tr['loco'].type.name} + {len(tr['wagons'])} vagonů"):
                        train_info = assembled_trains.pop(i)
                        new_train = TerminusEngine.Vehicles.Train("Vlak", train_info["loco"], train_info["wagons"])
                        world.add_active_train(TerminusEngine.World.ActiveTrain(new_train, menu_state["temp_route"]))
                        menu_state["mode"] = "closed"
                        menu_state["temp_route"] = None
                        break
                    y_offset += 45
                        
            game.screen.set_clip(old_clip)
            if menu_state["mode"] not in ["main", "inventory_main"]:
                content_height = (y_offset + menu_state["scroll_y"]) - start_y_offset
                menu_state["max_scroll"] = max(0, content_height - clip_rect.height)

    game.run(
        loop=loop,
        event_handler=event_handler
    )

if __name__ == "__main__":
    main()