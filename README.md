# 🎮 Tetris AI Agent

Proyecto final de Sistemas Inteligentes — **Agente autónomo que juega TETR.IO Blitz** usando visión por computadora, heurísticas ofensivas basadas en N-Depth Beam Search Lookahead, y estrategia de Hold dinámica ("Soft I-Trap").

El agente captura la pantalla para jugar [TETR.IO](https://tetr.io) en tiempo real. Utiliza OpenCV para extraer el estado de la matriz, la cola completa de NEXT (3 piezas) y el slot HOLD, procesando la posición matemáticamente perfecta hasta 3 niveles hacia el futuro para generar combos y Tetrises gigantes a velocidad sobrehumana.

> **Récord Actual: 60,000+ pts en TETR.IO Blitz (2 Minutos)**

## 👥 Equipo de Desarrollo
- Nicolas Pajaro Sanchez
- Juan Camilo Lopez Bustos
- Brayan Alejandro Muñoz Pérez

## ⚙️ Configuración Obligatoria TETR.IO
Dado que el agente lee píxeles brutos de la pantalla, es vital minimizar el "ruido visual" (partículas, brillos, alertas) para evitar *ghost blocks* (bloques fantasma). Configura TETR.IO así:

1. **Video & Interface -> Graphics**: `Minimal` (Apaga efectos de partículas y destellos).
2. **Video & Interface -> Render at low resolution**: `OFF` (Evita pixelación errática de los colores).
3. **Gameplay -> Warn me when the game is not focused**: `OFF` (Evita que el letrero rojo de alerta tape el tablero cuando el agente asume el control del teclado).

## 📋 Requisitos e Instalación

```bash
pip install opencv-python numpy mss pyautogui
```
- **Python 3.10+**

## 🚀 Uso / Calibración Inicial

```bash
python main.py
```

1. Asegúrate de tener TETR.IO visible y limpio en pantalla.
2. La terminal te dará **5 segundos** de gracia para enfocar la ventana del juego de Tetris.
3. Arrastra y selecciona con el mouse el **tablero de juego**, la **cola NEXT** y la **caja HOLD**.
4. Presiona **SPACE** o **ENTER** para confirmar cada recorte (Guarda automáticamente las coordenadas en `roi_config.json` para tus futuras partidas si no mueves la ventana).
5. ¡El agente arranca a jugar solo a máxima velocidad!

## 🏗️ Arquitectura del Sistema

```text
Tetris/
├── Main.py              # Orquestador: ciclo principal y timer estricto Blitz
├── Ambiente.py          # Percepción (OpenCV): extracción de tablero, NEXT y HOLD
├── Agente.py            # Estratega: encolado dinámico y evaluación de HOLD/NEXT
├── Control.py           # Actuador (pyautogui): inputs de extrema baja latencia
├── debug_vision.py      # Diagnóstico visual de la captura de OpenCV en tiempo real
├── roi_config.json      # Cache de coordenadas screen-space
└── Model/
    ├── IA.py            # Motor algorítmico: N-Depth Recursive Beam Search
    ├── Grid.py          # Físicas y Heurísticas ofensivas "El-Tetris" modificadas
    └── Pieces.py        # Super Rotation System (SRS) y mapeo matricial
```

## 🧠 Algoritmos Base y Optimizaciones

### N-Depth Recursive Beam Search (K=3)
El motor original revisaba `~1640` tableros para una profundidad de 2 piezas (Pieza Actual + 1 Next). Reemplazado por un motor N-Depth Recursivo con límite topológico:
1. Evalúa las 40 opciones de la pieza en mano.
2. Filtra dinámicamente el **Top 3 de mejores decisiones (K=3)**.
3. Ramifica el futuro evaluando las siguientes piezas de la cola (NEXT) *solo* a través de esas 3 ramas maestras cardinales.
**Resultado:** Se analizan apenas `~520` tableros por frame (Profundidad de 3 piezas), dándole a un PC de ofimática (60Hz) el mismo nivel de inteligencia profunda y un `%75` menos de carga térmica en la CPU.

### "Soft I-Trap" Dinámico
Para solucionar el histórico bug matemático donde la IA bloqueaba su HOLD eternamente esperando un pozo ideal guardando la pieza `I`:
Se recompensa lógicamente cualquier estado prospectivo del tablero que termine devolviendo la pieza `I` a la recámara HOLD con **+500 puntos**. Esto induce de manera heurística a la máquina a "guardar mágicamente" el palo largo por instinto para construir Tetrises, pero la libera conductualmente si jugar dicha pieza saca de golpe un Tetris real (+3000 puntos heurísticos) o limpia lo justo para sobrevivir.

### Muerte Súbita (120s Blitz Timer)
Al acabar una partida de competición en TETR.IO Blitz (120 segundos temporizados), las animaciones masivas de "TIME UP" y el menú final generan parpadeos erráticos en OpenCV que simulan bloques fantasma. Como método de defensa anti-alucinaciones extremo, `Main.py` incopora una variable centinela de hardware que paraliza las hebras de ejecución tras `122 segundos` contados desde la primera pieza. Esto congela totalmente al bot y te permite capturar inmaculadamente tu puntuación final.

### Anti-Ghosting y APM de Alta Frecuencia
- Un rastreo Flood-Fill en cascada asegurando *8-conectividad* desde el ras de suelo del tablero erradica y limpia a los bloques transitorios de caídas aéreas que corrompen el mapeo 10x20.
- El límite crudo de velocidad latente del marco virtual (SLEEP del orquestador tras hard drop) fue compactado de `350ms` a una cifra letal de `280ms`. 
- Armado con un `MOVE_DELAY` ultrarrápido inyectado vía direct-input de `5ms` por milímetro de desplazamiento transversal, el Agente zafa evadiendo limpiamente la catastrófica *trampa gravitacional (20G Drop Delay)* acaecida estrepitosamente en el fragor de los últimos instantes (Time < 15s).

---
🎓 **Desarrollado en - Universidad Nacional de Colombia**
