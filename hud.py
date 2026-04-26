# -*- coding: utf-8 -*-
"""
hud.py
======
Heads-Up Display: exibe vidas (corações), fase atual, barra de power-up
e controles na tela.
"""

import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


class HUD:
    def __init__(self):
        self.font_main  = pygame.font.SysFont(None, 28)
        self.font_small = pygame.font.SysFont(None, 22)
        self._heart = self._build_heart()

    # ------------------------------------------------------------------

    @staticmethod
    def _build_heart():
        """Desenha um coração 18×16 usando círculos + triângulo."""
        w, h = 18, 16
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        color = (220, 50, 60)
        r = 5
        pygame.draw.circle(surf, color, (5, 5), r)
        pygame.draw.circle(surf, color, (13, 5), r)
        pygame.draw.polygon(surf, color, [(1, 7), (w - 1, 7), (w // 2, h - 1)])
        return surf

    # ------------------------------------------------------------------

    def draw(self, surface, lives, level, level_name,
             scale_timer=0, scale_max=1, scale_kind=""):
        # — Corações (vidas) —
        for i in range(lives):
            surface.blit(self._heart, (12 + i * 24, 10))

        # — Fase (centro superior) —
        level_txt = self.font_main.render(
            f"Fase {level} — {level_name}", True, (200, 200, 255))
        surface.blit(level_txt,
                     (SCREEN_WIDTH // 2 - level_txt.get_width() // 2, 10))

        # — Barra de power-up —
        if scale_timer > 0 and scale_max > 0:
            bar_w = 80
            bar_h = 6
            bar_x = 12
            bar_y = 34
            ratio = scale_timer / scale_max

            # fundo
            pygame.draw.rect(surface, (40, 40, 60),
                             (bar_x, bar_y, bar_w, bar_h), border_radius=3)
            # preenchimento
            fill_color = (255, 180, 50) if scale_kind == "grow" else (100, 220, 255)
            fill_w = max(1, int(bar_w * ratio))
            pygame.draw.rect(surface, fill_color,
                             (bar_x, bar_y, fill_w, bar_h), border_radius=3)

            label_text = "GRANDE" if scale_kind == "grow" else "PEQUENO"
            label = self.font_small.render(label_text, True, fill_color)
            surface.blit(label, (bar_x + bar_w + 8, bar_y - 4))

        # — Controles (rodapé) —
        ctrl = self.font_small.render(
            "← → mover  |  ESPAÇO pular  |  R reiniciar  |  ESC menu",
            True, (100, 100, 130))
        surface.blit(ctrl,
                     (SCREEN_WIDTH // 2 - ctrl.get_width() // 2,
                      SCREEN_HEIGHT - 24))
