import time
import pyautogui

LEFT = 'left'
RIGHT = 'right'
ROTATE = 'up'
DROP = 'space'
HOLD = 'c'

# CRÍTICO: pyautogui agrega PAUSE=0.1s a CADA tecla por defecto
pyautogui.PAUSE = 0

# Busy-wait de alta resolución para evadir el redondeo de 15.6ms de Windows en time.sleep()
def hrd_sleep(duration):
    start = time.perf_counter()
    while time.perf_counter() - start < duration:
        pass

# Delays precisos para evadir que la pieza caiga antes de llegar a los laterales
MOVE_DELAY = 0.015   # 15ms entre movimientos laterales
ROT_DELAY = 0.020    # 20ms entre rotaciones
FINAL_DELAY = 0.020  # 20ms pausa antes del hard drop
HOLD_DELAY = 0.030   # 30ms después de hold para que TETR.IO procese

def _secure_press(key, press_duration=0.018):
    """
    Mantener la tecla 18ms garantiza al menos 1 frame de registro en el navegador de TETR.IO (60FPS = 16.6ms),
    lo suficientemente rápido para que la gravedad de nivel 6+ no alcance a la pieza.
    """
    pyautogui.keyDown(key)
    hrd_sleep(press_duration)
    pyautogui.keyUp(key)

def ejecutar_movimiento(col_objetivo, rotaciones, spawn_col=3):
    # Primero rotar
    for _ in range(rotaciones):
        _secure_press(ROTATE)
        hrd_sleep(ROT_DELAY)

    # Calcular desplazamiento desde posición post-rotación
    desplazamiento = col_objetivo - spawn_col
    tecla = RIGHT if desplazamiento > 0 else LEFT

    for _ in range(abs(desplazamiento)):
        _secure_press(tecla)
        hrd_sleep(MOVE_DELAY)

    # Pausa mínima antes de drop
    hrd_sleep(FINAL_DELAY)
    _secure_press(DROP)
    
    # DELAY VITAL: El "Hard Drop" en TETR.IO genera un flash brillante / onda expansiva.
    # 0.05s es suficiente para que la pieza se solidifique visualmente.
    hrd_sleep(0.05)


def ejecutar_hold():
    """Presiona la tecla correspondiente para hacer Hold swap."""
    _secure_press(HOLD, press_duration=0.04) # Un poco más para el HOLD que es vital
    hrd_sleep(HOLD_DELAY)
