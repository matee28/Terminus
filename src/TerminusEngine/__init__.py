import pygame
import math
import os
import numpy as np

from shapely.geometry import LineString, Point


# systém souřadnic enginu: +y je nahoru; +x je doprava


class Camera:
    """
    Inicializuje a uchovává atributy kamery.
    """
    def __init__(self, position: tuple[float, float], move_speed: float, zoom: float, max_zoom: float, min_zoom: float, zoom_speed: float):
        """
        Inicializuje kameru.

        Args:
            position (tuple[float, float]): počáteční souřadnice kamery (x, y)
            move_speed (float): rychlost pohybu kamery
            zoom (float): počáteční přiblížení pohledu kamery
            max_zoom (float): maximální přiblížení pohledu kamery
            min_zoom (float): minimální přiblížení pohledu kamery
            zoom_speed (float): rychlost přiblížování pohledu kamery
        """
        self.position = position
        self.move_speed = move_speed
        self.zoom = zoom
        self.max_zoom = max_zoom
        self.min_zoom = min_zoom
        self.zoom_speed = zoom_speed

    def __validate_zoom(self):
        """
        Ponechává přiblížení pohledu kamery v rozmezí mezi minimálním a maximálním přiblížením.

        Returns:
            bool: zda bylo přiblížení upraveno
        """
        if self.zoom > self.max_zoom:
            self.zoom = self.max_zoom
            return False
        elif self.zoom < self.min_zoom:
            self.zoom = self.min_zoom
            return False
        return True

    def set_zoom(self, zoom: float):
        """
        Nastavuje přiblížení pohledu kamery.

        Args:
            zoom (float): nové přiblížení pohledu kamery

        Returns:
            bool: zda bylo přiblížení upraveno
        """
        self.zoom = zoom
        return self.__validate_zoom()

    def zoom_in(self):
        """
        Přibližuje pohled kamery.

        Returns:
            bool: zda bylo přiblížení upraveno
        """
        self.zoom *= self.zoom_speed
        return self.__validate_zoom()

    def zoom_out(self):
        """
        Oddaluje pohled kamery.

        Returns:
            bool: zda bylo přiblížení upraveno
        """
        self.zoom /= self.zoom_speed
        return self.__validate_zoom()

    def move(self, d: tuple[float, float]):
        """
        Posouvá kameru.

        Args:
            d (tuple[float, float]): vzdálenost posunu kamery (x, y)
        """
        dx, dy = d
        self.position = (self.position[0] + dx/self.zoom*self.move_speed, self.position[1] + dy/self.zoom*self.move_speed)

    def set_position(self, position: tuple[float, float]):
        """
        Přesouvá kameru na zadané souřadnice.

        Args:
            position (tuple[float, float]): nové souřadnice kamery (x, y)
        """
        self.position = position


