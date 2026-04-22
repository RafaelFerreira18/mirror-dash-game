# -*- coding: utf-8 -*-
"""
hud.py
======
Heads-Up Display: exibe vidas, fase atual e controles na tela.
"""

import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


class HUD:
    def __init__(self):
        self.font_main  = pygame.font.SysFont(None, 30)
        self.font_small = pygame.font.SysFont(None, 22)

    def draw(self, surface, lives, level, level_name):
        # Vidas — canto superior esquerdo
        lives_txt = self.font_main.render(f"Vidas: {lives}", True, (220, 80, 80))
        surface.blit(lives_txt, (10, 10))

        # Fase — centro superior
        level_txt = self.font_main.render(
            f"Fase {level}: {level_name}", True, (200, 200, 255))
        surface.blit(level_txt,
                     (SCREEN_WIDTH // 2 - level_txt.get_width() // 2, 10))

        # Controles — rodapé central
        ctrl = self.font_small.render(
            "A/D ou setas: mover   |   W / ESPACO: pular", True, (130, 130, 160))
        surface.blit(ctrl,
                     (SCREEN_WIDTH // 2 - ctrl.get_width() // 2,
                      SCREEN_HEIGHT - 26))
