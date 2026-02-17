import pygame
import math

# systém souřadnic enginu: +y je nahoru; +x je doprava

class Camera:
    """
    Inicializuje a uchovává atributy kamery.
    """
    def __init__(self, position: tuple[float, float], move_speed: float, zoom: float, max_zoom: float, min_zoom: float, zoom_speed: float):
        """
        Inicializuje kameru.

        Args:
            position (tuple[float, float]): počáteční pozice kamery (x, y)
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
        """
        if self.zoom > self.max_zoom:
            self.zoom = self.max_zoom
        elif self.zoom < self.min_zoom:
            self.zoom = self.min_zoom

    def set_zoom(self, zoom: float):
        """
        Nastavuje přiblížení pohledu kamery.

        Args:
            zoom (float): nové přiblížení pohledu kamery
        """
        self.zoom = zoom
        self.__validate_zoom()

    def zoom_in(self):
        """
        Přibližuje pohled kamery.
        """
        self.zoom *= self.zoom_speed
        self.__validate_zoom()

    def zoom_out(self):
        """
        Oddaluje pohled kamery.
        """
        self.zoom /= self.zoom_speed
        self.__validate_zoom()

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
        Přesouvá kameru na zadanou pozici.

        Args:
            position (tuple[float, float]): nová pozice kamery (x, y)
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
        self.camera = camera

        # pygame
        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("TerminusEngine")
    
    def __floor_tuple(self, tuple: tuple[float, float]):
        """
        Zaokrouhluje pozici na celá čísla.

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
        Převádí absolutní souřadnice na relativní souřadnice.

        Args:
            position (tuple[float, float]): absolutní souřadnice (x, y)
        """
        return (
            position[0] - self.camera.position[0],
            position[1] - self.camera.position[1] # +, protože pygame má obráceně osu y
        )

    def screen_position(self, position: tuple[float, float]):
        """
        Převádí absolutní souřadnice na souřadnice na obrazovce.

        Args:
            position (tuple[float, float]): absolutní souřadnice (x, y)
        """
        rel_position = self.relative_position(position)
        return (
            rel_position[0] * self.camera.zoom + self.screen.get_width()/2,
            rel_position[1] * self.camera.zoom + self.screen.get_height()/2
        )

    def calculate_alignment(self, position: tuple[float, float], size: tuple[float, float], x_alignment: str, y_alignment: str):
        """
        Vypočítává pozici pro zadané zarovnání.

        Args:
            position (tuple[float, float]): souřadnice (x, y)
            size (tuple[float, float]): velikost objektu (výška, šířka)
            x_alignment (str): zarovnání v ose x ("left", "center", "right")
            y_alignment (str): zarovnání v ose y ("top", "center", "bottom")
        """
        x_alignment = x_alignment.lower().strip()
        y_alignment = y_alignment.lower().strip()

        position_x, position_y = position
        size_x, size_y = size

        if x_alignment == "center":
            position_x = position_x - size_x/2
        elif x_alignment == "right":
            position_x = position_x - size_x
        # left nic
        
        if y_alignment == "center":
            position_y = position_y - size_y/2
        elif y_alignment == "bottom":
            position_y = position_y - size_y
        # top nic

        return (position_x, position_y)

    def load_image(self, name: str, path: str):
        """
        Načítá obrázek a ukládá ho do paměti.

        Args:
            name (str): název obrázku v paměti
            path (str): cesta k souboru
        """
        image = pygame.image.load(path)
        self.images[name] = image

    def draw_debug_dot(self, absolute_position: tuple[float, float], size=10):
        """
        Vykreslí debugovací bod na zadané pozici.

        Args:
            absolute_position (tuple[float, float]): absolutní pozice bodu (x, y)
            size (int; default: 10): velikost bodu
        """
        pygame.draw.circle(self.screen, (0, 255, 0), self.screen_position(absolute_position), size*self.camera.zoom)
        pygame.draw.circle(self.screen, (255, 0, 0), self.screen_position(absolute_position), 2)

    def render_image(self, texture_name: str, absolute_position: tuple[float, float], size: tuple[float, float], rotation: float = 0, x_alignment: str = "center", y_alignment: str = "center", tiled: bool = False):
        """
        Vykreslí obrázek uložený v paměti.

        Args:
            texture_name (str): název obrázku v slovníku
            absolute_position (tuple[float, float]): absolutní pozice obrázku (x, y)
            size (tuple[float, float]): velikost obrázku (výška, šířka)
            rotation (float; default: 0): rotace obrázku ve stupních
            x_alignment (str; default: "center"): zarovnání v ose x (viz funkce calculate_alignment)
            y_alignment (str; default: "center"): zarovnání v ose y (viz funkce calculate_alignment)
            tiled (bool; default: False): zda se má obrázek vykreslit jako dlaždice
        """
        if texture_name in self.images:

            texture = self.images[texture_name]

            size = self.__floor_tuple((size[0] * self.camera.zoom, size[1] * self.camera.zoom))

            texture = pygame.transform.scale(texture, size)

            if rotation != 0:
                texture = pygame.transform.rotate(texture, rotation)

            position = self.__floor_tuple(self.screen_position(absolute_position))

            position = self.calculate_alignment(position, size, x_alignment, y_alignment)

            position_x, position_y = position
            size_x, size_y = size    

            if (not tiled) and (position_x + size_x >= 0) and (position_x < self.screen.get_width()) and (position_y + size_y >= 0) and (position_y < self.screen.get_height()):
                self.screen.blit(texture, (position_x, position_y))

            elif tiled:
                offset_x = position_x % size_x
                offset_y = position_y % size_y
                for y in range(0-size_y, self.screen.get_height(), size_y):
                    for x in range(0-size_x, self.screen.get_width(), size_x):
                        self.screen.blit(texture, (x + offset_x, y + offset_y))