import time
import pyautogui

LEFT = 'left'
RIGHT = 'right'
ROTATE = 'up'
DROP = 'space'

# Velocidad de acciones
MOVE_DELAY = 0.03
ROT_DELAY = 0.05
FINAL_DELAY = 0.08


def ejecutar_movimiento(col_objetivo, rotaciones, spawn_col=3):
    # Primero rotar — esto cambia la posición de la pieza en el juego
    for _ in range(rotaciones):
        pyautogui.press(ROTATE)
        time.sleep(ROT_DELAY)

    # spawn_col indica dónde está la pieza DESPUÉS de rotar
    # (ej: I vertical está en col 5, no en col 3)
    desplazamiento = col_objetivo - spawn_col
    tecla = RIGHT if desplazamiento > 0 else LEFT

    for _ in range(abs(desplazamiento)):
        pyautogui.press(tecla)
        time.sleep(MOVE_DELAY)
    time.sleep(FINAL_DELAY)
    pyautogui.press(DROP)
