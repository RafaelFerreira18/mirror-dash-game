# -*- coding: utf-8 -*-
"""
transforms.py
=============
Transformações geométricas implementadas via matrizes homogêneas 3x3.
Este módulo é a evidência matemática central do projeto Mirror Dash.

Todas as transformações seguem a forma:
    | a  b  tx |
    | c  d  ty |  aplicado a um ponto [x, y, 1]^T
    | 0  0   1 |
"""

import math
import pygame


# ---------------------------------------------------------------------------
# Utilitários matriciais
# ---------------------------------------------------------------------------

def mat_mul(A, B):
    """Multiplica duas matrizes 3x3 (listas de listas)."""
    result = [[0] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                result[i][j] += A[i][k] * B[k][j]
    return result


def apply_matrix(mat, x, y):
    """Aplica uma matriz homogênea 3x3 a um ponto (x, y) e retorna (xn, yn)."""
    xn = mat[0][0] * x + mat[0][1] * y + mat[0][2]
    yn = mat[1][0] * x + mat[1][1] * y + mat[1][2]
    return xn, yn


# ---------------------------------------------------------------------------
# TRANSLAÇÃO
# ---------------------------------------------------------------------------

def translation_matrix(tx, ty):
    """
    Matriz de translação:
        T = | 1  0  tx |
            | 0  1  ty |
            | 0  0   1 |
    """
    return [
        [1, 0, tx],
        [0, 1, ty],
        [0, 0,  1],
    ]


def translate(x, y, tx, ty):
    """[TRANSFORMAÇÃO] Translação — translada ponto (x, y) por (tx, ty)."""
    return apply_matrix(translation_matrix(tx, ty), x, y)


# ---------------------------------------------------------------------------
# ROTAÇÃO
# ---------------------------------------------------------------------------

def rotation_matrix(angle_deg, cx=0, cy=0):
    """
    Matriz de rotação em torno de (cx, cy):
        M = T(cx, cy) · R(θ) · T(-cx, -cy)

    onde R(θ) = | cos θ  -sen θ  0 |
                | sen θ   cos θ  0 |
                |   0       0    1 |
    """
    theta = math.radians(angle_deg)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    T1 = translation_matrix(-cx, -cy)
    R = [
        [ cos_t, -sin_t, 0],
        [ sin_t,  cos_t, 0],
        [     0,      0, 1],
    ]
    T2 = translation_matrix(cx, cy)
    return mat_mul(T2, mat_mul(R, T1))


def rotate_point(x, y, angle_deg, cx=0, cy=0):
    """[TRANSFORMAÇÃO] Rotação — rotaciona ponto (x, y) por angle_deg em torno de (cx, cy)."""
    return apply_matrix(rotation_matrix(angle_deg, cx, cy), x, y)


# ---------------------------------------------------------------------------
# ESCALA
# ---------------------------------------------------------------------------

def scale_matrix(sx, sy, cx=0, cy=0):
    """
    Matriz de escala em torno de (cx, cy):
        M = T(cx, cy) · S(sx, sy) · T(-cx, -cy)

    onde S(sx, sy) = | sx  0  0 |
                     |  0 sy  0 |
                     |  0  0  1 |
    """
    T1 = translation_matrix(-cx, -cy)
    S = [
        [sx,  0, 0],
        [ 0, sy, 0],
        [ 0,  0, 1],
    ]
    T2 = translation_matrix(cx, cy)
    return mat_mul(T2, mat_mul(S, T1))


def scale_point(x, y, sx, sy, cx=0, cy=0):
    """[TRANSFORMAÇÃO] Escala — escala ponto (x, y) pelos fatores (sx, sy) em torno de (cx, cy)."""
    return apply_matrix(scale_matrix(sx, sy, cx, cy), x, y)


def scale_surface(surface, sx, sy):
    """
    [TRANSFORMAÇÃO] Escala — redimensiona um pygame.Surface pelos fatores sx e sy.
    Usa a matriz de escala para calcular as novas dimensões.
    """
    orig_w, orig_h = surface.get_size()
    # Aplica a escala como transformação matricial nas dimensões
    new_w, new_h = scale_point(orig_w, orig_h, sx, sy)
    new_w = max(1, int(new_w))
    new_h = max(1, int(new_h))
    return pygame.transform.scale(surface, (new_w, new_h))


# ---------------------------------------------------------------------------
# REFLEXÃO
# ---------------------------------------------------------------------------

def reflection_matrix(axis='y', ref_line=0):
    """
    Matriz de reflexão (espelhamento) em torno de uma linha.

    axis='y': reflexão em torno de x = ref_line  (espelho vertical)
        M = T(ref_line, 0) · Flip_X · T(-ref_line, 0)
        Flip_X = | -1  0  0 |
                 |  0  1  0 |
                 |  0  0  1 |

    axis='x': reflexão em torno de y = ref_line  (espelho horizontal)
        M = T(0, ref_line) · Flip_Y · T(0, -ref_line)
        Flip_Y = |  1  0  0 |
                 |  0 -1  0 |
                 |  0  0  1 |
    """
    if axis == 'y':
        T1 = translation_matrix(-ref_line, 0)
        Rf = [[-1, 0, 0], [0, 1, 0], [0, 0, 1]]
        T2 = translation_matrix(ref_line, 0)
    else:
        T1 = translation_matrix(0, -ref_line)
        Rf = [[1, 0, 0], [0, -1, 0], [0, 0, 1]]
        T2 = translation_matrix(0, ref_line)
    return mat_mul(T2, mat_mul(Rf, T1))


def reflect_point(x, y, axis='y', ref_line=0):
    """[TRANSFORMAÇÃO] Reflexão — espelha ponto (x, y) em torno do eixo dado."""
    return apply_matrix(reflection_matrix(axis, ref_line), x, y)


def reflect_surface(surface):
    """[TRANSFORMAÇÃO] Reflexão — retorna cópia espelhada horizontalmente de um pygame.Surface."""
    return pygame.transform.flip(surface, True, False)
