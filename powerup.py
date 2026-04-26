# -*- coding: utf-8 -*-
"""
powerup.py
==========
Itens coletáveis que aplicam transformação de escala ao jogador.

  - 'grow'   → sx=2.0, sy=2.0  (dobra de tamanho por ~3 segundos)
  - 'shrink' → sx=0.5, sy=0.5  (reduz à metade por ~3 segundos)
"""

import pygame
import math


class PowerUp:
    """
    Power-up flutuante que, ao ser coletado, dispara a transformação de escala
    nos dois jogadores simultaneamente.
    """

    DURATION = 420        # quadros (~7 s a 60 fps)
    RESPAWN_DELAY = 360   # quadros até reaparecer (~6 s)

    def __init__(self, x, y, kind='grow'):
        self.x    = x
        self.y    = y
        self.kind = kind
        self.collected   = False
        self.size        = 26
        self.float_offset = 0.0
        self.float_dir   = 1
        self._age = 0          # frame counter para animações
        self._respawn_timer = 0

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y + int(self.float_offset),
                           self.size, self.size)

    @property
    def scale_values(self):
        """Retorna (sx, sy) correspondente ao tipo de power-up."""
        return (2.0, 2.0) if self.kind == 'grow' else (0.5, 0.5)

    def update(self):
        """Animação de flutuar e lógica de respawn."""
        self._age += 1
        if self.collected:
            self._respawn_timer -= 1
            if self._respawn_timer <= 0:
                self.collected = False
                self._respawn_timer = 0
            return
        self.float_offset += 0.15 * self.float_dir
        if abs(self.float_offset) > 8:
            self.float_dir *= -1

    def collect(self):
        """Marca como coletado e inicia timer de respawn."""
        self.collected = True
        self._respawn_timer = self.RESPAWN_DELAY

    def draw(self, surface):
        if self.collected:
            return

        color = (255, 180, 50) if self.kind == 'grow' else (100, 220, 255)
        cx = self.x + self.size // 2
        cy = self.y + self.size // 2 + int(self.float_offset)

        # Anel pulsante externo
        pulse = 0.5 + 0.5 * math.sin(self._age * 0.08)
        ring_r = self.size // 2 + 5 + int(5 * pulse)
        ring_color = tuple(max(0, c - 80) for c in color)
        pygame.draw.circle(surface, ring_color, (cx, cy), ring_r, 2)

        # Halo
        halo_color = tuple(max(0, c - 40) for c in color)
        pygame.draw.circle(surface, halo_color, (cx, cy), self.size // 2 + 3)

        # Corpo principal
        pygame.draw.circle(surface, color, (cx, cy), self.size // 2)

        # Brilho sutil no topo
        highlight = tuple(min(255, c + 80) for c in color)
        pygame.draw.circle(surface, highlight, (cx - 3, cy - 4), 3)

        # Ícone: seta ▲ (grow) ou ▼ (shrink)
        if self.kind == 'grow':
            pygame.draw.polygon(surface, (20, 20, 20), [
                (cx, cy - 7), (cx - 6, cy + 4), (cx + 6, cy + 4)])
        else:
            pygame.draw.polygon(surface, (20, 20, 20), [
                (cx, cy + 7), (cx - 6, cy - 4), (cx + 6, cy - 4)])
