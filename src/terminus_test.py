import pygame

import TerminusEngine
import TerminusEngine.World
import TerminusEngine.Economy
import TerminusEngine.Vehicles


import os
import math


RAILWAY_MODE = False
RAILWAY_MODE_SNAP_DIST_PX = 20

INITIAL_BALANCE = 1000000

RAILWAY_COST_PER_METER = 10

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

    economy = TerminusEngine.Economy.Economy(initial_balance=INITIAL_BALANCE)


    game.load_image("terrain", "assets/terrain/rocky_terrain_02_diff_1k.png")
    game.load_image("rail_tile", "assets/rails/rail_tile_1.png", rotation=90)
    game.load_image("ce_head", "assets/trains/ce/head.png", rotation=-90)
    game.load_image("ce_middle", "assets/trains/ce/middle.png", rotation=-90)

    # City Elephant
    ce_loco = TerminusEngine.Vehicles.Locomotive("CityElephant (lokomotiva)", max_speed=140.0, power=2000.0, texture_name="ce_head", passenger_capacity=310)
    ce_wagons = [TerminusEngine.Vehicles.PassengerWagon("CityElephant (vložený vůz)", passenger_capacity=310, texture_name="ce_middle") for _ in range(2)]
    ce_train = TerminusEngine.Vehicles.Train("CityElephant", ce_loco, ce_wagons)


    def event_handler(event: pygame.event.Event):

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

        # stisk klávesy
        if event.type == pygame.KEYDOWN:

            # RAILWAY_MODE toggle = T
            if event.key == pygame.K_t:
                global RAILWAY_MODE
                RAILWAY_MODE = not RAILWAY_MODE
                if RAILWAY_MODE:
                    world.add_railway(TerminusEngine.World.Railway(None, None, []))
                else:
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

            # pozastavení času = P
            if event.key == pygame.K_p:
                game.time_paused = not game.time_paused



        # přidávání kolejí
        if RAILWAY_MODE:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3: # pravé tlačítko
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
                                
                                world.add_active_train(TerminusEngine.World.ActiveTrain(ce_train, world.railways[-1])) # nasazení vlaku
                                
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
            size=(200, 200),
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
            if len(at.railway.points) < 2: continue
            
            all_parts = [at.train.locomotive] + at.train.wagons # zkombinování částí
            current_offset = 0.0
            prev_len = 0.0
            
            for i, part in enumerate(all_parts):
                part_len = TerminusEngine.px2m(game.images[part.texture_name].get_width())
                
                if i > 0:
                    current_offset += (prev_len / 2) + (part_len / 2) + game.train_gap
                prev_len = part_len
                
                part_dist = at.distance - (current_offset * at.direction)
                pos, heading, total_len = game.get_point_on_path(at.railway.points, part_dist)
                
                render_heading = heading + (180 if at.direction == -1 else 0)
                game.render_image(part.texture_name, pos, size=(0,0), rotation=render_heading)
                
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
        game.render_text("r mode: " + str(RAILWAY_MODE), (0, 60), color=(255, 0, 0))
        game.render_text("balance: $" + str(int(economy.balance)), (0, 80), color=(255, 0, 0))

        if RAILWAY_MODE and len(world.railways) > 0 and len(world.railways[-1].points) > 1:
            pts = world.railways[-1].points
            
            for point in pts[:-1]:
                game.draw_debug_dot(point, 3)

            current_cost = sum(math.dist(pts[i-1], pts[i]) for i in range(1, len(pts))) * RAILWAY_COST_PER_METER
            mouse_pos = pygame.mouse.get_pos()
            color = (0, 255, 0) if economy.can_afford(current_cost) else (255, 0, 0)
            game.render_text("$" + str(int(current_cost)), (mouse_pos[0] + 15, mouse_pos[1] + 15), color=color)

        time_str = game.get_time_string()
        if game.time_paused:
            time_str += " (pozastaveno)"
        
        screen_w = game.screen.get_width()
        screen_h = game.screen.get_height()
        game.render_text(time_str, (screen_w - 10, screen_h - 10), color=(255, 255, 255), x_alignment="right", y_alignment="bottom", font_size=24)

    game.run(
        loop=loop,
        event_handler=event_handler
    )

if __name__ == "__main__":
    main()