import pygame

class UIManager:
    """
    Správce uživatelského rozhraní.
    """
    def __init__(self, game):
        """
        Inicializuje správce UI.

        Args:
            game (TerminusEngine.Game): instance hry
        """
        self.game = game
        self.font_small = pygame.font.SysFont(game.font_name, 18)
        self.font = pygame.font.SysFont(game.font_name, 24)
        self.font_large = pygame.font.SysFont(game.font_name, 32, bold=True)
        self._was_pressed = False
        self.mouse_pressed = False
        self.mouse_released = False
        
    def update(self):
        """
        Aktualizuje stav myši (kliknutí a uvolnění tlačítka).
        """
        self.mouse_pressed = False
        self.mouse_released = False
        
        pressed = pygame.mouse.get_pressed()[0]
            
        if pressed and not self._was_pressed:
            self.mouse_pressed = True
        elif not pressed and self._was_pressed:
            self.mouse_released = True
            
        self._was_pressed = pressed

    def panel(self, rect, color=(30, 32, 38, 240), border_radius=12):
        """
        Vykreslí panel.

        Args:
            rect (tuple nebo pygame.Rect): pozice a velikost panelu (x, y, šířka, výška).
            color (tuple): barva pozadí (R, G, B, A)
            border_radius (int): poloměr zaoblení rohů
        """
        if not isinstance(rect, pygame.Rect):
            rect = pygame.Rect(rect)
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, color, s.get_rect(), border_radius=border_radius)
        self.game.screen.blit(s, rect.topleft)
        pygame.draw.rect(self.game.screen, (80, 85, 95), rect, width=2, border_radius=border_radius)

    def label(self, pos, text, color=(240, 240, 240), align="left", size="normal"):
        """
        Vykreslí text.

        Args:
            pos (tuple): pozice ukotvení textu (x, y)
            text (str): text
            color (tuple): barva textu
            align (str): zarovnání textu ("left", "center", "right")
            size (str): velikost písma ("small", "normal", "large")
        """
        if size == "small":
            f = self.font_small
        elif size == "large":
            f = self.font_large
        else:
            f = self.font
            
        surf = f.render(str(text), True, color)
        r = surf.get_rect()
        if align == "left":
            r.topleft = pos
        elif align == "center":
            r.center = pos
        elif align == "right":
            r.topright = pos
        self.game.screen.blit(surf, r)

    def button(self, rect, text, color=(45, 90, 160), hover_color=(60, 115, 200), text_color=(255, 255, 255), disabled=False):
        """
        Vykreslí interaktivní tlačítko a vrátí True, pokud bylo stisknuto.

        Args:
            rect (tuple nebo pygame.Rect): pozice a velikost tlačítka (x, y, šířka, výška)
            text (str): text zobrazený na tlačítku
            color (tuple): barva pozadí
            hover_color (tuple): barva pozadí při hoveru
            text_color (tuple): barva textu
            disabled (bool): zda je tlačítko neaktivní
        """
        if not isinstance(rect, pygame.Rect):
            rect = pygame.Rect(rect)
            
        mouse_pos = pygame.mouse.get_pos()
        clip = self.game.screen.get_clip()
        hovered = rect.collidepoint(mouse_pos) and clip.collidepoint(mouse_pos)
        clicked = hovered and self.mouse_released and not disabled

        if disabled:
            draw_color = (60, 65, 75)
        else:
            draw_color = hover_color if hovered else color

        # stín
        shadow_rect = rect.copy()
        shadow_rect.y += 3
        pygame.draw.rect(self.game.screen, (15, 15, 20), shadow_rect, border_radius=8)

        pygame.draw.rect(self.game.screen, draw_color, rect, border_radius=8)
        border_color = (120, 160, 220) if hovered and not disabled else (60, 70, 80)
        pygame.draw.rect(self.game.screen, border_color, rect, width=2, border_radius=8)

        if text:
            f = self.font
            surf = f.render(str(text), True, (140, 140, 140) if disabled else text_color)
            r = surf.get_rect(center=rect.center)
            self.game.screen.blit(surf, r)

        return clicked

