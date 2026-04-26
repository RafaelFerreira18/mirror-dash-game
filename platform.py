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
from transforms import rotate_point, translate


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
                 rotating=False, rotation_speed=1.0, color=COLOR_PLATFORM,
                 moving=False, move_dx=0.0, move_dy=0.0,
                 move_x_min=None, move_x_max=None,
                 move_y_min=None, move_y_max=None):
        self.base_x = x
        self.base_y = y
        self.width  = width
        self.height = height
        self.rotating       = rotating
        self.rotation_speed = rotation_speed
        self.angle = 0.0
        self.color = color
        # [TRANSFORMAÇÃO] Translação — campos de movimento
        self.moving     = moving
        self.move_dx    = move_dx
        self.move_dy    = move_dy
        self.move_x_min = move_x_min if move_x_min is not None else x
        self.move_x_max = move_x_max if move_x_max is not None else x
        self.move_y_min = move_y_min if move_y_min is not None else y
        self.move_y_max = move_y_max if move_y_max is not None else y
        self._move_dir_x = 1
        self._move_dir_y = 1
        self._build_surface()

    def _build_surface(self):
        """Constrói surface da plataforma sem assets externos."""
        self._surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(self._surface, self.color,
                         (0, 0, self.width, self.height), border_radius=4)
        # Linha decorativa no topo
        highlight = tuple(min(c + 60, 255) for c in self.color)
        pygame.draw.line(self._surface, highlight, (3, 2), (self.width - 3, 2), 2)
        # Indicador visual para plataformas móveis: setas ↔
        if getattr(self, 'moving', False):
            arrow_col = (220, 255, 200)
            mid_y = self.height // 2
            for xi in [self.width // 4, self.width // 2, 3 * self.width // 4]:
                # Seta apontando para a direita
                pygame.draw.polygon(self._surface, arrow_col, [
                    (xi - 3, mid_y - 3),
                    (xi + 3, mid_y),
                    (xi - 3, mid_y + 3),
                ])

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

    def get_tilt(self):
        """
        Retorna a inclinação efetiva da plataforma em graus [-90, 90].
        0 = perfeitamente horizontal. Valores positivos = inclinada para a direita.
        Plataformas estáticas sempre retornam 0.
        """
        if not self.rotating:
            return 0.0
        # Normaliza para -180..180
        a = self.angle % 360
        if a > 180:
            a -= 360
        # Mapeia para -90..90 (superfície pode estar "de cabeça pra baixo")
        if a > 90:
            a = 180 - a
        elif a < -90:
            a = -180 - a
        return a

    def get_carry_vx(self):
        """
        [TRANSFORMAÇÃO] Translação — retorna a velocidade horizontal atual
        para ser aplicada ao jogador que está em cima da plataforma.
        """
        if self.moving and self.move_dx != 0.0:
            return self.move_dx * self._move_dir_x
        return 0.0

    def update(self):
        """[TRANSFORMAÇÃO] Rotação e Translação — atualiza estado a cada frame."""
        if self.rotating:
            self.angle = (self.angle + self.rotation_speed) % 360

        if self.moving:
            # [TRANSFORMAÇÃO] Translação — usa translate() de transforms.py
            nx, ny = translate(self.base_x, self.base_y,
                               self.move_dx * self._move_dir_x,
                               self.move_dy * self._move_dir_y)
            if self.move_dx != 0.0:
                if nx <= self.move_x_min:
                    self._move_dir_x = 1
                    nx = self.move_x_min
                elif nx >= self.move_x_max:
                    self._move_dir_x = -1
                    nx = self.move_x_max
            if self.move_dy != 0.0:
                if ny <= self.move_y_min:
                    self._move_dir_y = 1
                    ny = self.move_y_min
                elif ny >= self.move_y_max:
                    self._move_dir_y = -1
                    ny = self.move_y_max
            self.base_x = nx
            self.base_y = ny

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
            draw_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(draw_surf, self.color,
                             (0, 0, self.width, self.height), border_radius=4)
            highlight = tuple(min(c + 60, 255) for c in self.color)
            pygame.draw.line(draw_surf, highlight, (3, 2), (self.width - 3, 2), 2)

            # Rotaciona a surface do pygame em torno do centro
            rotated = pygame.transform.rotate(draw_surf, -self.angle)
            rect = rotated.get_rect(center=self.center)
            surface.blit(rotated, rect.topleft)
        else:
            surface.blit(self._surface, (self.base_x, self.base_y))
