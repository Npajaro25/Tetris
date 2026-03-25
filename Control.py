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

# Delays ultra-rápidos para compensar el lag inherente de PyAutoGUI en Windows (~15ms por llamada)
# Esto evita que excedamos el "Lock Delay" (500ms) de TETR.IO en niveles de gravedad máxima
MOVE_DELAY = 0.002   # 2ms entre movimientos
ROT_DELAY = 0.005    # 5ms entre rotaciones

# ========== PACEMAKER (Control de APM) ========== #
# En lugar de pausar el bot DESPUÉS de tirar la ficha, lo pausamos en el aire.
# Buscando el "Time Perfect 120s": 130ms era muy lento (79k pts) y 80ms es suicida (>Lvl 11 rápido).
# 100ms es el medio de oro empírico para sangrar el tiempo justo antes del Game Over por gravedad.
FINAL_DELAY = 0.100  # 100ms pausa antes del drop (Equilibrio de supervivencia perfecto)

HOLD_DELAY = 0.020   # 20ms después de hold

def _secure_press(key, press_duration=0.030):
    """
    Mantener la tecla 30ms asegura registro rápido sin comerse el timer de Lock Delay,
    mientras cubre 2 frames completos en 60Hz para evitar inputs droppeados.
    """
    pyautogui.keyDown(key)
    hrd_sleep(press_duration)
    pyautogui.keyUp(key)

def ejecutar_movimiento(col_objetivo, rotaciones, spawn_col=3, width_pieza=1):
    # Primero rotar
    for _ in range(rotaciones):
        _secure_press(ROTATE)
        hrd_sleep(ROT_DELAY)

    # Calcular desplazamiento desde posición post-rotación
    desplazamiento = col_objetivo - spawn_col
    tecla = RIGHT if desplazamiento > 0 else LEFT

    # ========== MECÁNICA DE DAS (TELETRANSPORTACIÓN FÍSICA) ========== #
    # Utilizar el DAS del motor de juego para viajar instantáneamente (0 ARR) a las paredes.
    # El usuario debe usar la Config PROBADA y ESTABLE (DAS=100ms y ARR=0)
    # Por lo que 130ms de HOLD garantiza un Teleport que absorbe el drift del OS Windows.
    if (col_objetivo == 0 and tecla == LEFT) or (col_objetivo == (10 - width_pieza) and tecla == RIGHT):
        pyautogui.keyDown(tecla)
        hrd_sleep(0.130) 
        pyautogui.keyUp(tecla)
    else:
        # Movimiento intermedio: Requiere taps precisos porque no hay pared límite
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
