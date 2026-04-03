import pygame
import TerminusEngine
import TerminusEngine.World
import os

# TODO: integrovat tratě do World + optimalizovat NĚJAK vykreslování a výpočet bodů


RAILWAY_MODE = False
RAILWAYS = []


def main():

    world_boundary = 1000

    world = TerminusEngine.World.WorldGenerator(
        world_boundary=world_boundary,
        city_names=TerminusEngine.read_src("assets/names/CITIES").splitlines(),
        cities=10,
        small_city_max_population=5000,
        large_city_max_population=500000,
        max_city_boundary=100,
        max_stations_per_city=3,
        passenger_station_names=TerminusEngine.read_src("assets/names/STATIONS_PASSENGER").splitlines(),
        cargo_station_names=TerminusEngine.read_src("assets/names/STATIONS_CARGO").splitlines()
    )

    print(world)


    pygame.font.init()
    font = pygame.font.SysFont("Comic Sans MS", 20)


    camera = TerminusEngine.Camera(
        position=(0, 0),
        max_distance=world_boundary,
        move_speed=1.0,
        zoom=1.0,
        max_zoom=2.5,
        min_zoom=0.01,
        zoom_speed=1.5
    )

    game = TerminusEngine.Game(
        camera=camera,
        width=800,
        height=600
    )


    game.load_image("terrain", "assets/terrain/rocky_terrain_02_diff_1k.png")
    game.load_image("rail_tile", "assets/rails/rail_tile_1_small.png", rotation=90)


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
                    RAILWAYS.append([])


        # přidávání kolejí
        if RAILWAY_MODE:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3: # pravé tlačítko
                    RAILWAYS[-1].append(game.world_position(event.pos))
                    print(RAILWAYS)


    def loop():
        game.render_image(
            texture_name="terrain",
            world_position=(0, 0),
            size=(200, 200),
            tiled=True
        )

        for railway in RAILWAYS:
            if len(railway) > 1:
                game.render_image_path(
                    texture_name="rail_tile",
                    distance=11/8, # velikost textury / METERS_TO_PIXELS
                    path=railway
                )
            elif len(railway) == 1:
                game.draw_debug_dot(railway[0], 5)

        game.draw_debug_dot((0, 0))
        game.screen.blit(font.render("pos: " + str(camera.position), False, (255, 0, 0)), (0, 0))
        game.screen.blit(font.render("zoom: " + str(camera.zoom), False, (255, 0, 0)), (0, 20))
        game.screen.blit(font.render("mouse pos: " + str(game.world_position(pygame.mouse.get_pos())), False, (255, 0, 0)), (0, 40))
        game.screen.blit(font.render("r mode: " + str(RAILWAY_MODE), False, (255, 0, 0)), (0, 60))

        game.draw_debug_dot(game.world_position(pygame.mouse.get_pos()))
        game.draw_debug_dot(game.world_position((pygame.display.get_surface().get_width()/2, pygame.display.get_surface().get_height()/2)), 5)

        for city in world.cities:
            game.draw_debug_dot(city.position, size=100, text=city.name)
            for station in city.stations:
                game.draw_debug_dot(station.position, size=0, text=station.name)


    game.run(
        loop=loop,
        event_handler=event_handler
    )

if __name__ == "__main__":
    main()