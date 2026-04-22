# -*- coding: utf-8 -*-
"""
level.py
========
Estrutura de dados que representa uma fase carregada do JSON.
O carregamento e a instanciação dos objetos ficam em game.py;
este módulo only define o contêiner LevelData para tipagem explícita.
"""


class LevelData:
    """
    Contêiner leve para os dados brutos de uma fase (após parse do JSON).

    Campos
    ------
    name            : str
    background_color: tuple(r, g, b)
    mirror_line_x   : int
    player_start    : (x, y)
    exit_rect_data  : (x, y, w, h)
    platforms_data  : list[dict]
    powerups_data   : list[dict]
    """

    def __init__(self, raw: dict):
        self.name             = raw.get("name", "Fase")
        self.background_color = tuple(raw.get("background_color", [15, 15, 35]))
        self.mirror_line_x    = raw.get("mirror_line_x", 450)
        self.player_start     = tuple(raw["player_start"])
        self.exit_rect_data   = tuple(raw["exit"])
        self.platforms_data   = raw.get("platforms", [])
        self.powerups_data    = raw.get("powerups", [])
