# -*- coding: utf-8 -*-
"""
game.py
=======
Gerenciador principal do Mirror Dash.

Estados: menu → transition → playing → win/gameover → próxima fase ou menu.

A mecânica central de reflexão é implementada via reflect_point() a cada frame:
a posição X de P2 = reflexão do X de P1 em torno de mirror_line_x.
Nunca hardcoded — a função matricial de transforms.py é sempre chamada.
"""

import pygame
import json
import os
import math
import random

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    PLAYER_SPEED, TRANSITION_FRAMES,
    COLOR_PLAYER1, COLOR_PLAYER2, COLOR_EXIT,
    COLOR_PLATFORM_P1, COLOR_PLATFORM_P2,
    STATE_MENU, STATE_PLAYING, STATE_WIN, STATE_GAMEOVER, STATE_TRANSITION,
)
from player import Player
from platform import Platform
from powerup import PowerUp
from hazard import Spike, Laser
from hud import HUD
from transforms import reflect_point
from particles import ParticleSystem


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
        self.particles  = ParticleSystem()
        self.frame      = 0
        self.transition_timer = 0
        self.hint       = ""
        self.death_flash = 0
        self.font_big   = pygame.font.SysFont(None, 72, bold=True)
        self.font_med   = pygame.font.SysFont(None, 38)
        self.font_small = pygame.font.SysFont(None, 24)
        self.font_hint  = pygame.font.SysFont(None, 22)

        # Estrelas pré-calculadas para menus / backgrounds
        rng = random.Random(42)
        self.stars = [(rng.randint(0, SCREEN_WIDTH),
                       rng.randint(0, SCREEN_HEIGHT),
                       rng.uniform(0.5, 2.0)) for _ in range(120)]

        # Sprites de preview do menu (evita recriar cada frame)
        self._menu_p1 = Player(0, 0, is_mirror=False, color=COLOR_PLAYER1).get_sprite()
        self._menu_p2 = Player(0, 0, is_mirror=True,  color=COLOR_PLAYER2).get_sprite()

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
                moving=pd.get("moving", False),
                move_dx=pd.get("move_dx", 0.0),
                move_dy=pd.get("move_dy", 0.0),
                move_x_min=pd.get("move_x_min", None),
                move_x_max=pd.get("move_x_max", None),
                move_y_min=pd.get("move_y_min", None),
                move_y_max=pd.get("move_y_max", None),
            )
            for pd in data["platforms"]
        ]

        self.powerups = [
            PowerUp(pu["x"], pu["y"], pu.get("kind", "grow"))
            for pu in data.get("powerups", [])
        ]

        self.spikes = [
            Spike(sp["x"], sp["y"], sp["w"], sp.get("h", 16),
                  sp.get("facing", "up"))
            for sp in data.get("spikes", [])
        ]

        self.lasers = [
            Laser(la["x"], la["y"], la["w"],
                  la.get("on", 90), la.get("off", 90), la.get("offset", 0))
            for la in data.get("lasers", [])
        ]

        ex, ey, ew, eh = data["exit"]
        self.exit_rect  = pygame.Rect(ex, ey, ew, eh)
        self.bg_color   = tuple(data.get("background_color", [15, 15, 35]))
        self.level_name = data.get("name", f"Fase {level_num}")
        self.hint       = data.get("hint", "")
        self.particles.clear()

    def _enter_level(self, level_num, show_intro=True):
        """Carrega a fase e opcionalmente mostra tela de transição."""
        self._load_level(level_num)
        if show_intro:
            self.transition_timer = TRANSITION_FRAMES
            self.state = STATE_TRANSITION
        else:
            self.state = STATE_PLAYING

    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------

    def run(self):
        while True:
            self.clock.tick(FPS)
            self.frame += 1
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
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._enter_level(self.current_level, show_intro=True)

                elif self.state == STATE_TRANSITION:
                    # Qualquer tecla pula a intro
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.transition_timer = 0

                elif self.state == STATE_PLAYING:
                    if event.key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
                        # Ambos pulam simultaneamente
                        self.p1.jump()
                        self.p2.jump()
                    elif event.key == pygame.K_r:
                        self._load_level(self.current_level)
                        self.state = STATE_PLAYING
                    elif event.key == pygame.K_ESCAPE:
                        self.current_level = 1
                        self.lives = 3
                        self._load_level(1)
                        self.state = STATE_MENU

                elif self.state in (STATE_WIN, STATE_GAMEOVER):
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._handle_end_state()

    def _handle_end_state(self):
        if self.state == STATE_WIN:
            if self.current_level < self.MAX_LEVELS:
                self.current_level += 1
                self._enter_level(self.current_level, show_intro=True)
            else:
                # Zerou o jogo → volta ao menu
                self.current_level = 1
                self.lives = 3
                self._load_level(1)
                self.state = STATE_MENU
        elif self.state == STATE_GAMEOVER:
            self.lives = 3
            self._enter_level(self.current_level, show_intro=False)

    # ------------------------------------------------------------------
    # Atualização
    # ------------------------------------------------------------------

    def _update(self):
        # --- Transição de nível ---
        if self.state == STATE_TRANSITION:
            self.transition_timer -= 1
            if self.transition_timer <= 0:
                self.state = STATE_PLAYING
            return

        if self.state != STATE_PLAYING:
            return

        # Flash de morte (contagem regressiva visual)
        if self.death_flash > 0:
            self.death_flash -= 1

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
            pu.update()
            if not pu.collected:
                if (self.p1.rect.colliderect(pu.rect) or
                        self.p2.rect.colliderect(pu.rect)):
                    pu.collect()
                    sx, sy = pu.scale_values
                    # [TRANSFORMAÇÃO] Escala — aplica aos dois jogadores
                    self.p1.apply_scale_powerup(sx, sy, PowerUp.DURATION)
                    self.p2.apply_scale_powerup(sx, sy, PowerUp.DURATION)
                    # Partículas de coleta
                    color = (255, 180, 50) if pu.kind == 'grow' else (100, 220, 255)
                    self.particles.emit_burst(
                        pu.x + pu.size // 2,
                        pu.y + pu.size // 2,
                        color, count=25, speed=4, life=35)

        # Atualiza rotação das plataformas
        for plat in self.platforms:
            plat.update()

        # Atualiza lasers
        for laser in self.lasers:
            laser.update()

        # Partículas do sistema
        self.particles.update()

        # Partículas nos portais de saída (stream contínuo)
        if self.frame % 4 == 0:
            ex = self.exit_rect
            self.particles.emit_stream(
                ex.centerx, ex.bottom, COLOR_EXIT,
                count=1, speed=0.8, life=25, size=2, direction=(0, -1))
            mx = self._mirrored_exit()
            self.particles.emit_stream(
                mx.centerx, mx.bottom, COLOR_EXIT,
                count=1, speed=0.8, life=25, size=2, direction=(0, -1))

        # --- Detecção de morte por obstáculos ---
        hit_hazard = False

        # Espinhos (P1 vs normais, P2 vs espelhados)
        for sp in self.spikes:
            if self.p1.rect.colliderect(sp.rect):
                hit_hazard = True
                break
        if not hit_hazard:
            for sp in self._get_mirrored_spikes():
                if self.p2.rect.colliderect(sp.rect):
                    hit_hazard = True
                    break

        # Lasers ativos (P1 vs normais, P2 vs espelhados)
        if not hit_hazard:
            for la in self.lasers:
                if la.is_active and self.p1.rect.colliderect(la.rect):
                    hit_hazard = True
                    break
            if not hit_hazard:
                for la in self._get_mirrored_lasers():
                    if la.is_active and self.p2.rect.colliderect(la.rect):
                        hit_hazard = True
                        break

        if hit_hazard:
            self.particles.emit_burst(
                int(self.p1.x + self.p1.width / 2),
                int(self.p1.y + self.p1.height / 2),
                (255, 80, 80), count=30, speed=5, life=30)
            self.lives -= 1
            self.death_flash = 15
            if self.lives <= 0:
                self.state = STATE_GAMEOVER
            else:
                self._load_level(self.current_level)
                self.state = STATE_PLAYING
            return

        # Morte por queda fora da tela
        fell = (self.p1.y > SCREEN_HEIGHT + 60 or
                self.p2.y > SCREEN_HEIGHT + 60)
        if fell:
            self.lives -= 1
            self.death_flash = 12
            if self.lives <= 0:
                self.state = STATE_GAMEOVER
            else:
                self._load_level(self.current_level)
                self.state = STATE_PLAYING
            return

        # Vitória — AMBOS P1 e P2 precisam alcançar suas respectivas saídas
        p1_at_exit = self.p1.rect.colliderect(self.exit_rect)
        p2_at_exit = self.p2.rect.colliderect(self._mirrored_exit())
        if p1_at_exit and p2_at_exit:
            self.particles.emit_burst(
                self.exit_rect.centerx, self.exit_rect.centery,
                COLOR_EXIT, count=40, speed=5, life=40)
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

    def _get_mirrored_spikes(self):
        """Gera espinhos espelhados para colisão/desenho do lado de P2."""
        mirrored = []
        for sp in self.spikes:
            mx = int(self._mirror_x(sp.x, sp.w))
            mirrored.append(Spike(mx, sp.y, sp.w, sp.h, sp.facing))
        return mirrored

    def _get_mirrored_lasers(self):
        """Gera lasers espelhados para colisão/desenho do lado de P2."""
        mirrored = []
        for la in self.lasers:
            mx = int(self._mirror_x(la.x, la.w))
            ml = Laser(mx, la.y, la.w, la.on_frames, la.off_frames, 0)
            ml._timer = la._timer  # sincroniza o ciclo
            mirrored.append(ml)
        return mirrored

    # ------------------------------------------------------------------
    # Renderização
    # ------------------------------------------------------------------

    def _draw(self):
        self.screen.fill(self.bg_color)

        if self.state == STATE_MENU:
            self._draw_menu()
        elif self.state == STATE_TRANSITION:
            self._draw_transition()
        elif self.state == STATE_PLAYING:
            self._draw_game()
        elif self.state == STATE_WIN:
            self._draw_game()
            self._draw_overlay("FASE COMPLETA!",
                               "ENTER para continuar", (80, 220, 100))
        elif self.state == STATE_GAMEOVER:
            self._draw_game()
            self._draw_overlay("GAME OVER",
                               "ENTER para tentar de novo", (220, 80, 80))

        # Flash vermelho na morte
        if self.death_flash > 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 50, 50, int(160 * self.death_flash / 12)))
            self.screen.blit(flash, (0, 0))

        pygame.display.flip()

    # --- helpers de desenho -------------------------------------------

    def _draw_background(self):
        """Grade sutil de fundo."""
        gc = tuple(min(c + 6, 255) for c in self.bg_color)
        for x in range(0, SCREEN_WIDTH + 1, 60):
            pygame.draw.line(self.screen, gc, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT + 1, 60):
            pygame.draw.line(self.screen, gc, (0, y), (SCREEN_WIDTH, y))

    def _draw_mirror_line(self):
        """Linha central de espelho com brilho pulsante e tracejado."""
        pulse = 0.6 + 0.4 * math.sin(self.frame * 0.03)
        # Brilho difuso
        glow = pygame.Surface((10, SCREEN_HEIGHT), pygame.SRCALPHA)
        glow.fill((180, 200, 255, int(15 + 15 * pulse)))
        self.screen.blit(glow, (self.mirror_line_x - 5, 0))
        # Tracejado central
        dash = pygame.Surface((2, SCREEN_HEIGHT), pygame.SRCALPHA)
        y = 0
        ca = int(80 + 40 * pulse)
        while y < SCREEN_HEIGHT:
            pygame.draw.line(dash, (220, 230, 255, ca), (0, y), (1, y + 10))
            y += 20
        self.screen.blit(dash, (self.mirror_line_x - 1, 0))

    def _draw_exit_portal(self, rect):
        """Portal de saída com brilho pulsante."""
        pulse = 0.5 + 0.5 * math.sin(self.frame * 0.06)
        # Glow externo
        gs = int(4 + 8 * pulse)
        gr = rect.inflate(gs * 2, gs * 2)
        gsf = pygame.Surface((gr.width, gr.height), pygame.SRCALPHA)
        ga = int(40 + 50 * pulse)
        pygame.draw.rect(gsf,
                         (COLOR_EXIT[0] // 2, COLOR_EXIT[1] // 2,
                          COLOR_EXIT[2] // 2, ga),
                         (0, 0, gr.width, gr.height), border_radius=8)
        self.screen.blit(gsf, gr.topleft)
        # Borda luminosa
        bc = tuple(min(255, int(c + 30 * pulse)) for c in COLOR_EXIT)
        pygame.draw.rect(self.screen, bc, rect, border_radius=5)
        inner = rect.inflate(-4, -4)
        pygame.draw.rect(self.screen, COLOR_EXIT, inner, border_radius=3)
        # Label
        lbl = self.font_small.render("META", True, (20, 40, 20))
        self.screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                               rect.centery - lbl.get_height() // 2))

    # --- telas --------------------------------------------------------

    def _draw_menu(self):
        self.screen.fill((8, 8, 25))

        # Estrelas cintilantes
        for sx, sy, brightness in self.stars:
            twinkle = 0.5 + 0.5 * math.sin(self.frame * 0.02 + sx * 0.1)
            b = int(min(255, 120 * brightness * twinkle))
            pygame.draw.circle(self.screen, (b, b, min(255, b + 40)),
                               (sx, sy), 1)

        # Título com sombra e flutuação
        fy = math.sin(self.frame * 0.025) * 5
        title = self.font_big.render("MIRROR DASH", True, (200, 220, 255))
        shadow = self.font_big.render("MIRROR DASH", True, (40, 50, 80))
        tx = SCREEN_WIDTH // 2 - title.get_width() // 2
        self.screen.blit(shadow, (tx + 3, int(150 + fy) + 3))
        self.screen.blit(title,  (tx,     int(150 + fy)))

        # Subtítulo pulsante
        p = 0.6 + 0.4 * math.sin(self.frame * 0.04)
        sc = (int(100 + 80 * p), int(100 + 80 * p), int(160 + 60 * p))
        sub = self.font_med.render("Pressione ENTER para jogar", True, sc)
        self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 255))

        # Preview dos personagens com bounce
        bounce = abs(math.sin(self.frame * 0.05)) * 8
        px1 = SCREEN_WIDTH // 2 - 80
        px2 = SCREEN_WIDTH // 2 + 48
        py  = int(330 - bounce)
        self.screen.blit(self._menu_p1, (px1, py))
        self.screen.blit(self._menu_p2, (px2, py))

        # Labels P1/P2
        l1 = self.font_small.render("P1", True, COLOR_PLAYER1)
        l2 = self.font_small.render("P2", True, COLOR_PLAYER2)
        self.screen.blit(l1, (px1 + 8, 370))
        self.screen.blit(l2, (px2 + 8, 370))

        # Mini linha de espelho entre os previews
        ml = pygame.Surface((2, 60), pygame.SRCALPHA)
        yy = 0
        while yy < 60:
            pygame.draw.line(ml, (255, 255, 255, 50), (0, yy), (1, yy + 6))
            yy += 14
        self.screen.blit(ml, (SCREEN_WIDTH // 2 - 1, 320))

        # Controles
        controls = [
            ("← →  ou  A D", "Mover"),
            ("W / ESPAÇO",    "Pular"),
            ("R",             "Reiniciar"),
            ("ESC",           "Menu"),
        ]
        ystart = 420
        for i, (key, action) in enumerate(controls):
            kt = self.font_small.render(key, True, (180, 180, 220))
            at = self.font_small.render(f"  {action}", True, (120, 120, 160))
            tw = kt.get_width() + at.get_width()
            cx = SCREEN_WIDTH // 2 - tw // 2
            self.screen.blit(kt, (cx, ystart + i * 26))
            self.screen.blit(at, (cx + kt.get_width(), ystart + i * 26))

        # Dica inferior
        hint = self.font_hint.render(
            "Guie P1 (azul) e seu reflexo P2 (vermelho) até as metas!",
            True, (80, 120, 180))
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 555))

    def _draw_transition(self):
        """Tela de intro da fase com fade in/out."""
        self._draw_background()

        progress = 1.0 - (self.transition_timer / TRANSITION_FRAMES)
        if progress < 0.3:
            alpha = progress / 0.3
        elif progress > 0.7:
            alpha = (1.0 - progress) / 0.3
        else:
            alpha = 1.0
        alpha = max(0.0, min(1.0, alpha))

        # Número da fase
        num = self.font_big.render(
            f"FASE {self.current_level}", True,
            (int(200 * alpha), int(220 * alpha), int(255 * alpha)))
        self.screen.blit(num, (SCREEN_WIDTH // 2 - num.get_width() // 2, 210))

        # Linha decorativa
        lw = int(220 * alpha)
        if lw > 0:
            pygame.draw.line(
                self.screen,
                (int(100 * alpha), int(120 * alpha), int(180 * alpha)),
                (SCREEN_WIDTH // 2 - lw // 2, 280),
                (SCREEN_WIDTH // 2 + lw // 2, 280), 2)

        # Nome da fase
        name = self.font_med.render(
            self.level_name, True,
            (int(150 * alpha), int(170 * alpha), int(220 * alpha)))
        self.screen.blit(name, (SCREEN_WIDTH // 2 - name.get_width() // 2, 300))

        # Hint
        if self.hint:
            h = self.font_hint.render(
                self.hint, True,
                (int(120 * alpha), int(150 * alpha), int(180 * alpha)))
            self.screen.blit(h, (SCREEN_WIDTH // 2 - h.get_width() // 2, 365))

        # Skip hint
        skip = self.font_small.render("ENTER para pular", True, (80, 80, 120))
        self.screen.blit(skip, (SCREEN_WIDTH // 2 - skip.get_width() // 2, 500))

    def _draw_game(self):
        self._draw_background()
        self._draw_mirror_line()

        # Portais de saída
        self._draw_exit_portal(self.exit_rect)
        self._draw_exit_portal(self._mirrored_exit())

        # Plataformas normais e espelhadas
        for plat in self.platforms:
            plat.draw(self.screen)
        for plat in self._get_mirrored_platforms():
            plat.draw(self.screen)

        # Espinhos normais e espelhados
        for sp in self.spikes:
            sp.draw(self.screen)
        for sp in self._get_mirrored_spikes():
            sp.draw(self.screen)

        # Lasers normais e espelhados
        for la in self.lasers:
            la.draw(self.screen, self.frame)
        for la in self._get_mirrored_lasers():
            la.draw(self.screen, self.frame)

        # Power-ups
        for pu in self.powerups:
            pu.draw(self.screen)

        # Partículas (atrás dos jogadores)
        self.particles.draw(self.screen)

        # Jogadores
        self.p1.draw(self.screen)
        self.p2.draw(self.screen)

        # HUD
        scale_timer = self.p1.scale_timer
        scale_max   = PowerUp.DURATION
        scale_kind  = ""
        if self.p1.scale_timer > 0:
            scale_kind = "grow" if self.p1.scale_x > 1.0 else "shrink"
        self.hud.draw(self.screen, self.lives, self.current_level,
                      self.level_name, scale_timer, scale_max, scale_kind)

    def _draw_overlay(self, title_text, subtitle_text, color):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        # Caixa decorativa
        bw, bh = 500, 200
        bx = SCREEN_WIDTH // 2 - bw // 2
        by = SCREEN_HEIGHT // 2 - bh // 2
        box = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(box, (20, 20, 40, 200),
                         (0, 0, bw, bh), border_radius=12)
        pygame.draw.rect(box, (*color, 150),
                         (0, 0, bw, bh), width=2, border_radius=12)
        self.screen.blit(box, (bx, by))

        t = self.font_big.render(title_text,    True, color)
        s = self.font_med.render(subtitle_text, True, (200, 200, 220))
        self.screen.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, by + 40))
        self.screen.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2, by + 120))
