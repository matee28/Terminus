import pygame
import math
import os
from dataclasses import dataclass
from typing import Callable, Optional, Any

@dataclass
class AudioSource:
    """
    Reprezentuje aktivní zdroj zvuku.
    """
    channel: pygame.mixer.Channel
    sound_name: str
    get_position: Callable[[], Optional[tuple[float, float]]]
    base_volume: float
    panning: bool
    max_distance: float
    loop: bool
    get_volume_multiplier: Callable[[], float]

class AudioManager:
    def __init__(self, game):
        """
        Inicializuje správce zvuku.

        Args:
            game (Game): instance hry
        """
        self.game = game
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)
        self.sounds = {}
        self.active_sources = []

    def load_sound(self, name: str, path: str):
        """
        Načte zvukový soubor do paměti a uloží ho pod zadaným jménem.

        Args:
            name (str): název zvuku
            path (str): relativní cesta ke zvukovému souboru
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_dir, path)
        self.sounds[name] = pygame.mixer.Sound(full_path)


    def play_sound(self, name: str, get_position, loop: bool = False, base_volume: float = 1.0, panning: bool = True, max_distance: float = 2000, get_volume_multiplier=lambda: 1.0):
        """
        Přehraje zvuk na dané pozici a vytvoří aktivní zdroj zvuku.

        Args:
            name (str): název zvuku v paměti
            get_position (callable): funkce/lambda vracející aktuální pozici zdroje ve světě
            loop (bool; default = False): zda se má zvuk přehrávat v loopu
            base_volume (float; default = 1.0): základní hlasitost (0.0-1.0)
            panning (bool; default = True): zda povolit panning zvuku
            max_distance (float; default = 2000): max. dosah zvuku v metrech
            get_volume_multiplier (callable; default = lambda: 1.0): funkce/lambda vracející násobič hlasitosti pro daný frame

        Returns:
            AudioSource: zdroj zvuku
        """
        if name not in self.sounds:
            return None
        
        channel = pygame.mixer.find_channel(force=True)
        if not channel:
            return None
            
        sound = self.sounds[name]
        channel.play(sound, loops=-1 if loop else 0)
        
        source = AudioSource(
            channel=channel,
            sound_name=name,
            get_position=get_position,
            base_volume=base_volume,
            panning=panning,
            max_distance=max_distance,
            loop=loop,
            get_volume_multiplier=get_volume_multiplier
        )
        self.active_sources.append(source)
        self._update_source(source)
        return source

    def play_oneshot(self, name: str, position: tuple[float, float], base_volume: float = 1.0, panning: bool = True, max_distance: float = 2000):
        """
        Zahraje zvuk jednorázově na statické pozici.

        Args:
            name (str): název zvuku v paměti
            position (tuple[float, float]): statická pozice zdroje ve světě (x, y)
            base_volume (float; default = 1.0): základní hlasitost (0.0-1.0)
            panning (bool; default = True): zda povolit panning zvuku
            max_distance (float; default = 2000): max. dosah zvuku v metrech
        """
        self.play_sound(name, lambda: position, loop=False, base_volume=base_volume, panning=panning, max_distance=max_distance)

    def stop_source(self, source: AudioSource):
        """
        Zastaví přehrávání konkrétního aktivního zdroje zvuku a odstraní jej ze sledování.

        Args:
            source (AudioSource): aktivní zdroj zvuku
        """
        if source and source in self.active_sources:
            source.channel.stop()
            self.active_sources.remove(source)

    def update(self):
        """
        Aktualizuje hlasitosti všech aktivních zvuků.
        """
        self.active_sources = [s for s in self.active_sources if s.channel.get_busy()] # odstranění dohraných zdrojů
        
        for source in self.active_sources:
            self._update_source(source)
            
    def _update_source(self, source: AudioSource):
        """
        Přepočítá hlasitost a panning jednoho aktivního zdroje podle kamery.

        Args:
            source (AudioSource): aktivní zdroj zvuku
        """
        pos = source.get_position()
        if pos is None:
            source.channel.set_volume(0)
            return

        screen_pos = self.game.screen_position(pos)
        sw, sh = self.game.screen.get_size()
        cx, cy = sw / 2, sh / 2
        
        # px od středu obrazovky
        dist_px = math.hypot(screen_pos[0] - cx, screen_pos[1] - cy)
        


        # hlasitost podle zoomu

        # mapa rozsahu zoomu
        zoom_min_vol = 0.005
        zoom_max_vol = 0.3

        if self.game.camera.zoom >= zoom_max_vol:
            zoom_factor = 1.0
        elif self.game.camera.zoom <= zoom_min_vol:
            zoom_factor = 0.0
        else:
            # lineární mapování
            zoom_factor = (self.game.camera.zoom - zoom_min_vol) / (zoom_max_vol - zoom_min_vol)
        

        world_dist = math.hypot(pos[0] - self.game.camera.position[0], pos[1] - self.game.camera.position[1])
        
        # útlum kvůli vzdálenosti (lineánrí)
        dist_multiplier = max(0.0, 1.0 - (world_dist / source.max_distance))
        
        dynamic_vol = source.get_volume_multiplier()
        
        final_volume = source.base_volume * dynamic_vol * dist_multiplier * zoom_factor
        
        if source.panning:
            # panning
            pan_val = (screen_pos[0] - cx) / cx # -1 (vlevo) <-> 1 (vpravo)
            pan_val = max(-1.0, min(1.0, pan_val))
            
            left_vol = final_volume * min(1.0, 1.0 - pan_val)
            right_vol = final_volume * min(1.0, 1.0 + pan_val)
            source.channel.set_volume(left_vol, right_vol)
        else:
            source.channel.set_volume(final_volume, final_volume)
