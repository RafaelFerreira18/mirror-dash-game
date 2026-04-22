# Mirror Dash

Jogo de plataforma 2D onde você controla dois personagens simultaneamente: **P1** (azul) e **P2** (vermelho). P2 é o reflexo espelhado de P1 — tudo que P1 faz, P2 faz ao contrário. Chegue à saída com os dois jogadores para avançar de fase.

## Requisitos

- Python 3.9 ou superior
- pip

## Instalação

1. Clone ou baixe o repositório:
   ```bash
   git clone <url-do-repositorio>
   cd mirror_dash
   ```

2. (Opcional) Crie um ambiente virtual:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/macOS
   source .venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Como rodar

```bash
python main.py
```

## Controles

| Tecla | Ação |
|-------|------|
| `←` / `→` | Mover P1 (P2 se move em espelho) |
| `Espaço` | Pular |
| `R` | Reiniciar fase atual |
| `Esc` | Voltar ao menu |

## Mecânicas

- **Reflexo**: P2 sempre ocupa a posição espelhada de P1 em relação à linha central da tela.
- **Power-ups** (ícones dourados): coletá-los aplica `grow` (dobra o tamanho por ~3 s) ou `shrink` (reduz à metade por ~3 s) nos dois personagens ao mesmo tempo.
- **Vidas**: você começa com 3 vidas. Cair no vazio consome uma vida e reinicia a fase.
- **Fases**: 4 fases disponíveis em `levels/`. Ao completar todas, o jogo retorna ao menu.

## Estrutura do projeto

```
mirror_dash/
├── main.py          # Ponto de entrada
├── game.py          # Loop principal e gerenciamento de estados
├── player.py        # Lógica dos personagens
├── platform.py      # Plataformas
├── powerup.py       # Itens coletáveis
├── hud.py           # Interface (vidas, fase)
├── transforms.py    # Funções de transformação matricial (reflexão, escala, translação)
├── settings.py      # Constantes globais
├── requirements.txt
└── levels/
    ├── level1.json
    ├── level2.json
    ├── level3.json
    └── level4.json
```
