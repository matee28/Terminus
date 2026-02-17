import pygame
import TerminusEngine
from TerminusEngine import World

pygame.font.init()
font = pygame.font.SysFont("Comic Sans MS", 30)

camera = TerminusEngine.Camera(
    position=(0, 0),
    move_speed=1.0,
    zoom=1.0,
    max_zoom=10.0,
    min_zoom=0.1,
    zoom_speed=1.5
)

game = TerminusEngine.Game(
    camera=camera,
    width=800,
    height=600
)


game.load_image("terrain", "src/assets/terrain/rocky_terrain_02_diff_1k.png")


def event_handler(event: pygame.event.Event):
    if event.type == pygame.MOUSEWHEEL:
        if event.y > 0:
            camera.zoom_in()
        else:
            camera.zoom_out()

    if event.type == pygame.MOUSEMOTION:
        if event.buttons[0]:
            camera.move((-event.rel[0], -event.rel[1]))


def loop():
    game.render_image(
        texture_name="terrain",
        absolute_position=(0, 0),
        size=(200, 200),
        tiled=True
    )
    game.draw_debug_dot((0, 0))
    game.screen.blit(font.render("pos: " + str(camera.position), False, (255, 0, 0)), (0, 0))
    game.screen.blit(font.render("zoom: " + str(camera.zoom), False, (255, 0, 0)), (0, 30))


game.run(
    loop=loop,
    event_handler=event_handler
)