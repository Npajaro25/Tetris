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

# estado interno para evitar repetir jugadas
ultima_jugada = None


def ejecutar_movimiento(col_objetivo, rotaciones):
    global ultima_jugada
    jugada_actual = (col_objetivo, rotaciones)
    if jugada_actual == ultima_jugada:
        return
    ultima_jugada = jugada_actual

    for _ in range(rotaciones):
        pyautogui.press(ROTATE)
        time.sleep(ROT_DELAY)

    columna_actual = 4
    desplazamiento = col_objetivo - columna_actual
    tecla = RIGHT if desplazamiento > 0 else LEFT

    for _ in range(abs(desplazamiento)):
        pyautogui.press(tecla)
        time.sleep(MOVE_DELAY)
    time.sleep(FINAL_DELAY)
    pyautogui.press(DROP)
