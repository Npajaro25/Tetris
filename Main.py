import time
from Ambiente import Ambiente
from Agente import Agente
from Control import ejecutar_movimiento
import numpy as np

ambiente = Ambiente()
agente = Agente()

print("Iniciando en 3 segundos...")
time.sleep(3)

stale_count = 0
MAX_STALE = 30

while True:
    tablero, pieza = ambiente.obtener_estado()

    # Detectar si el tablero es todo ceros repetidamente (game over)
    if np.sum(tablero) == 0:
        stale_count += 1
        if stale_count >= MAX_STALE:
            print("El tablero esta vacio por mucho tiempo. Posible game over.")
            print("Deteniendo agente.")
            break
        time.sleep(0.3)
        continue
    else:
        stale_count = 0

    col, rot, spawn_col = agente.decidir(tablero, pieza)

    ejecutar_movimiento(col, rot, spawn_col)

    # Esperar a que la pieza caiga y se asiente
    time.sleep(0.4)
