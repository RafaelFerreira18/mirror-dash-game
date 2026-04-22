# -*- coding: utf-8 -*-
"""
platform.py
===========
Plataformas estáticas e giratórias.

Transformações aplicadas:
  - Rotação    : plataformas giratórias acumulam ângulo a cada frame;
                 get_rotated_corners() usa rotate_point() de transforms.py
  - Translação : posicionamento absoluto definido pelo JSON de fase
"""

import pygame
import math
from settings import COLOR_PLATFORM
from transforms import rotate_point


class Platform:
    """
    Plataforma retangular, podendo ser estática ou giratória.

    Parâmetros
    ----------
    x, y            : canto superior-esquerdo (pixels)
    width, height   : dimensões em pixels
    rotating        : True → plataforma gira em torno do próprio centro
    rotation_speed  : graus por frame (negativo = sentido anti-horário)
    color           : cor de preenchimento
    """

    def __init__(self, x, y, width, height,
                 rotating=False, rotation_speed=1.0, color=COLOR_PLATFORM):
        self.base_x = x
        self.base_y = y
        self.width  = width
        self.height = height
        self.rotating       = rotating
        self.rotation_speed = rotation_speed
        self.angle = 0.0
        self.color = color
        self._build_surface()

    def _build_surface(self):
        """Constrói surface da plataforma sem assets externos."""
        self._surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(self._surface, self.color,
                         (0, 0, self.width, self.height), border_radius=4)
        # Linha decorativa no topo
        highlight = tuple(min(c + 60, 255) for c in self.color)
        pygame.draw.line(self._surface, highlight, (3, 2), (self.width - 3, 2), 2)

    @property
    def rect(self):
        """Rect do AABB usado para posicionamento e desenho."""
        return pygame.Rect(self.base_x, self.base_y, self.width, self.height)

    @property
    def center(self):
        return (self.base_x + self.width // 2, self.base_y + self.height // 2)

    def get_collision_rect(self):
        """
        Retorna o Rect usado para detecção de colisão.

        Plataformas giratórias: retorna o bounding box (AABB) dos cantos
        rotacionados, de modo que a colisão acompanha a rotação visual.

        [TRANSFORMAÇÃO] Rotação — a hitbox muda a cada frame via rotate_point().
        """
        if not self.rotating:
            return self.rect
        corners = self.get_rotated_corners()
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        min_x = int(min(xs))
        min_y = int(min(ys))
        max_x = int(max(xs))
        max_y = int(max(ys))
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)

    def is_landable(self):
        """
        Retorna True se a plataforma está suficientemente horizontal
        para o jogador pousar. Plataformas estáticas são sempre pousáveis.

        Plataformas giratórias só permitem pouso quando o ângulo está
        dentro de ±35° de 0° ou 180° (superfície quase horizontal).
        """
        if not self.rotating:
            return True
        # Normaliza ângulo para 0-360
        a = self.angle % 360
        # Distância angular até a horizontal mais próxima (0° ou 180°)
        tilt = min(a % 180, 180 - (a % 180))
        return tilt <= 35

    def update(self):
        """[TRANSFORMAÇÃO] Rotação — incrementa o ângulo de rotação a cada frame."""
        if self.rotating:
            self.angle = (self.angle + self.rotation_speed) % 360

    def get_rotated_corners(self):
        """
        Retorna os quatro cantos após aplicar a rotação corrente.
        Usa rotate_point() de transforms.py (matrizes homogêneas).

        [TRANSFORMAÇÃO] Rotação — cada canto é rotacionado em torno do centro.
        """
        cx, cy = self.center
        corners = [
            (self.base_x,               self.base_y),
            (self.base_x + self.width,  self.base_y),
            (self.base_x + self.width,  self.base_y + self.height),
            (self.base_x,               self.base_y + self.height),
        ]
        return [rotate_point(px, py, self.angle, cx, cy) for px, py in corners]

    def draw(self, surface):
        if self.rotating:
            # Recria surface com cor indicando se é pousável
            draw_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            if self.is_landable():
                # Cor normal — seguro para pousar
                draw_color = self.color
            else:
                # Vermelho/escuro semi-transparente — perigoso, não dá pra pousar
                draw_color = (
                    min(self.color[0] + 80, 255),
                    max(self.color[1] - 80, 30),
                    max(self.color[2] - 80, 30),
                )
            pygame.draw.rect(draw_surf, draw_color,
                             (0, 0, self.width, self.height), border_radius=4)
            highlight = tuple(min(c + 60, 255) for c in draw_color)
            pygame.draw.line(draw_surf, highlight, (3, 2), (self.width - 3, 2), 2)

            # Rotaciona a surface do pygame em torno do centro
            rotated = pygame.transform.rotate(draw_surf, -self.angle)
            rect = rotated.get_rect(center=self.center)
            surface.blit(rotated, rect.topleft)
        else:
            surface.blit(self._surface, (self.base_x, self.base_y))
