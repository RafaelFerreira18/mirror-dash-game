# -*- coding: utf-8 -*-
"""
game.py
=======
Gerenciador principal do Mirror Dash.

Estados: menu → playing → win/gameover → próxima fase ou menu.

A mecânica central de reflexão é implementada via reflect_point() a cada frame:
a posição X de P2 = reflexão do X de P1 em torno de mirror_line_x.
Nunca hardcoded — a função matricial de transforms.py é sempre chamada.
"""

import pygame
import json
import os

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    PLAYER_SPEED,
    COLOR_PLAYER1, COLOR_PLAYER2, COLOR_EXIT,
    COLOR_PLATFORM_P1, COLOR_PLATFORM_P2,
    STATE_MENU, STATE_PLAYING, STATE_WIN, STATE_GAMEOVER,
)
from player import Player
from platform import Platform
from powerup import PowerUp
from hud import HUD
from transforms import reflect_point


class Game:
    """
    Gerencia o loop principal e todos os estados de jogo.

    Transformações centrais aplicadas aqui:
      - Reflexão  : posição X de P2 é sempre reflect_point(p1.x) a cada frame
      - Translação: movimento horizontal de P1 via player.move()
    """

    MAX_LEVELS = 4

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock      = pygame.time.Clock()
        self.state      = STATE_MENU
        self.current_level = 1
        self.lives      = 3
        self.hud        = HUD()
        self.font_big   = pygame.font.SysFont(None, 64)
        self.font_med   = pygame.font.SysFont(None, 36)
        self.font_small = pygame.font.SysFont(None, 24)
        self._load_level(self.current_level)

    # ------------------------------------------------------------------
    # Carregamento de fase
    # ------------------------------------------------------------------

    def _load_level(self, level_num):
        """Lê o JSON da fase e instancia todos os objetos do mundo."""
        path = os.path.join(os.path.dirname(__file__), "levels",
                            f"level{level_num}.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        self.mirror_line_x = data.get("mirror_line_x", SCREEN_WIDTH // 2)
        sx, sy = data["player_start"]

        # [TRANSFORMAÇÃO] Translação — posição inicial de P1 lida do JSON
        self.p1 = Player(sx, sy, is_mirror=False, color=COLOR_PLAYER1)

        # [TRANSFORMAÇÃO] Reflexão — posição inicial de P2 é espelho de P1
        # Usa reflexão baseada no centro (contabiliza largura do sprite)
        p2x = 2 * self.mirror_line_x - sx - Player.BASE_WIDTH
        self.p2 = Player(int(p2x), sy, is_mirror=True, color=COLOR_PLAYER2)

        self.platforms = [
            Platform(
                pd["x"], pd["y"], pd["w"], pd["h"],
                rotating=pd.get("rotating", False),
                rotation_speed=pd.get("speed", 1.0),
                color=COLOR_PLATFORM_P1,
            )
            for pd in data["platforms"]
        ]

        self.powerups = [
            PowerUp(pu["x"], pu["y"], pu.get("kind", "grow"))
            for pu in data.get("powerups", [])
        ]

        ex, ey, ew, eh = data["exit"]
        self.exit_rect  = pygame.Rect(ex, ey, ew, eh)
        self.bg_color   = tuple(data.get("background_color", [15, 15, 35]))
        self.level_name = data.get("name", f"Fase {level_num}")

    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------

    def run(self):
        while True:
            self.clock.tick(FPS)
            self._handle_events()
            self._update()
            self._draw()

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if self.state == STATE_MENU:
                    if event.key == pygame.K_RETURN:
                        self.state = STATE_PLAYING

                elif self.state == STATE_PLAYING:
                    if event.key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
                        # Ambos pulam simultaneamente
                        self.p1.jump()
                        self.p2.jump()

                elif self.state in (STATE_WIN, STATE_GAMEOVER):
                    if event.key == pygame.K_RETURN:
                        self._handle_transition()

    def _handle_transition(self):
        if self.state == STATE_WIN:
            if self.current_level < self.MAX_LEVELS:
                self.current_level += 1
                self._load_level(self.current_level)
                self.state = STATE_PLAYING
            else:
                # Zerou o jogo → volta ao menu
                self.current_level = 1
                self.lives = 3
                self._load_level(1)
                self.state = STATE_MENU
        elif self.state == STATE_GAMEOVER:
            self.lives = 3
            self._load_level(self.current_level)
            self.state = STATE_PLAYING

    # ------------------------------------------------------------------
    # Atualização
    # ------------------------------------------------------------------

    def _update(self):
        if self.state != STATE_PLAYING:
            return

        keys = pygame.key.get_pressed()

        # [TRANSFORMAÇÃO] Translação — movimento horizontal de P1
        dx = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            dx = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx =  PLAYER_SPEED
        if dx != 0:
            self.p1.facing_right = dx > 0
        self.p1.move(dx, 0)

        # Impede P1 de sair dos limites horizontais da tela
        self.p1.x = max(0, min(self.p1.x, SCREEN_WIDTH - self.p1.width))

        # [TRANSFORMAÇÃO] Reflexão — P2 espelha a posição X de P1 a cada frame
        # Usa reflexão baseada no centro para alinhar corretamente com o espelho
        p2x = self._mirror_x(self.p1.x, self.p1.width)
        self.p2.x = p2x

        # Sincroniza velocidade vertical antes da física
        self.p2.vy = self.p1.vy

        # Física vertical independente (com gravidade)
        self.p1.update_physics(self.platforms)
        self.p2.update_physics(self._get_mirrored_platforms())

        # [TRANSFORMAÇÃO] Escala — atualiza timer dos power-ups
        self.p1.update_scale()
        self.p2.update_scale()

        # Atualiza e verifica coleta de power-ups
        for pu in self.powerups:
            if not pu.collected:
                pu.update()
                if (self.p1.rect.colliderect(pu.rect) or
                        self.p2.rect.colliderect(pu.rect)):
                    pu.collected = True
                    sx, sy = pu.scale_values
                    # [TRANSFORMAÇÃO] Escala — aplica aos dois jogadores
                    self.p1.apply_scale_powerup(sx, sy, PowerUp.DURATION)
                    self.p2.apply_scale_powerup(sx, sy, PowerUp.DURATION)

        # Atualiza rotação das plataformas
        for plat in self.platforms:
            plat.update()

        # Morte por queda fora da tela
        fell = (self.p1.y > SCREEN_HEIGHT + 60 or
                self.p2.y > SCREEN_HEIGHT + 60)
        if fell:
            self.lives -= 1
            if self.lives <= 0:
                self.state = STATE_GAMEOVER
            else:
                self._load_level(self.current_level)
            return

        # Vitória — P1 precisa alcançar a saída principal
        # P2 estará automaticamente na saída espelhada se as posições estão corretas
        p1_at_exit = self.p1.rect.colliderect(self.exit_rect)
        if p1_at_exit:
            self.state = STATE_WIN

    # ------------------------------------------------------------------
    # Espelhamento de objetos do mundo
    # ------------------------------------------------------------------

    def _mirror_x(self, obj_x, obj_w):
        """
        [TRANSFORMAÇÃO] Reflexão — calcula a coordenada X espelhada de um objeto.
        Equivale a reflect_point aplicado ao centro do objeto.
        """
        obj_cx = obj_x + obj_w / 2
        mirrored_cx, _ = reflect_point(obj_cx, 0, axis='y',
                                        ref_line=self.mirror_line_x)
        return mirrored_cx - obj_w / 2

    def _get_mirrored_platforms(self):
        """
        Gera a lista de plataformas espelhadas em X para colisão de P2.

        [TRANSFORMAÇÃO] Reflexão — cada plataforma tem sua posição X
        calculada via reflexão em torno de mirror_line_x.
        """
        mirrored = []
        for plat in self.platforms:
            mx = int(self._mirror_x(plat.base_x, plat.width))
            mirrored.append(
                Platform(mx, plat.base_y, plat.width, plat.height,
                         color=COLOR_PLATFORM_P2)
            )
        return mirrored

    def _mirrored_exit(self):
        """
        [TRANSFORMAÇÃO] Reflexão — retorna o Rect da saída de P2 (espelho da de P1).
        """
        mx = int(self._mirror_x(self.exit_rect.x, self.exit_rect.width))
        return pygame.Rect(mx, self.exit_rect.y,
                           self.exit_rect.width, self.exit_rect.height)

    # ------------------------------------------------------------------
    # Renderização
    # ------------------------------------------------------------------

    def _draw(self):
        self.screen.fill(self.bg_color)

        if self.state == STATE_MENU:
            self._draw_menu()
        elif self.state == STATE_PLAYING:
            self._draw_game()
        elif self.state == STATE_WIN:
            self._draw_game()
            self._draw_overlay("SAÍDA ENCONTRADA!",
                               "ENTER para continuar", (80, 220, 100))
        elif self.state == STATE_GAMEOVER:
            self._draw_game()
            self._draw_overlay("GAME OVER",
                               "ENTER para tentar de novo", (220, 80, 80))

        pygame.display.flip()

    def _draw_menu(self):
        self.screen.fill((10, 10, 30))

        # Gradiente simples de estrelas
        import random
        rng = random.Random(42)
        for _ in range(80):
            sx = rng.randint(0, SCREEN_WIDTH)
            sy = rng.randint(0, SCREEN_HEIGHT)
            pygame.draw.circle(self.screen, (200, 200, 255), (sx, sy), 1)

        title = self.font_big.render("MIRROR DASH", True, (200, 220, 255))
        sub   = self.font_med.render("Pressione ENTER para jogar", True, (150, 150, 200))
        ctrl  = self.font_small.render(
            "A/D ou setas: mover   |   W / ESPACO: pular", True, (120, 120, 170))
        hint  = self.font_small.render(
            "Guie P1 (azul) e P2 (vermelho) até as saídas simultaneamente!",
            True, (100, 150, 200))

        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 180))
        self.screen.blit(sub,   (SCREEN_WIDTH // 2 - sub.get_width()   // 2, 280))
        self.screen.blit(ctrl,  (SCREEN_WIDTH // 2 - ctrl.get_width()  // 2, 340))
        self.screen.blit(hint,  (SCREEN_WIDTH // 2 - hint.get_width()  // 2, 390))

    def _draw_game(self):
        # Linha central de espelho
        line_surf = pygame.Surface((2, SCREEN_HEIGHT), pygame.SRCALPHA)
        line_surf.fill((255, 255, 255, 60))
        self.screen.blit(line_surf, (self.mirror_line_x - 1, 0))

        # Saída de P1 (direita)
        pygame.draw.rect(self.screen, COLOR_EXIT, self.exit_rect, border_radius=4)
        label_p1 = self.font_small.render("META", True, (0, 0, 0))
        self.screen.blit(label_p1, (self.exit_rect.x + 2,
                                    self.exit_rect.y + self.exit_rect.height // 2 - 7))

        # Saída de P2 (reflexo — esquerda)
        m_exit = self._mirrored_exit()
        pygame.draw.rect(self.screen, COLOR_EXIT, m_exit, border_radius=4)
        label_p2 = self.font_small.render("META", True, (0, 0, 0))
        self.screen.blit(label_p2, (m_exit.x + 2,
                                    m_exit.y + m_exit.height // 2 - 7))

        # Plataformas normais e espelhadas
        for plat in self.platforms:
            plat.draw(self.screen)
        for plat in self._get_mirrored_platforms():
            plat.draw(self.screen)

        # Power-ups
        for pu in self.powerups:
            pu.draw(self.screen)

        # Jogadores
        self.p1.draw(self.screen)
        self.p2.draw(self.screen)

        # HUD
        self.hud.draw(self.screen, self.lives,
                      self.current_level, self.level_name)

    def _draw_overlay(self, title_text, subtitle_text, color):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        t = self.font_big.render(title_text,    True, color)
        s = self.font_med.render(subtitle_text, True, (220, 220, 220))
        self.screen.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, 220))
        self.screen.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2, 310))
