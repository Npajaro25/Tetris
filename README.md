# 🎮 Tetris AI Agent

Proyecto de Sistemas Inteligentes — **Agente autónomo que juega Tetris** usando visión por computadora y heurísticas de IA.

El agente captura la pantalla del juego [TETR.IO](https://tetr.io), detecta el estado del tablero en tiempo real, calcula la mejor jugada usando heurísticas optimizadas, y ejecuta los movimientos automáticamente.

## 📋 Requisitos

```bash
pip install opencv-python numpy mss pyautogui
```

- **Python 3.10+**
- Un juego de Tetris visible en pantalla (probado con [TETR.IO](https://tetr.io))

## 🚀 Uso

```bash
python main.py
```

1. Tienes **5 segundos** para enfocar la ventana del juego
2. Selecciona el **tablero de juego** (solo las 10 columnas × 20 filas, sin HOLD/NEXT/bordes)
3. Presiona **SPACE** o **ENTER** para confirmar
4. El agente comienza a jugar automáticamente

> **Tip**: Selecciona el ROI ligeramente por dentro de los bordes del tablero. El sistema recorta 3% automáticamente, pero entre más preciso sea tu recorte, mejor será la detección.

## 🏗️ Arquitectura

```
Tetris/
├── Main.py          # Loop principal del agente
├── Ambiente.py      # Percepción: captura de pantalla + detección del tablero
├── Agente.py        # Interfaz entre percepción y modelo de IA
├── Control.py       # Actuador: envía teclas al juego (pyautogui)
└── Model/
    ├── IA.py        # Motor de decisiones: evalúa todas las posiciones/rotaciones
    ├── Grid.py      # Simulación del tablero + funciones heurísticas
    └── Pieces.py    # Definición de las 7 piezas de Tetris y sus rotaciones
```

### Flujo de ejecución

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Ambiente │────▶│ Agente  │────▶│   IA    │────▶│ Control │
│ (visión) │     │(interfaz)│    │(decisión)│    │ (teclas) │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
    │                                                 │
    │           Captura pantalla                      │
    │◀────────────────────────────────────────────────│
    │           Espera 0.4s y repite                  │
```

## 🧠 IA — Heurísticas

El agente evalúa **TODAS** las posiciones y rotaciones posibles para cada pieza y elige la que maximiza una función de puntuación con 5 heurísticas:

| Heurística | Peso | Efecto |
|---|---|---|
| **Altura agregada** | −0.51 | Penaliza tableros altos (suma de alturas de las 10 columnas) |
| **Líneas completadas** | +8.00 | Fuerte recompensa por completar filas horizontales |
| **Huecos** | −0.80 | Penaliza espacios vacíos debajo de bloques |
| **Bumpiness** | −0.30 | Penaliza diferencias de altura entre columnas adyacentes |
| **Altura máxima** | −1.50 | Penaliza fuertemente la columna más alta (anti-torres) |

La simulación **elimina líneas completas** antes de evaluar, dando una representación precisa del estado resultante.

### Desempate por centro

Cuando dos posiciones tienen puntuación idéntica, se prefiere la más cercana al **centro del tablero** (columna 4.5), evitando sesgo hacia los extremos.

## 👁️ Percepción — Detección del tablero

### Lectura doble (anti-pieza fantasma)

El tablero se lee **DOS veces** con 0.15s de diferencia. Solo se mantienen las celdas que son `1` en ambas lecturas:

- **Bloques colocados** → no se mueven → aparecen en ambas lecturas ✅
- **Pieza cayendo** → se mueve → diferente entre lecturas → filtrada ❌

### Procesamiento de imagen

- Convierte a **HSV** y analiza el centro (50%) de cada celda
- Umbrales: **Saturación > 70** y **Valor > 70** para filtrar fondo oscuro
- Recorte automático de **3%** en cada borde para excluir bordes del ROI
- Las primeras 4 filas se ignoran (zona de spawn)

## ⌨️ Control — Ejecución de movimientos

El sistema calcula el `spawn_col` después de aplicar la rotación elegida (el SRS de Tetris desplaza las piezas al rotar). El desplazamiento se calcula como:

```
desplazamiento = col_objetivo − spawn_col
```

Teclas: `↑` (rotar), `←`/`→` (mover), `SPACE` (hard drop).

## 🛑 Detección de Game Over

Si el tablero se lee como **todo vacío** durante 30 ciclos consecutivos, el agente asume game over y se detiene automáticamente.

## 👥 Equipo

Proyecto para la asignatura de **Sistemas Inteligentes** — Universidad Nacional de Colombia.
