import time
from Ambiente import Ambiente
from Agente import Agente
from Control import ejecutar_movimiento

ambiente = Ambiente()
agente =  Agente()

print("Iniciando en 3 segundos...")
time.sleep (3)

while True:
    tablero, pieza = ambiente.obtener_estado()

    col, rot = agente.decidir(tablero, pieza)

    ejecutar_movimiento(col, rot)

    time.sleep(0.1)
