# Mirror Dash — Documentação do Projeto

## Visão Geral

**Mirror Dash** é um jogo de plataforma 2D desenvolvido em Python com [pygame](https://www.pygame.org/). O jogador controla dois personagens simultaneamente: **P1** (azul) e **P2** (vermelho). P2 é o reflexo espelhado de P1 em relação à linha central da tela — todo movimento de P1 é replicado inversamente em P2. O objetivo é guiar os dois personagens até a saída de cada fase.

O projeto foi desenvolvido como trabalho de **Computação Gráfica**, com foco na implementação explícita de transformações geométricas via **matrizes homogêneas 3×3**.

---

## Estrutura de Arquivos

```
mirror_dash/
├── main.py           # Ponto de entrada: instancia e roda o Game
├── game.py           # Loop principal, gerenciamento de estados e fases
├── player.py         # Lógica e renderização dos personagens P1 e P2
├── platform.py       # Plataformas estáticas e giratórias
├── powerup.py        # Itens coletáveis (grow / shrink)
├── hud.py            # Interface (vidas, fase, controles)
├── level.py          # Contêiner de dados de fase (LevelData)
├── transforms.py     # Transformações geométricas (núcleo matemático)
├── settings.py       # Constantes globais (resolução, cores, física)
├── requirements.txt  # Dependências (pygame >= 2.1.0)
└── levels/
    ├── level1.json   # Tutorial — plataformas estáticas
    ├── level2.json   # Fase 2
    ├── level3.json   # Fase 3
    └── level4.json   # Fase 4
```

---

## Como Executar

**Requisitos:** Python 3.9+ e pip.

```bash
# 1. (Opcional) Ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/macOS

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Rodar o jogo
python main.py
```

---

## Controles

| Tecla | Ação |
|---|---|
| `←` / `→` ou `A` / `D` | Mover P1 horizontalmente (P2 se move em espelho) |
| `W` / `Espaço` | Pular |
| `R` | Reiniciar a fase atual |
| `Esc` | Voltar ao menu |

---

## Mecânicas de Jogo

### Reflexo (P2)
P2 nunca é controlado diretamente. A cada frame, sua posição X é calculada como a reflexão da posição de P1 em torno da `mirror_line_x`:

$$x_{P2} = 2 \cdot mirror\_line\_x - x_{P1} - largura$$

Isso é implementado via `reflect_point()` em `transforms.py`.

### Vidas e Game Over
O jogador começa com **3 vidas**. Ao cair fora da tela, perde uma vida e reinicia a fase. Com zero vidas, vai para a tela de Game Over.

### Power-ups
Itens dourados flutuantes com dois tipos:

| Tipo | Ícone | Efeito | Duração |
|---|---|---|---|
| `grow` | `+` (laranja) | Dobra o tamanho dos dois personagens (`sx=2.0, sy=2.0`) | ~3 s |
| `shrink` | `−` (ciano) | Reduz à metade (`sx=0.5, sy=0.5`) | ~3 s |

Coletá-los aplica a escala simultaneamente em P1 e P2.

### Plataformas Giratórias
Algumas plataformas giram em torno do próprio centro a cada frame (definido no JSON via `"rotating": true` e `"speed"`). A colisão usa os cantos rotacionados reais, calculados com `rotate_point()`.

---

## Transformações Geométricas (`transforms.py`)

Este é o módulo central do trabalho. Todas as transformações são implementadas como **matrizes homogêneas 3×3**, sem uso de funções prontas de biblioteca.

### Forma Geral

$$M = \begin{pmatrix} a & b & t_x \\ c & d & t_y \\ 0 & 0 & 1 \end{pmatrix}, \quad \begin{pmatrix} x' \\ y' \\ 1 \end{pmatrix} = M \cdot \begin{pmatrix} x \\ y \\ 1 \end{pmatrix}$$

### Translação

$$T(t_x, t_y) = \begin{pmatrix} 1 & 0 & t_x \\ 0 & 1 & t_y \\ 0 & 0 & 1 \end{pmatrix}$$

**Uso no projeto:** movimento horizontal/vertical de P1 a cada frame (`player.move()`).

### Rotação em torno de um ponto $(c_x, c_y)$

$$M_{rot} = T(c_x, c_y) \cdot R(\theta) \cdot T(-c_x, -c_y)$$

$$R(\theta) = \begin{pmatrix} \cos\theta & -\sin\theta & 0 \\ \sin\theta & \cos\theta & 0 \\ 0 & 0 & 1 \end{pmatrix}$$

**Uso no projeto:** plataformas giratórias — os quatro cantos são rotacionados a cada frame para colisão e renderização precisas.

### Escala em torno de um ponto $(c_x, c_y)$

$$M_{scale} = T(c_x, c_y) \cdot S(s_x, s_y) \cdot T(-c_x, -c_y)$$

$$S(s_x, s_y) = \begin{pmatrix} s_x & 0 & 0 \\ 0 & s_y & 0 \\ 0 & 0 & 1 \end{pmatrix}$$

**Uso no projeto:** power-ups aplicam escala nos sprites de P1 e P2 (`apply_scale_powerup()`).

### Reflexão (eixo vertical em $x = m$)

$$M_{ref} = \begin{pmatrix} -1 & 0 & 2m \\ 0 & 1 & 0 \\ 0 & 0 & 1 \end{pmatrix}$$

**Uso no projeto:** mecânica central do jogo — posição X de P2 é sempre o reflexo de P1 em torno de `mirror_line_x`.

### Reflexão de Superfície (`reflect_surface`)
Além da reflexão de ponto, `transforms.py` também espelha horizontalmente o sprite de P2 usando `pygame.transform.flip`, garantindo que o personagem fique visualmente invertido.

---

## Módulos

### `game.py` — Gerenciador Principal
Controla o loop do jogo (60 FPS) e a máquina de estados:

```
menu → playing → win / gameover → próxima fase ou menu
```

Responsabilidades:
- Carregar fases a partir dos JSONs em `levels/`
- Aplicar reflexão de P2 a cada frame
- Detectar colisões (plataformas, saída, power-ups, queda)
- Renderizar todos os objetos e a linha espelho

### `player.py` — Personagem
- Física simples: gravidade constante + força de pulo
- **Coyote time**: permite pular por até 6 frames após sair da borda de uma plataforma
- **Jump buffer**: registra intenção de pulo por até 8 frames antes de pousar
- Sprite gerado proceduralmente com `pygame.draw` (sem assets externos)

### `platform.py` — Plataforma
- Plataformas estáticas: rect simples do pygame
- Plataformas giratórias: acumulam ângulo a cada frame; colisão usa SAT (Separating Axis Theorem) simplificado sobre os cantos rotacionados

### `powerup.py` — Item Coletável
- Animação de flutuação vertical suave
- Ao coletado, dispara `apply_scale_powerup()` nos dois jogadores

### `hud.py` — Interface
- Exibe vidas (canto superior esquerdo), fase (centro superior) e teclas de controle (rodapé)

### `settings.py` — Constantes Globais
| Constante | Valor | Descrição |
|---|---|---|
| `SCREEN_WIDTH` | 900 | Largura da janela (px) |
| `SCREEN_HEIGHT` | 600 | Altura da janela (px) |
| `FPS` | 60 | Taxa de quadros |
| `GRAVITY` | 0.5 | Aceleração gravitacional (px/frame²) |
| `JUMP_FORCE` | -13 | Velocidade inicial do pulo (px/frame) |
| `PLAYER_SPEED` | 4 | Velocidade horizontal (px/frame) |

---

## Fases (`levels/*.json`)

Cada fase é um arquivo JSON com o esquema:

```json
{
  "name": "Nome da Fase",
  "background_color": [r, g, b],
  "mirror_line_x": 450,
  "player_start": [x, y],
  "exit": [x, y, largura, altura],
  "platforms": [
    { "x": 0, "y": 550, "w": 900, "h": 20, "rotating": false },
    { "x": 200, "y": 400, "w": 100, "h": 15, "rotating": true, "speed": 1.5 }
  ],
  "powerups": [
    { "x": 300, "y": 350, "kind": "grow" }
  ]
}
```

| Campo | Descrição |
|---|---|
| `mirror_line_x` | Posição X da linha de reflexão |
| `player_start` | Posição inicial de P1 (P2 é calculado automaticamente) |
| `exit` | Retângulo da saída que ambos os jogadores devem alcançar |
| `rotating` | Se `true`, a plataforma gira em torno do próprio centro |
| `speed` | Velocidade de rotação em graus/frame |
| `kind` | Tipo do power-up: `"grow"` ou `"shrink"` |

---

## Dependências

| Pacote | Versão mínima | Uso |
|---|---|---|
| `pygame` | 2.1.0 | Janela, eventos, renderização, áudio |

---

## Diagrama de Estados

```
         ┌─────────┐
         │  MENU   │ ◄─────────────────────┐
         └────┬────┘                       │
              │ Enter / Space              │ Esc
              ▼                            │
         ┌──────────┐   cai / tempo  ┌─────┴──────┐
         │ PLAYING  │ ──────────────► │  GAMEOVER  │
         └────┬─────┘                └────────────┘
              │ P1 e P2 na saída
              ▼
         ┌──────────────┐
         │  TRANSITION  │ (animação de vitória)
         └──────┬───────┘
                │ próxima fase existe?
       ┌────────┴────────┐
       │ Sim             │ Não
       ▼                 ▼
  ┌─────────┐       ┌─────────┐
  │ PLAYING │       │   WIN   │ → Menu
  │(fase+1) │       └─────────┘
  └─────────┘
```
