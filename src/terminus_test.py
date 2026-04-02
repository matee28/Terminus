import pygame
import TerminusEngine
import TerminusEngine.World
import os


def main():

    pygame.font.init()
    font = pygame.font.SysFont("Comic Sans MS", 20)


    camera = TerminusEngine.Camera(
        position=(0, 0),
        move_speed=1.0,
        zoom=1.0,
        max_zoom=2.5,
        min_zoom=0.1,
        zoom_speed=1.5
    )

    game = TerminusEngine.Game(
        camera=camera,
        width=800,
        height=600
    )


    game.load_image("terrain", "assets/terrain/rocky_terrain_02_diff_1k.png")
    game.load_image("rail_tile", "assets/rails/rail_tile_1_small.png", rotation=90)


    world = TerminusEngine.World.WorldGenerator(
        world_boundary=10000,
        city_names=TerminusEngine.read_src("assets/names/CITIES").splitlines(),
        cities=10,
        small_city_max_population=5000,
        large_city_max_population=500000,
        max_city_boundary=1000,
        max_stations_per_city=3,
        passenger_station_names=TerminusEngine.read_src("assets/names/STATIONS_PASSENGER").splitlines(),
        cargo_station_names=TerminusEngine.read_src("assets/names/STATIONS_CARGO").splitlines()
    )

    print(world)


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


    def loop():
        game.render_image(
            texture_name="terrain",
            world_position=(0, 0),
            size=(200, 200),
            tiled=True
        )

        game.render_image_path(
            texture_name="rail_tile",
            distance=10,
            path=[(0, 0), (-100, 100), (-200, 330), (-300, 1000)]
        )

        game.draw_debug_dot((0, 0))
        game.screen.blit(font.render("pos: " + str(camera.position), False, (255, 0, 0)), (0, 0))
        game.screen.blit(font.render("zoom: " + str(camera.zoom), False, (255, 0, 0)), (0, 20))
        game.screen.blit(font.render("mouse pos: " + str(game.world_position(pygame.mouse.get_pos())), False, (255, 0, 0)), (0, 40))

        game.draw_debug_dot(game.world_position(pygame.mouse.get_pos()))
        game.draw_debug_dot(game.world_position((pygame.display.get_surface().get_width()/2, pygame.display.get_surface().get_height()/2)), 5)


    game.run(
        loop=loop,
        event_handler=event_handler
    )

if __name__ == "__main__":
    main()