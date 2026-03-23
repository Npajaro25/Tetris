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
MAX_STALE = 5
game_started = False

while True:
    tablero, pieza = ambiente.obtener_estado()

    # Detectar si el tablero es todo ceros
    if np.sum(tablero) == 0:
        if not game_started:
            time.sleep(0.3)
            continue
        stale_count += 1
        if stale_count >= MAX_STALE:
            print("Game over detectado. Deteniendo agente.")
            break
        time.sleep(0.2)
        continue
    else:
        game_started = True
        stale_count = 0

    col, rot, spawn_col = agente.decidir(tablero, pieza)

    ejecutar_movimiento(col, rot, spawn_col)

    # Espera reducida para Blitz — cada ms cuenta
    time.sleep(0.35)
