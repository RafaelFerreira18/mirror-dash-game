# -*- coding: utf-8 -*-
"""
powerup.py
==========
Itens coletáveis que aplicam transformação de escala ao jogador.

  - 'grow'   → sx=2.0, sy=2.0  (dobra de tamanho por ~3 segundos)
  - 'shrink' → sx=0.5, sy=0.5  (reduz à metade por ~3 segundos)
"""

import pygame


class PowerUp:
    """
    Power-up flutuante que, ao ser coletado, dispara a transformação de escala
    nos dois jogadores simultaneamente.
    """

    DURATION = 180  # quadros (~3 s a 60 fps)

    def __init__(self, x, y, kind='grow'):
        self.x    = x
        self.y    = y
        self.kind = kind
        self.collected   = False
        self.size        = 24
        self.float_offset = 0.0
        self.float_dir   = 1

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y + int(self.float_offset),
                           self.size, self.size)

    @property
    def scale_values(self):
        """Retorna (sx, sy) correspondente ao tipo de power-up."""
        return (2.0, 2.0) if self.kind == 'grow' else (0.5, 0.5)

    def update(self):
        """Animação de flutuar suavemente."""
        self.float_offset += 0.15 * self.float_dir
        if abs(self.float_offset) > 8:
            self.float_dir *= -1

    def draw(self, surface):
        if self.collected:
            return
        color = (255, 180, 50) if self.kind == 'grow' else (100, 220, 255)
        cx = self.x + self.size // 2
        cy = self.y + self.size // 2 + int(self.float_offset)

        # Halo externo
        pygame.draw.circle(surface, tuple(max(c - 60, 0) for c in color),
                           (cx, cy), self.size // 2 + 4)
        # Corpo
        pygame.draw.circle(surface, color, (cx, cy), self.size // 2)

        # Ícone "+" (grow) ou "−" (shrink)
        font  = pygame.font.SysFont(None, 26)
        label = "+" if self.kind == 'grow' else "-"
        txt   = font.render(label, True, (0, 0, 0))
        surface.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))