class Game:
    """
    Umožňuje inicializovat a spouštět hru.
    """
    # https://www.geeksforgeeks.org/python/pygame-tutorial/

    def __init__(self, camera: Camera, width: int, height: int):
        """
        Inicializuje herní okno.

        Args:
            camera (Camera): kamera
            width (int): šířka okna
            height (int): výška okna
        """

        self.images = {}
        self.texture_cache = {}
        self.max_texture_cache_size = 100  # limit pro počet cachovaných textur
        self.camera = camera

        self.src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        # pygame
        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("TerminusEngine")

    def __abs_path(self, relative_path: str):
        """
        Vrací absolutní cestu k souboru.

        Args:
            relative_path (str): relativní cesta k souboru (relativně k src/)
        """
        return os.path.join(self.src_path, relative_path)
    
    def __floor_tuple(self, tuple: tuple[float, float]):
        """
        Zaokrouhluje souřadnice na celá čísla.

        Args:
            tuple (tuple[float, float]): tuple s dvěma float hodnotami
        """
        return (math.floor(tuple[0]), math.floor(tuple[1]))

    def run(self, loop: callable, event_handler: callable):
        """
        Spouští hlavní smyčku hry.

        Args:
            loop (callable): funkce hlavní smyčky hry
            event_handler (callable): funkce pro zpracování událostí, dostává jako argument objekt event
        """
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    exit()
                
                event_handler(event)

            self.screen.fill((0, 0, 0))
            loop()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def relative_position(self, position: tuple[float, float]):
        """
        Převádí světové souřadnice na relativní souřadnice.

        Args:
            position (tuple[float, float]): světová souřadnice (x, y)
        """
        return (
            position[0] - self.camera.position[0],
            position[1] - self.camera.position[1]
        )

    def screen_position(self, position: tuple[float, float]):
        """
        Převádí světové souřadnice na souřadnice na obrazovce.

        Args:
            position (tuple[float, float]): světová souřadnice (x, y)
        """
        rel_position = self.relative_position(position)
        return (
            rel_position[0] * self.camera.zoom + self.screen.get_width()/2,
            -rel_position[1] * self.camera.zoom + self.screen.get_height()/2
        )
    
    def world_position(self, screen_position: tuple[float, float]):
        """
        Převádí souřadnice na obrazovce na světové souřadnice.

        Args:
            screen_position (tuple[float, float]): souřadnice na obrazovce (x, y)
        """
        rel_x = (screen_position[0] - self.screen.get_width() / 2) / self.camera.zoom
        rel_y = (screen_position[1] - self.screen.get_height() / 2) / self.camera.zoom
        return (
            rel_x + self.camera.position[0],
            -rel_y + self.camera.position[1]
        )

    # def calculate_alignment(self, position: tuple[float, float], size: tuple[float, float], x_alignment: str, y_alignment: str, y_axis_offset_rotation: float = 0):
    #     """
    #     Vypočítává souřadnice pro zadané zarovnání.

    #     Args:
    #         position (tuple[float, float]): souřadnice (x, y)
    #         size (tuple[float, float]): velikost objektu (výška, šířka)
    #         x_alignment (str): zarovnání v ose x ("left", "center", "right")
    #         y_alignment (str): zarovnání v ose y ("top", "center", "bottom")
    #         y_axis_offset_rotation (float; default: 0): offset rotace osy y ve stupních (např. při zarovnání již rotovaných obrázků; tzn. alignment možnosti jsou relativně k obrázku, ne k světu)
    #     """
    #     x_alignment = x_alignment.lower().strip()
    #     y_alignment = y_alignment.lower().strip()

    #     position_x, position_y = position
    #     size_x, size_y = size
    #     offset_x, offset_y = 0, 0

    #     if x_alignment == "center":
    #         offset_x = -size_x/2
    #     elif x_alignment == "left":
    #         offset_x = -size_x
    #     # right nic
        
    #     if y_alignment == "center":
    #         offset_y = -size_y/2
    #     elif y_alignment == "top":
    #         offset_y = -size_y
    #     # bottom nic

    #     if y_axis_offset_rotation != 0: # rotace offsetu
    #         cos_angle = math.cos(math.radians(y_axis_offset_rotation))
    #         sin_angle = math.sin(math.radians(y_axis_offset_rotation))

    #         rotated_offset_x = offset_x * cos_angle - offset_y * sin_angle
    #         rotated_offset_y = offset_x * sin_angle + offset_y * cos_angle

    #         offset_x, offset_y = rotated_offset_x, rotated_offset_y

    #     position_x += offset_x
    #     position_y += offset_y

    #     return (position_x, position_y)
    
    def draw_debug_dot(self, world_position: tuple[float, float], size=10):
        """
        Vykreslí debugovací bod na zadané souřadnici.

        Args:
            world_position (tuple[float, float]): světové souřadnice (x, y)
            size (int; default: 10): velikost bodu
        """
        pygame.draw.circle(self.screen, (0, 255, 0), self.screen_position(world_position), size*self.camera.zoom)
        pygame.draw.circle(self.screen, (255, 0, 0), self.screen_position(world_position), 2)

    def load_image(self, name: str, path: str, rotation: float = 0):
        """
        Načítá obrázek a ukládá ho do paměti.

        Args:
            name (str): název obrázku v paměti
            path (str): cesta k souboru (relativně k src/)
            rotation (float): rotace obrázku ve stupních
        """
        image = pygame.image.load(self.__abs_path(path)).convert_alpha()
        image = self.rotate_image(image, rotation)
        self.images[name] = image

    def rotate_image(self, image: pygame.Surface, rotation: float):
        """
        Rotuje obrázek.

        Args:
            image (pygame.Surface): obrázek
            rotation (float): rotace obrázku ve stupních
        """
        if rotation != 0:
            image = pygame.transform.rotate(image, rotation)
        return image

    def render_image(self, texture_name: str, world_position: tuple[float, float], size: tuple[float, float] = (0, 0), rotation: float = 0, x_alignment: str = "center", y_alignment: str = "center", tiled: bool = False):
        """
        Vykreslí obrázek uložený v paměti.

        Args:
            texture_name (str): název obrázku v slovníku
            world_position (tuple[float, float]): světové souřadnice obrázku (x, y)
            size (tuple[float, float]; default: (0, 0)): velikost obrázku (výška, šířka), pro původní velikost na ose použijte velikost 0
            rotation (float; default: 0): rotace obrázku ve stupních
            x_alignment (str; default: "center"): zarovnání v ose x (viz funkce calculate_alignment)
            y_alignment (str; default: "center"): zarovnání v ose y (viz funkce calculate_alignment)
            tiled (bool; default: False): zda se má obrázek vykreslit jako dlaždice
        """
        if texture_name in self.images:

            texture = self.images[texture_name]

            if size[0] == 0:
                size = (texture.get_size()[0], size[1])
            if size[1] == 0:
                size = (size[0], texture.get_size()[1])

            size = self.__floor_tuple((size[0] * self.camera.zoom, size[1] * self.camera.zoom))

            texture_cache_key = (texture_name, size, rotation)
            if texture_cache_key in self.texture_cache:
                texture = self.texture_cache[texture_cache_key]
            else:
                texture = pygame.transform.scale(texture, size)
                texture = self.rotate_image(texture, rotation)
                self.texture_cache[texture_cache_key] = texture
                
                if len(self.texture_cache) > self.max_texture_cache_size: # cache přesahuje max velikost
                    oldest_key = list(self.texture_cache.keys())[0]
                    del self.texture_cache[oldest_key]



            # počítání vectoru (shoutout gemini)

            offset_x, offset_y = 0, 0
            if x_alignment == "center":
                offset_x = -size[0]/2
            elif x_alignment == "left":
                offset_x = -size[0]
            # right nic

            if y_alignment == "center":
                offset_y = -size[1]/2
            elif y_alignment == "top":
                offset_y = -size[1]
            # bottom nic


            center_x, center_y = size[0]/2, size[1]/2
            pivot_x, pivot_y = -offset_x, -offset_y
            vec = pygame.math.Vector2(pivot_x - center_x, pivot_y - center_y)

            rotated_vec = vec
            if rotation != 0:
                rotated_vec = vec.rotate(-rotation)

            pos = self.screen_position(world_position)
            final_center_x = pos[0] - rotated_vec.x
            final_center_y = pos[1] - rotated_vec.y
            
            rect = texture.get_rect(center=(final_center_x, final_center_y))

            if (not tiled) and (rect.right >= 0 and rect.left < self.screen.get_width() and rect.bottom >= 0 and rect.top < self.screen.get_height()):
                self.screen.blit(texture, rect.topleft)

            elif tiled:
                position_x, position_y = rect.topleft
                size_x, size_y = texture.get_size()
                
                offset_x = position_x % size_x
                offset_y = position_y % size_y
                for y in range(0-size_y, self.screen.get_height(), size_y):
                    for x in range(0-size_x, self.screen.get_width(), size_x):
                        self.screen.blit(texture, (x + offset_x, y + offset_y)) 

    def __get_angle(self, pos1: tuple[float, float], pos2: tuple[float, float]):
        """
        Vypočítává úhel mezi dvěma body.

        Args:
            pos1 (tuple[float, float]): souřadnice prvního bodu (x, y)
            pos2 (tuple[float, float]): souřadnice druhého bodu (x, y)
        """
        # https://stackoverflow.com/a/72602196 by Boris Kaptsanov (CC BY-SA 4.0)
        x1, y1 = pos1
        x2, y2 = pos2
        return math.degrees(math.atan2(y2-y1, x2-x1))

    
    def __points_on_path(self, path: list[tuple[float, float]], distance_delta: float):
        """
        Vypočítává body v zadané vzdálenosti na zadané cestě.

        Args:
            path (list[tuple[float, float]]): seznam světových souřadnic tvořících cestu
            distance_delta (float): vzdálenost mezi body
        """
        # https://stackoverflow.com/questions/62990029/how-to-get-equally-spaced-points-on-a-line-in-shapely
        # https://stackoverflow.com/a/62994304 by Georgy (CC BY-SA 4.0)

        if len(path) < 2:
            return path

        line = LineString(path)

        distances = np.arange(0, line.length, distance_delta)
        points = [line.interpolate(distance) for distance in distances]

        original_end_point = Point(line.coords[-1])
        if not points or points[-1] != original_end_point: # zahrnutí posledního bodu
            points.append(original_end_point)

        ret = []
        for i, point in enumerate(points):
            if i < len(points) - 1:
                heading = self.__get_angle(point.coords[0], points[i+1].coords[0])
            else:
                heading = self.__get_angle(points[i-1].coords[0], point.coords[0])
            ret.append([(point.x, point.y), heading])
        
        return ret


    
    def render_image_path(self, texture_name: str, path: list[tuple[float, float]], distance: float, size: tuple[float, float] = (0, 0), rotation: float = 0):
        """
        Vykreslí obrázek uložený v paměti podél zadané cesty.

        Args:
            texture_name (str): název obrázku v slovníku
            path (list[tuple[float, float]]): seznam světových souřadnic tvořících cestu
            size (tuple[float, float]; default: (0, 0)): velikost obrázku (výška, šířka), pro původní velikost na ose použijte velikost 0
            rotation (float; default: 0): rotace obrázku ve stupních
        """
        if texture_name in self.images:
            points = self.__points_on_path(path, distance)
            # for position, _ in points:
            #     for deg in range(0, 360, 30):
            #         self.render_image(texture_name, position, size, deg, x_alignment="right", y_alignment="center", tiled=False)
            for position, heading in points:
                self.render_image(texture_name, position, size, rotation + heading, x_alignment="right", y_alignment="center", tiled=False)
            # for position, _ in points:
                # self.draw_debug_dot(position, 2)