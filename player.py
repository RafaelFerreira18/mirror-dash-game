# -*- coding: utf-8 -*-
"""
player.py
=========
Define o personagem jogável (P1 e P2).

Transformações aplicadas:
  - Translação : move(dx, dy) usa translate() de transforms.py
  - Escala     : apply_scale_powerup() altera scale_x/scale_y; get_sprite() usa scale_surface()
  - Reflexão   : get_sprite() usa reflect_surface() para o personagem espelho (P2)
"""

import pygame
from settings import (
    GRAVITY, JUMP_FORCE, COLOR_PLAYER1, COLOR_PLAYER2,
)
from transforms import translate, scale_surface, reflect_surface


class Player:
    """
    Representa um personagem controlável no Mirror Dash.

    Parâmetros
    ----------
    x, y        : posição inicial (pixels)
    is_mirror   : True → personagem é P2 (reflexo de P1)
    color       : cor base do sprite (sobrescrita para P2)
    """

    BASE_WIDTH  = 32
    BASE_HEIGHT = 32

    def __init__(self, x, y, is_mirror=False, color=COLOR_PLAYER1):
        self.start_x = float(x)
        self.start_y = float(y)
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.is_mirror = is_mirror
        self.color = COLOR_PLAYER2 if is_mirror else color
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.scale_timer = 0
        self.facing_right = not is_mirror  # P2 nasce virado para a esquerda
        # Coyote time: permite pular poucos frames após sair da plataforma
        self.coyote_timer = 0
        self.COYOTE_FRAMES = 6
        # Jump buffer: registra intenção de pular antes de pousar
        self.jump_buffer = 0
        self.JUMP_BUFFER_FRAMES = 8
        self._build_sprite()

    def _build_sprite(self):
        """Constrói sprite base usando apenas pygame.draw (sem assets externos)."""
        base = pygame.Surface((self.BASE_WIDTH, self.BASE_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(base, self.color,
                         (0, 0, self.BASE_WIDTH, self.BASE_HEIGHT), border_radius=6)
        # Olhos
        pygame.draw.circle(base, (255, 255, 255), (10, 12), 4)
        pygame.draw.circle(base, (255, 255, 255), (22, 12), 4)
        pygame.draw.circle(base, (0, 0, 0),       (11, 12), 2)
        pygame.draw.circle(base, (0, 0, 0),       (23, 12), 2)
        # Boca
        pygame.draw.arc(base, (0, 0, 0),
                        pygame.Rect(8, 18, 16, 8), 3.14, 2 * 3.14, 2)
        self._base_sprite = base

    # ------------------------------------------------------------------
    # Propriedades dinâmicas (dependem da escala atual)
    # ------------------------------------------------------------------

    @property
    def width(self):
        return max(1, int(self.BASE_WIDTH * self.scale_x))

    @property
    def height(self):
        return max(1, int(self.BASE_HEIGHT * self.scale_y))

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    # ------------------------------------------------------------------
    # Transformações
    # ------------------------------------------------------------------

    def move(self, dx, dy):
        """[TRANSFORMAÇÃO] Translação — move o jogador pelo vetor (dx, dy)."""
        self.x, self.y = translate(self.x, self.y, dx, dy)

    def apply_scale_powerup(self, sx, sy, duration_frames):
        """[TRANSFORMAÇÃO] Escala — altera tamanho durante duration_frames quadros."""
        self.scale_x = sx
        self.scale_y = sy
        self.scale_timer = duration_frames

    def update_scale(self):
        """Conta regressiva do power-up de escala; restaura tamanho ao expirar."""
        if self.scale_timer > 0:
            self.scale_timer -= 1
            if self.scale_timer == 0:
                self.scale_x = 1.0
                self.scale_y = 1.0

    def get_sprite(self):
        """
        Retorna sprite processado com as transformações ativas.

        [TRANSFORMAÇÃO] Escala    — redimensiona via scale_surface()
        [TRANSFORMAÇÃO] Reflexão  — espelha P2 via reflect_surface()
        """
        # [TRANSFORMAÇÃO] Escala — aplica fator de escala atual ao sprite base
        sprite = scale_surface(self._base_sprite, self.scale_x, self.scale_y)

        # [TRANSFORMAÇÃO] Reflexão — P2 é sempre exibido espelhado
        if self.is_mirror:
            sprite = reflect_surface(sprite)
        elif not self.facing_right:
            sprite = pygame.transform.flip(sprite, True, False)

        return sprite

    # ------------------------------------------------------------------
    # Física
    # ------------------------------------------------------------------

    def update_physics(self, platforms):
        """
        Aplica gravidade (translação em Y) e resolve colisões com plataformas.

        A gravidade é implementada como translação incremental em Y:
            y_new = y + vy,  onde vy aumenta GRAVITY por frame (queda livre).
        """
        # Gravidade
        self.vy += GRAVITY

        # Limita velocidade de queda para evitar túnel em plataformas finas
        if self.vy > 16:
            self.vy = 16

        # Salva posição anterior para resolver colisão corretamente
        old_bottom = self.y + self.height
        old_top = self.y

        # [TRANSFORMAÇÃO] Translação — move verticalmente pelo vetor (0, vy)
        self.move(0, self.vy)

        was_on_ground = self.on_ground
        self.on_ground = False

        for plat in platforms:
            prect = plat.get_collision_rect()
            if self.rect.colliderect(prect):
                # Plataforma giratória inclinada demais → não colide, player cai
                if not plat.is_landable():
                    continue
                if self.vy >= 0 and old_bottom <= prect.top + 8:
                    # Estava acima → pousa no topo da plataforma
                    self.y = prect.top - self.height
                    self.vy = 0.0
                    self.on_ground = True
                elif self.vy < 0 and old_top >= prect.bottom - 8:
                    # Estava abaixo → bateu a cabeça
                    self.y = prect.bottom
                    self.vy = 0.0

        # Coyote time: permite pular por alguns frames após cair de plataforma
        if self.on_ground:
            self.coyote_timer = self.COYOTE_FRAMES
        elif was_on_ground:
            self.coyote_timer = self.COYOTE_FRAMES
        else:
            if self.coyote_timer > 0:
                self.coyote_timer -= 1

        # Jump buffer: se o jogador pediu pulo recentemente e agora pode pular
        if self.jump_buffer > 0:
            self.jump_buffer -= 1
            if self.on_ground or self.coyote_timer > 0:
                self._do_jump()

    def _do_jump(self):
        """Executa o pulo de fato."""
        self.vy = JUMP_FORCE
        self.on_ground = False
        self.coyote_timer = 0
        self.jump_buffer = 0

    def jump(self):
        """[TRANSFORMAÇÃO] Translação — aplica impulso vertical (JUMP_FORCE em Y)."""
        if self.on_ground or self.coyote_timer > 0:
            self._do_jump()
        else:
            # Armazena intenção de pulo para os próximos frames
            self.jump_buffer = self.JUMP_BUFFER_FRAMES

    # ------------------------------------------------------------------
    # Desenho e reset
    # ------------------------------------------------------------------

    def draw(self, surface):
        surface.blit(self.get_sprite(), (int(self.x), int(self.y)))

    def reset(self):
        self.x = self.start_x
        self.y = self.start_y
        self.vx = 0.0
        self.vy = 0.0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.scale_timer = 0
        self.on_ground = False
        self.coyote_timer = 0
        self.jump_buffer = 0
