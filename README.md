# 🎮 Tetris AI Agent

Proyecto de Sistemas Inteligentes — **Agente autónomo que juega TETR.IO Blitz** usando visión por computadora, heurísticas ofensivas con lookahead, y estrategia de Hold inteligente.

El agente captura la pantalla del juego [TETR.IO](https://tetr.io), detecta el estado del tablero en tiempo real (incluyendo la cola NEXT y el slot HOLD), calcula la mejor jugada usando un motor de búsqueda con lookahead de 2 piezas, y ejecuta los movimientos automáticamente.

> **Record actual: ~60,000 pts en TETR.IO Blitz (2 min)**

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
3. Selecciona la **cola NEXT** (las 5 piezas siguientes)
4. Selecciona la **caja HOLD**
5. Presiona **SPACE** o **ENTER** para confirmar cada selección
6. El agente comienza a jugar automáticamente

> **Tip**: Selecciona los ROIs ligeramente por dentro de los bordes. El sistema recorta 3% automáticamente, pero entre más preciso sea tu recorte, mejor será la detección. Los ROIs se guardan en `roi_config.json` para uso futuro.

## 🏗️ Arquitectura

```
Tetris/
├── Main.py              # Loop principal del agente + game-over detection
├── Ambiente.py          # Percepción: tablero + NEXT queue + HOLD (visión)
├── Agente.py            # Cerebro: lookahead + estrategia Hold ofensiva
├── Control.py           # Actuador: envía teclas al juego (pyautogui)
├── debug_vision.py      # Herramienta de diagnóstico visual en tiempo real
├── roi_config.json      # ROIs guardados (tablero, NEXT, HOLD)
└── Model/
    ├── IA.py            # Motor de búsqueda: evalúa posiciones con lookahead
    ├── Grid.py          # Simulación del tablero + heurísticas ofensivas
    └── Pieces.py        # Definición de las 7 piezas de Tetris (SRS)
```

### Flujo de ejecución

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Ambiente  │────▶│  Agente   │────▶│    IA    │────▶│ Control  │
│ (visión)  │     │(lookahead)│    │(búsqueda) │    │ (teclas)  │
└──────────┘     │  + Hold   │     └──────────┘     └──────────┘
    │            └──────────┘                            │
    │         Captura pantalla + NEXT                    │
    │◀──────────────────────────────────────────────────│
    │         Espera 0.35s y repite                      │
```

## 🧠 Motor de Decisiones

### Lookahead de 2 piezas

El agente no solo evalúa la pieza actual, sino que simula **todas las combinaciones** de la pieza actual + la siguiente pieza de la cola NEXT:

1. Para cada posición posible de la pieza actual → simula colocarla
2. Sobre el tablero resultante → evalúa todas las posiciones de la pieza siguiente
3. La puntuación final = mejor resultado combinado de ambas piezas

Esto permite jugadas que parecen subóptimas ahora pero habilitan Tetrises en el turno siguiente.

> **Rendimiento**: El lookahead de 2 piezas ejecuta en **< 20ms**, muy por debajo del presupuesto de 350ms por ciclo.

### Estrategia de Hold ofensiva (I-Trap)

El sistema de Hold implementa la estrategia **"I-Trap"** optimizada para maximizar Tetrises:

| Regla | Comportamiento |
|---|---|
| **Guardar I** | Si llega una pieza I y no hay oportunidad de Tetris, se guarda en HOLD |
| **Bloquear I** | Una I en el HOLD solo sale si puede hacer un Tetris (+1000 pts) |
| **Hold vacío** | Compara jugar la actual vs jugar la NEXT (guardando la actual) |
| **Hold ocupado** | Compara jugar la actual vs jugar la pieza guardada |
| **Anti-umbral** | Requiere ventaja de +5 pts para activar Hold (evita swaps innecesarios) |

La lógica incluye protección contra **Timeline Schism**: si la siguiente pieza es I y va a ser robada para el HOLD, el lookahead no la cuenta como disponible.

### Detección de cola NEXT

El agente detecta las **3 primeras piezas** de la cola NEXT en cada frame usando análisis de color HSV:

- Divide la región NEXT en 5 segmentos verticales
- Para cada segmento, analiza los píxeles saturados del centro
- Clasifica por **mediana de Hue**: I(cyan), T(púrpura), S(verde), Z(rojo), O(amarillo), L(naranja), J(azul)

## 📊 Heurísticas Ofensivas (El-Tetris B2B)

El sistema combinado evalúa con dos componentes:

### Base (construcción plana)

| Feature | Peso | Efecto |
|---|---|---|
| Altura agregada (col 0-8) | −51.0 | Mantener el tablero bajo |
| Bumpiness (col 0-8) | −18.4 | Superficie uniforme |
| Huecos (col 0-8) | −35.6 | Penalizar espacios vacíos |

### Ofensiva (maximizar puntuación)

| Feature | Peso | Efecto |
|---|---|---|
| **Tetris (4 líneas)** | +3,000 | Recompensa masiva por limpiar 4 líneas |
| Quemar líneas (1-3) | −100/línea | Castigo por desperdiciar líneas sin Tetris |
| Modo pánico (altura > 14) | +500/línea | Sobrevivir limpiando cualquier línea |
| **Pozo col 9 tapado** | −500/bloque | Castigo severo por bloquear el pozo de Tetrises |
| Rango de altura | −100 | Forzar superficie plana entre col 0-8 |
| Huecos | −500/hueco | Castigo brutal contra huecos |

> La columna 9 se excluye de todos los cálculos espaciales — se reserva como **pozo para Tetrises**.

### Desempate por centro

Cuando dos posiciones tienen puntuación idéntica, se prefiere la más cercana al **centro del tablero** (columna 4.5), evitando sesgo hacia los extremos.

## 👁️ Percepción — Visión por Computadora

### Lectura doble (anti-pieza fantasma)

El tablero se lee **DOS veces** con 0.15s de diferencia. Solo se mantienen las celdas que son `1` en ambas lecturas:

- **Bloques colocados** → no se mueven → aparecen en ambas lecturas 
- **Pieza cayendo** → se desplaza → diferente entre lecturas → filtrada 

### Flood-Fill dinámico con 8-conectividad

Después de la lectura doble, se aplica un **flood-fill desde la fila más baja con bloques** para eliminar cualquier artefacto residual (pieza cayendo que no se movió, texto UI, partículas):

```
Versión   Problema                           Solución
v1        Flood-Fill desde Row 19 fija       → Fallaba durante line clears (Row 19 vacía)
v2        Wipe filas 0-3 estáticas           → Fallaba a alta velocidad (pieza en filas 4-7)
v3      Flood-Fill dinámico desde piso     → Funciona siempre
```

- **Semilla dinámica**: Busca la fila ocupada más baja del tablero (no hardcoded)
- **8-conectividad**: Incluye conexiones diagonales — necesario porque piezas S/Z crean adyacencias diagonales que 4-conectividad descartaría erróneamente
- **Resultado**: Solo sobreviven bloques conectados al "piso" del stack

### Procesamiento de celdas

- Convierte a **HSV** y analiza el centro (50%) de cada celda
- Umbrales: **Saturación > 120** y **Valor > 120** (filtra fondo, texto semi-transparente y partículas)
- Recorte automático de **3%** en cada borde para excluir bordes del ROI

## ⌨️ Control — Ejecución de movimientos

El sistema calcula el `spawn_col` después de aplicar la rotación elegida (el SRS de Tetris desplaza las piezas al rotar). El desplazamiento se calcula como:

```
desplazamiento = col_objetivo − spawn_col
```

Teclas: `↑` (rotar), `←`/`→` (mover), `SPACE` (hard drop), `c` (hold).

**Timing**: Cada ciclo completo (percepción → decisión → ejecución → espera) tarda **~0.35s**, permitiendo ~170 piezas en una partida de 2 minutos.

## 🛑 Detección de Game Over

El sistema distingue entre tableros vacíos "normales" (antes de que el juego empiece o durante line clears) y el verdadero game over:

1. **Antes del juego**: Tablero vacío → espera pacientemente (no juega)
2. **Durante el juego**: Tablero vacío → incrementa `stale_count`
3. **8 lecturas vacías consecutivas** (~3 segundos) → asume game over y detiene el agente

## 🔧 Diagnóstico Visual — `debug_vision.py`

Herramienta de diagnóstico en tiempo real que muestra exactamente lo que la IA "ve":

```bash
python debug_vision.py
```

Muestra una ventana con:

- **Tablero**: Cada celda resaltada en verde si se detectó como bloque, con valores S/V
- **Cola NEXT**: Las 3 primeras piezas identificadas por color con su valor Hue
- **Slot HOLD**: Pieza guardada identificada por color
- **Contador de bloques**: Total de celdas detectadas como ocupadas

Además, durante el juego el agente guarda **capturas de pantalla cada 10 segundos** como `debug_board_*.png` para análisis post-mortem.

> **Tip**: Ejecuta `debug_vision.py` en paralelo con el juego para verificar que la detección es correcta antes de activar el agente.

## 👥 Equipo

Proyecto para la asignatura de **Sistemas Inteligentes** — Universidad Nacional de Colombia.
