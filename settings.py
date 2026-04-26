# -*- coding: utf-8 -*-
SCREEN_WIDTH  = 900
SCREEN_HEIGHT = 600
FPS           = 60
TITLE         = "Mirror Dash"

GRAVITY       = 0.5
JUMP_FORCE    = -13
PLAYER_SPEED  = 4

COLOR_BG          = (15, 15, 35)
COLOR_PLAYER1     = (80, 180, 255)
COLOR_PLAYER2     = (255, 100, 100)
COLOR_PLATFORM    = (60, 200, 100)
COLOR_PLATFORM_P1 = (70, 140, 220)
COLOR_PLATFORM_P2 = (220, 90, 90)
COLOR_POWERUP     = (255, 220, 50)
COLOR_EXIT        = (200, 255, 150)
COLOR_MIRROR_LINE = (255, 255, 255, 80)

STATE_MENU       = "menu"
STATE_PLAYING    = "playing"
STATE_WIN        = "win"
STATE_GAMEOVER   = "gameover"
STATE_TRANSITION = "transition"

TRANSITION_FRAMES = 120   # ~2 s a 60 fps
