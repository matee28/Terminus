import pygame
import math
import os
import numpy as np
import random
import sys

from shapely.geometry import LineString, Point

import TerminusEngine.Audio


# systém souřadnic enginu: +y je nahoru; +x je doprava

pygame.font.init()

# poměr metrů na pixely dle rozlišení textur/ortofot
METERS_TO_PIXELS = 8 # (1 metr = 8 pixelů)

# hranice zoomu pro vykreslování barvy <-> textury
FADE_TO_COLOR_ZOOM_THRESHOLD = 0.05
FADE_TO_COLOR_ZOOM_START = 0.15

# minimální šířka kolejí
RAILWAY_MIN_WIDTH_PX = 2

def m2px(value: float):
    """
    Převádí metry na pixely.

    Args:
        value (float): hodnota v metrech
    """
    return value * METERS_TO_PIXELS

def px2m(value: float):
    """
    Převádí pixely na metry.

    Args:
        value (float): hodnota v pixelech
    """
    return value / METERS_TO_PIXELS


def read_src(path):
    """
    Vrací obsah souboru (string) ve složce src/.
    """
    return open(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", path)), "r", encoding="utf-8").read()


class Camera:
    """
    Inicializuje a uchovává atributy kamery.
    """
    def __init__(
            self,
            position: tuple[float, float],
            max_distance: float,
            move_speed: float,
            zoom: float, max_zoom: float,
            min_zoom: float,
            zoom_speed: float
        ):

        """
        Inicializuje kameru.

        Args:
            position (tuple[float, float]): počáteční souřadnice kamery (x, y)
            max_distance (float): maximální vzdálenost kamery od středu světa (0, 0)
            move_speed (float): rychlost pohybu kamery
            zoom (float): počáteční přiblížení pohledu kamery
            max_zoom (float): maximální přiblížení pohledu kamery
            min_zoom (float): minimální přiblížení pohledu kamery
            zoom_speed (float): rychlost přiblížování pohledu kamery
        """
        self.position = position
        self.max_distance = max_distance
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
            d (tuple[float, float]): vzdálenost posunu kamery z myši v px na obrazovce (x, y)
        """
        dx, dy = d
        # dx, dy je v px -> převod na m
        new_position = (self.position[0] + px2m(dx)/self.zoom*self.move_speed, self.position[1] + px2m(dy)/self.zoom*self.move_speed)
        self.set_position(new_position)


    def set_position(self, position: tuple[float, float]):
        """
        Přesouvá kameru na zadané souřadnice.

        Args:
            position (tuple[float, float]): nové souřadnice kamery (x, y)
        """
        if position[0] > self.max_distance:
            position = (self.max_distance, position[1])
        elif position[0] < -self.max_distance:
            position = (-self.max_distance, position[1])

        if position[1] > self.max_distance:
            position = (position[0], self.max_distance)
        elif position[1] < -self.max_distance:
            position = (position[0], -self.max_distance)

        self.position = position


class Game:
    """
    Umožňuje inicializovat a spouštět hru.
    """
    # https://www.geeksforgeeks.org/python/pygame-tutorial/

    def __init__(self, camera: Camera, width: int, height: int, font_name: str = "Comic Sans MS"):
        """
        Inicializuje herní okno.

        Args:
            camera (Camera): kamera
            width (int): šířka okna
            height (int): výška okna
            font_name (str): název fontu
        """

        self.images = {}
        self.image_colors = {}
        self.texture_cache = {}
        self.max_texture_cache_size = 100  # limit pro počet cachovaných textur
        
        self.audio = TerminusEngine.Audio.AudioManager(self)

        self.path_cache = {}
        
        self.camera = camera
        self.font_name = font_name
        self.fonts = {}

        self.src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        # čas
        self.time_scale = 180 # 1 irl sekunda = 180 ingame sekund
        self.time = 0
        self.time_paused = False
        self.train_speed_multiplier = 0.5
        self.train_gap = 0.2
        self.passenger_generation_rate = 0.05 # rychlost zaplnění stanic cestujícími
        self.cargo_generation_rate = 0.05 # rychlost zaplnění stanic nákladem

        # pygame
        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("Terminus")

        icon = pygame.image.load(self.__abs_path("assets/icon.png"))
        pygame.display.set_icon(icon)

    def __abs_path(self, relative_path: str):
        """
        Vrací absolutní cestu k souboru.

        Args:
            relative_path (str): relativní cesta k souboru (relativně k src/)
        """
        return os.path.join(self.src_path, relative_path)
    
    def __round_tuple(self, tuple: tuple[float, float]):
        """
        Zaokrouhluje souřadnice na nejbližší celá čísla.

        Args:
            tuple (tuple[float, float]): tuple s dvěma float hodnotami
        """
        return (round(tuple[0]), round(tuple[1]))

    def run(self, loop: callable, event_handler: callable):
        """
        Spouští hlavní smyčku hry.

        Args:
            loop (callable): funkce hlavní smyčky hry
            event_handler (callable): funkce pro zpracování událostí, dostává jako argument objekt event
        """
        running = True
        while running:
            dt_seconds = self.clock.tick(60) / 1000.0
            
            if not self.time_paused:
                self.time += dt_seconds * self.time_scale

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    exit()
                elif event.type == pygame.VIDEORESIZE:
                    if event.w > 0 and event.h > 0:
                        self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                
                event_handler(event)

            self.audio.update()
            self.screen.fill((0, 0, 0))
            loop()
            pygame.display.flip()
            # self.clock.tick(60) # na zacatku loopu kvuli mereni casu

        pygame.quit()
        sys.exit()

    def get_time_string(self):
        """
        Vrací aktuální herní čas ve formátu 'Den X, HH:MM'.
        """
        total_minutes = int(self.time // 60)
        minutes = total_minutes % 60
        total_hours = total_minutes // 60
        hours = total_hours % 24
        days = (total_hours // 24) + 1
        return f"Den {days}, {hours:02d}:{minutes:02d}"

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
        Převádí světové souřadnice (v metrech) na souřadnice na obrazovce (v pixelech).

        Args:
            position (tuple[float, float]): světová souřadnice v metrech (x, y)
        """
        rel_position = self.relative_position(position)
        return (
            m2px(rel_position[0]) * self.camera.zoom + self.screen.get_width() / 2,
            -m2px(rel_position[1]) * self.camera.zoom + self.screen.get_height() / 2
        )
    
    def world_position(self, screen_position: tuple[float, float]):
        """
        Převádí souřadnice na obrazovce (v pixelech) na světové souřadnice (v metrech).

        Args:
            screen_position (tuple[float, float]): souřadnice na obrazovce (x, y)
        """
        rel_x = (screen_position[0] - self.screen.get_width() / 2) / (self.camera.zoom * METERS_TO_PIXELS)
        rel_y = (screen_position[1] - self.screen.get_height() / 2) / (self.camera.zoom * METERS_TO_PIXELS)
        return (
            rel_x + self.camera.position[0],
            -rel_y + self.camera.position[1]
        )

    def screen_distance(self, distance_m: float):
        """
        Převádí vzdálenost ve světě (v metrech) na vzdálenost na obrazovce (v pixelech) podle aktuálního přiblížení kamery.

        Args:
            value_m (float): vzdálenost ve světě v metrech
        """
        return m2px(distance_m) * self.camera.zoom
    
    def draw_debug_dot(self, world_position: tuple[float, float], size=10, text: str = ""):
        """
        Vykreslí debugovací bod s textem na zadané souřadnici.

        Args:
            world_position (tuple[float, float]): světové souřadnice v metrech (x, y)
            size (float; default: 10): velikost bodu v metrech
            text (str; default: ""): text, který se zobrazí u bodu
        """
        pos = self.screen_position(world_position)
        pygame.draw.circle(self.screen, (0, 255, 0), pos, m2px(size)*self.camera.zoom)
        pygame.draw.circle(self.screen, (255, 0, 0), pos, 2)
        if text != "":
            self.render_text(text, pos, color=(255, 255, 255), outline_color=(0, 0, 0), outline_width=1)

    def render_city(self, world_position: tuple[float, float], radius: float, text: str = ""):
        """
        Vykreslí město jako náhodný tvar s minimálním poloměrem.
        
        Args:
            world_position (tuple[float, float]): světové souřadnice (x, y)
            radius (float): minimální poloměr města v metrech
            text (str; default: ""): text, který se zobrazí u města
        """
        rng = random.Random(int(world_position[0] * 100 + world_position[1] * 10000)) # seed pro konzistentní generaci
        
        num_points = 12 # počet "vrcholů"
        points = []
        for i in range(num_points):
            angle = math.radians(i * (360 / num_points))
            point_radius = radius + rng.uniform(0, radius * 0.6)
            
            px = world_position[0] + math.cos(angle) * point_radius
            py = world_position[1] + math.sin(angle) * point_radius
            points.append(self.screen_position((px, py)))
            
        if len(points) >= 3:
            pygame.draw.polygon(self.screen, (50, 50, 50), points)
            
        if text != "":
            self.render_text(text, self.screen_position(world_position), color=(255, 255, 255), x_alignment="center", y_alignment="center", outline_color=(0, 0, 0), outline_width=1)

    def render_station(self, world_position: tuple[float, float]):
        """
        Vykreslí stanici jako malou modrou tečku.
        
        Args:
            world_position (tuple[float, float]): světové souřadnice (x, y)
        """
        pos = self.screen_position(world_position)
        pygame.draw.circle(self.screen, (0, 100, 255), pos, 2)

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
        self.image_colors[name] = pygame.transform.average_color(image)

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
            world_position (tuple[float, float]): světové souřadnice obrázku v metrech (x, y)
            size (tuple[float, float]; default: (0, 0)): velikost obrázku (výška, šířka) v metrech, pro původní velikost na ose použijte velikost 0
            rotation (float; default: 0): rotace obrázku ve stupních
            x_alignment (str; default: "center"): zarovnání v ose x (left, center, right)
            y_alignment (str; default: "center"): zarovnání v ose y (top, center, bottom)
            tiled (bool; default: False): zda se má obrázek vykreslit jako dlaždice
        """
        if texture_name in self.images:

            texture = self.images[texture_name]

            # originál je v px; tzn. pokud size 0 -> px2m originální velikosti
            size_m = (size[0], size[1])
            if size_m[0] == 0:
                size_m = (px2m(texture.get_size()[0]), size_m[1])
            if size_m[1] == 0:
                size_m = (size_m[0], px2m(texture.get_size()[1]))

            # převod na px s ohledem na zoom
            scaled_size = self.__round_tuple((m2px(size_m[0]) * self.camera.zoom, m2px(size_m[1]) * self.camera.zoom))

            if not tiled:
                pos = self.screen_position(world_position)
                margin = max(scaled_size)
                if pos[0] < -margin or pos[0] > self.screen.get_width() + margin or pos[1] < -margin or pos[1] > self.screen.get_height() + margin:
                    return

            # fade to color pokud je textura moc malá
            if tiled and self.camera.zoom <= FADE_TO_COLOR_ZOOM_THRESHOLD:
                avg_color = self.image_colors[texture_name]
                self.screen.fill(avg_color)
                return

            texture_cache_key = (texture_name, scaled_size, rotation)
            if texture_cache_key in self.texture_cache:
                texture = self.texture_cache[texture_cache_key]
            else:
                texture = pygame.transform.scale(texture, scaled_size)
                texture = self.rotate_image(texture, rotation)
                self.texture_cache[texture_cache_key] = texture
                
                if len(self.texture_cache) > self.max_texture_cache_size: # cache přesahuje max velikost
                    oldest_key = list(self.texture_cache.keys())[0]
                    del self.texture_cache[oldest_key]



            # počítání vectoru (shoutout gemini)

            offset_x, offset_y = 0, 0
            if x_alignment == "center":
                offset_x = -scaled_size[0]/2
            elif x_alignment == "left":
                offset_x = -scaled_size[0]
            # right nic

            if y_alignment == "center":
                offset_y = -scaled_size[1]/2
            elif y_alignment == "top":
                offset_y = -scaled_size[1]
            # bottom nic


            center_x, center_y = scaled_size[0]/2, scaled_size[1]/2
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

                if self.camera.zoom <= FADE_TO_COLOR_ZOOM_START:
                    if self.camera.zoom < FADE_TO_COLOR_ZOOM_START:
                        fade_range = FADE_TO_COLOR_ZOOM_START - FADE_TO_COLOR_ZOOM_THRESHOLD
                        opacity = 255 * (1.0 - (self.camera.zoom - FADE_TO_COLOR_ZOOM_THRESHOLD) / fade_range)
                        opacity = max(0, min(255, int(opacity)))
                        if opacity > 0:
                            fade_surface = pygame.Surface(self.screen.get_size())
                            fade_surface.fill(self.image_colors[texture_name])
                            fade_surface.set_alpha(opacity)
                            self.screen.blit(fade_surface, (0, 0))

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

    
    def __points_on_path(self, path: list[tuple[float, float]], distance_delta: float, smooth: bool = True):
        """
        Vypočítává body v zadané vzdálenosti na zadané cestě.

        Args:
            path (list[tuple[float, float]]): seznam světových souřadnic tvořících cestu
            distance_delta (float): vzdálenost mezi body
            smooth (bool; default: True): zda se má cesta vyhladit
        """
        # https://stackoverflow.com/questions/62990029/how-to-get-equally-spaced-points-on-a-line-in-shapely
        # https://stackoverflow.com/a/62994304 by Georgy (CC BY-SA 4.0)

        if smooth:
            path = self.__smooth_path(path)

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
    
    def get_point_on_path(self, path: list[tuple[float, float]], distance: float):
        """
        Vrátí přesnou souřadnici a úhel natočení pro zadanou vzdálenost na trati.

        Args:
            path (list[tuple[float, float]]): seznam bodů cesty
            distance (float): vzdálenost od začátku trati
            
        Returns:
            tuple[tuple[float, float], float]: (pozice (x, y), úhel (stupně))
        """
        if len(path) < 2:
            return path[0], 0, 0
        
        smoothed_path = self.__smooth_path(path)
        line = LineString(smoothed_path)
        
        # clamp vzdálenosti
        dist = max(0.0, min(distance, line.length))
        point = line.interpolate(dist)
        
        # výpočet heading úhlu
        if dist >= line.length - 1:
            point_behind = line.interpolate(max(0.0, dist - 1.0))
            heading = self.__get_angle(point_behind.coords[0], point.coords[0])
        else:
            point_ahead = line.interpolate(min(line.length, dist + 1.0))
            heading = self.__get_angle(point.coords[0], point_ahead.coords[0])
            
        return (point.x, point.y), heading, line.length
    

    def __smooth_path(self, path: list[tuple[float, float]], smoothing_iterations: int = 3):
        """
        Převádí zadanou cestu na hladší cestu pomocí Chaikinova algoritmu.

        Args:
            path (list[tuple[float, float]]): seznam světových souřadnic tvořících cestu
            distance_delta (float): vzdálenost mezi body
            smoothing_iterations (int; default 3): počet iterací pro vyhlazení rohů (čím vyšší, tím kulatější)
        """

        if len(path) <= 2: # nemá smysl
            return path
        
        # shoutout gemini
        # Chaikinův algoritmus funguje tak, že v každé iteraci "usekne" ostré rohy 
        # původní lomené čáry. Ze všech úseček vygeneruje nové body ve čtvrtině
        # a ve třech čtvrtinách jejich délky a původní rohy zahodí.
        smoothed_path = path
        for _ in range(smoothing_iterations):
            new_path = [smoothed_path[0]]
            for i in range(len(smoothed_path) - 1):
                p0 = smoothed_path[i]
                p1 = smoothed_path[i + 1]

                # Výpočet nových bodů (ve 25 % a 75 % délky aktuálního segmentu)
                pA = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
                pB = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])

                # Klasický algoritmus by smazal i původní první a poslední bod (cesta by se "smrskla").
                # Proto uměle první přidaný bod z prvního segmentu a poslední z posledního přeskočíme,
                # čímž se zbytek křivky natvrdo ukotví na absolutní začátek/konec trasy.
                if i != 0:
                    new_path.append(pA)
                if i != len(smoothed_path) - 2:
                    new_path.append(pB)

            new_path.append(smoothed_path[-1]) # Vždy bezpečně přidáme původní koncový bod
            smoothed_path = new_path

        return smoothed_path


    
    def render_image_path(self, texture_name: str, path: list[tuple[float, float]], distance: float, size: tuple[float, float] = (0, 0), rotation: float = 0, cache: bool = True):
        """
        Vykreslí obrázek uložený v paměti podél zadané cesty.

        Args:
            texture_name (str): název obrázku v slovníku
            path (list[tuple[float, float]]): seznam světových souřadnic tvořících cestu
            size (tuple[float, float]; default: (0, 0)): velikost obrázku (výška, šířka), pro původní velikost na ose použijte velikost 0
            rotation (float; default: 0): rotace obrázku ve stupních
            cache (bool; default: True): zda se má cesta uložit do/volat z paměti
        """
        if texture_name in self.images:

            # výpočet velikosti textury
            texture = self.images[texture_name]
            
            size_m = (size[0], size[1])
            if size_m[0] == 0:
                size_m = (px2m(texture.get_size()[0]), size_m[1])
            if size_m[1] == 0:
                size_m = (size_m[0], px2m(texture.get_size()[1]))

            scaled_size = self.__round_tuple((m2px(size_m[0]) * self.camera.zoom, m2px(size_m[1]) * self.camera.zoom))


            # fade to color pokud je textura moc malá
            if self.camera.zoom <= FADE_TO_COLOR_ZOOM_THRESHOLD:
                avg_color = self.image_colors.get(texture_name, (255, 0, 255))
                smoothed_path = self.__smooth_path(path)
                screen_points = [self.screen_position(p) for p in smoothed_path]
                if len(screen_points) >= 2:
                    thickness = max(RAILWAY_MIN_WIDTH_PX, int(scaled_size[1])) # tloušťka čáry = tloušťka textury
                    pygame.draw.lines(self.screen, avg_color, False, screen_points, thickness)
                return


            path_key = (tuple(path), distance)
            if cache and path_key in self.path_cache:
                points = self.path_cache[path_key]
            else:
                points = self.__points_on_path(path, distance, smooth=True)
                if cache:
                    self.path_cache[path_key] = points

            # for position, _ in points:
            #     for deg in range(0, 360, 30):
            #         self.render_image(texture_name, position, size, deg, x_alignment="right", y_alignment="center", tiled=False)
            for position, heading in points:
                self.render_image(texture_name, position, size, rotation + heading, x_alignment="right", y_alignment="center", tiled=False)
            # for position, _ in points:
                # self.draw_debug_dot(position, 2)


    def get_font(self, size: int):
        """
        Vrátí font dané velikosti z paměti, nebo ho inicializuje.

        Args:
            size (int): velikost fontu
        """
        if size not in self.fonts:
            self.fonts[size] = pygame.font.SysFont(self.font_name, size)
        return self.fonts[size]

    def render_text(self, text: str, position: tuple[float, float], color: tuple[int, int, int] = (255, 255, 255), is_world_position: bool = False, x_alignment: str = "left", y_alignment: str = "top", antialias: bool = True, font_size: int = 20, outline_color: tuple[int, int, int] = None, outline_width: int = 1):
        """
        Vykreslí text na obrazovku.

        Args:
            text (str): text k vykreslení
            position (tuple[float, float]): souřadnice (x, y) na obrazovce nebo ve světě
            color (tuple[int, int, int]; default: (255, 255, 255)): barva textu
            is_world_position (bool; default: False): zda je pozice ve světových souřadnicích
            x_alignment (str; default: "left"): zarovnání na ose X (left, center, right)
            y_alignment (str; default: "top"): zarovnání na ose Y (top, center, bottom)
            antialias (bool; default: True): zda se má použít antialiasing
            font_size (int; default: 20): velikost textu
            outline_color (tuple[int, int, int]; default: None): barva obrysu textu (None = obrys se nevykreslí)
            outline_width (int; default: 1): šířka obrysu v pixelech
        """
        
        font = self.get_font(font_size)
        
        if is_world_position:
            pos = self.screen_position(position)
        else:
            pos = position

        def get_rect_for_pos(surf, px, py):
            rect = surf.get_rect()
            if x_alignment == "left":
                rect.left = px
            elif x_alignment == "center":
                rect.centerx = px
            elif x_alignment == "right":
                rect.right = px
                
            if y_alignment == "top":
                rect.top = py
            elif y_alignment == "center":
                rect.centery = py
            elif y_alignment == "bottom":
                rect.bottom = py
            return rect

        # outline
        if outline_color is not None:
            outline_surface = font.render(text, antialias, outline_color)
            for dx in [-outline_width, 0, outline_width]:
                for dy in [-outline_width, 0, outline_width]:
                    if dx == 0 and dy == 0:
                        continue
                    self.screen.blit(outline_surface, get_rect_for_pos(outline_surface, pos[0] + dx, pos[1] + dy))

        # samotný text
        text_surface = font.render(text, antialias, color)
        self.screen.blit(text_surface, get_rect_for_pos(text_surface, pos[0], pos[1]))