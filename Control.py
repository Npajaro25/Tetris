import time
import pyautogui

LEFT = 'left'
RIGHT = 'right'
ROTATE = 'up'
DROP = 'space'

# Delays RÁPIDOS para Blitz (120s) — cada ms cuenta
MOVE_DELAY = 0.04   # 40ms entre movimientos laterales
ROT_DELAY = 0.05    # 50ms entre rotaciones
FINAL_DELAY = 0.05  # 50ms pausa antes del hard drop


def ejecutar_movimiento(col_objetivo, rotaciones, spawn_col=3):
    # Primero rotar
    for _ in range(rotaciones):
        pyautogui.press(ROTATE)
        time.sleep(ROT_DELAY)

    # Calcular desplazamiento desde posición post-rotación
    desplazamiento = col_objetivo - spawn_col
    tecla = RIGHT if desplazamiento > 0 else LEFT

    for _ in range(abs(desplazamiento)):
        pyautogui.press(tecla)
        time.sleep(MOVE_DELAY)

    # Pausa mínima antes de drop
    time.sleep(FINAL_DELAY)
    pyautogui.press(DROP)
