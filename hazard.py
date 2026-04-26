# -*- coding: utf-8 -*-
"""
hazard.py
=========
Obstáculos mortais: espinhos estáticos e lasers horizontais.

  - Spike  : triângulos afiados fixos em plataformas; tocá-los mata o jogador.
             Se o jogador está com 'shrink', o hitbox menor pode ajudar a desviar.
  - Laser  : feixe horizontal que liga/desliga periodicamente.
             Se o jogador está com 'grow', o pulo maior ajuda a pular por cima.
"""

import pygame
import math


class Spike:
    """
    Fileira de espinhos em uma posição fixa.

    Parâmetros
    ----------
    x, y     : canto superior-esquerdo da área de espinhos
    w        : largura total da fileira
    h        : altura dos espinhos (ponta a base)
    facing   : 'up' (padrão) ou 'down'
    """

    def __init__(self, x, y, w, h=16, facing='up'):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.facing = facing
        self._color = (220, 60, 60)
        self._highlight = (255, 120, 120)

    @property
    def rect(self):
        """Hitbox dos espinhos — ligeiramente menor para ser justo."""
        margin_x = 4
        margin_y = 4
        return pygame.Rect(self.x + margin_x, self.y + margin_y,
                           self.w - margin_x * 2, self.h - margin_y * 2)

    def draw(self, surface):
        spike_w = 14
        count = max(1, self.w // spike_w)
        actual_w = self.w / count

        for i in range(count):
            bx = self.x + i * actual_w
            if self.facing == 'up':
                points = [
                    (bx, self.y + self.h),
                    (bx + actual_w / 2, self.y),
                    (bx + actual_w, self.y + self.h),
                ]
            else:
                points = [
                    (bx, self.y),
                    (bx + actual_w / 2, self.y + self.h),
                    (bx + actual_w, self.y),
                ]
            pygame.draw.polygon(surface, self._color, points)
            # Highlight na ponta
            tip = points[1]
            pygame.draw.circle(surface, self._highlight,
                               (int(tip[0]), int(tip[1])), 2)


class Laser:
    """
    Feixe horizontal que liga/desliga ciclicamente.

    Parâmetros
    ----------
    x, y     : início do feixe (esquerda)
    w        : comprimento do feixe
    on_frames  : quadros ligado
    off_frames : quadros desligado
    offset     : fase inicial (para sincronizar vários lasers)
    """

    def __init__(self, x, y, w, on_frames=90, off_frames=90, offset=0):
        self.x = x
        self.y = y
        self.w = w
        self.h = 8          # espessura do feixe
        self.on_frames = on_frames
        self.off_frames = off_frames
        self._timer = offset % (on_frames + off_frames)
        self._color_core = (255, 50, 50)
        self._color_glow = (255, 100, 100)

    @property
    def is_active(self):
        return self._timer < self.on_frames

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y - self.h // 2, self.w, self.h)

    def update(self):
        self._timer = (self._timer + 1) % (self.on_frames + self.off_frames)

    def draw(self, surface, frame=0):
        # Emissores nas pontas (sempre visíveis)
        em_color = (180, 40, 40) if not self.is_active else (255, 80, 80)
        pygame.draw.circle(surface, em_color, (self.x, self.y), 5)
        pygame.draw.circle(surface, em_color, (self.x + self.w, self.y), 5)

        if not self.is_active:
            # Feixe desligado — linha tracejada sutil de aviso
            dash_y = self.y
            for dx in range(0, self.w, 12):
                pygame.draw.line(surface, (80, 20, 20),
                                 (self.x + dx, dash_y),
                                 (self.x + min(dx + 5, self.w), dash_y), 1)
            return

        # Feixe ativo — glow + core
        flicker = 0.7 + 0.3 * math.sin(frame * 0.3)
        gw = int(self.h * 1.5 * flicker)
        glow_rect = pygame.Rect(self.x, self.y - gw // 2, self.w, gw)
        gs = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        ga = int(50 * flicker)
        gs.fill((*self._color_glow, ga))
        surface.blit(gs, glow_rect.topleft)

        # Core beam
        core_h = max(2, int(4 * flicker))
        pygame.draw.rect(surface, self._color_core,
                         (self.x, self.y - core_h // 2, self.w, core_h))
