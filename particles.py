# -*- coding: utf-8 -*-
"""
particles.py
============
Sistema de partículas leve para efeitos visuais (coleta de power-up,
portais de saída, etc.).
"""

import pygame
import random
import math


class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size')

    def __init__(self, x, y, vx, vy, life, color, size):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size


class ParticleSystem:
    """Gerencia uma lista de partículas com emissão em rajada ou contínua."""

    def __init__(self):
        self.particles: list[Particle] = []

    # ------------------------------------------------------------------
    # Emissão
    # ------------------------------------------------------------------

    def emit_burst(self, x, y, color, count=20, speed=3.0, life=30, size=3.0):
        """Emite *count* partículas em todas as direções a partir de (x, y)."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(speed * 0.3, speed)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            c = tuple(min(255, max(0, ch + random.randint(-30, 30)))
                      for ch in color)
            s = random.uniform(size * 0.5, size * 1.2)
            self.particles.append(
                Particle(x, y, vx, vy,
                         life + random.randint(-5, 5), c, s))

    def emit_stream(self, x, y, color, count=1, speed=1.0, life=20,
                    size=2.0, direction=(0, -1)):
        """Emite *count* partículas na *direction* indicada (stream contínuo)."""
        base_angle = math.atan2(direction[1], direction[0])
        for _ in range(count):
            angle = base_angle + random.uniform(-0.5, 0.5)
            spd = random.uniform(speed * 0.4, speed)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            c = tuple(min(255, max(0, ch + random.randint(-20, 20)))
                      for ch in color)
            s = random.uniform(size * 0.5, size)
            self.particles.append(
                Particle(x + random.randint(-4, 4), y, vx, vy, life, c, s))

    # ------------------------------------------------------------------
    # Atualização e desenho
    # ------------------------------------------------------------------

    def update(self):
        alive = []
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += 0.04          # leve gravidade nas partículas
            p.vx *= 0.98          # atrito
            p.life -= 1
            if p.life > 0:
                alive.append(p)
        self.particles = alive

    def draw(self, surface):
        for p in self.particles:
            alpha = max(0.0, p.life / p.max_life)
            sz = max(1, int(p.size * alpha))
            if alpha < 0.5:
                color = tuple(int(c * alpha * 2) for c in p.color)
            else:
                color = p.color
            pygame.draw.circle(surface, color, (int(p.x), int(p.y)), sz)

    def clear(self):
        self.particles.clear()
