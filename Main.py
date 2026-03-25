import time
from Ambiente import Ambiente
from Agente import Agente
from Control import ejecutar_movimiento, ejecutar_hold
import numpy as np
import cv2
import os
import glob

ambiente = Ambiente()
agente = Agente()

# Esperar activamente a que desaparezca el texto "GO!" o "READY"
print("Esperando a que el tablero esté completamente limpio de UI...")
intentos = 0
while True:
    # Solo necesitamos el tablero para ver si está vacío
    img = ambiente.capturar()
    tablero = ambiente._detectar_tablero(img)
    if tablero is not None and np.sum(tablero) == 0:
        print("Tablero limpio detectado. ¡A jugar!")
        break
    intentos += 1
    if intentos > 50: # Timeout tras ~5 segundos
        print("Cuidado: El tablero no parece vaciarse. Iniciando de todos modos...")
        break
    time.sleep(0.1)

# Limpiar evidencias de la partida anterior
evidence_dir = "evidences"
if not os.path.exists(evidence_dir):
    os.makedirs(evidence_dir)
else:
    for f in glob.glob(os.path.join(evidence_dir, "evidence_*.png")):
        try:
            os.remove(f)
        except Exception:
            pass

stale_count = 0
MAX_STALE = 2            # 2 ciclos vacíos consecutivos = ~0.7 segundos = game over
game_started = False
start_time = None
prev_pieza = None
prev_next = None

while True:
    tablero, pieza, next_pieza = ambiente.obtener_estado()

    # ========== TIME OVER ESTRICTO (120 Segundos) ========== #
    if game_started:
        elapsed = time.time() - start_time
        
        # Capturas de evidencia en los últimos segundos (115s a 122s)
        if 115 <= elapsed <= 122:
            if not hasattr(ambiente, 'last_evidence_time'):
                ambiente.last_evidence_time = 0
            if time.time() - ambiente.last_evidence_time >= 1.0:
                # Capturar toda la pantalla (monitor 1) para garantizar que se vea la UI exterior y la puntuación
                full_screen = np.array(ambiente.sct.grab(ambiente.sct.monitors[1]))
                full_screen = cv2.cvtColor(full_screen, cv2.COLOR_BGRA2BGR)
                
                img_path = os.path.join(evidence_dir, f"evidence_sec_{int(elapsed)}.png")
                cv2.imwrite(img_path, full_screen)
                
                ambiente.last_evidence_time = time.time()
                print(f"[DEBUG] Evidencia final guardada (Full Screen): {img_path}")

        if elapsed >= 122: # 120s de Blitz + 2s de gracia (animación inicial)
            print("¡Tiempo límite de TETR.IO Blitz alcanzado! Deteniendo agente para ver puntuación.")
            break

    # ========== DETECCIÓN DE TABLERO VACÍO ========== #
    board_empty = (np.sum(tablero) == 0)
    
    if board_empty:
        if not game_started:
            # Antes de la primera pieza anclada: esperar pacientemente
            time.sleep(0.3)
            continue
        else:
            # DESPUÉS de que el juego empezó: podría ser un line clear transitorio
            # o el verdadero game over
            stale_count += 1
            if stale_count >= MAX_STALE:
                print("Game over detectado (tablero vacío persistente). Deteniendo agente.")
                break
            time.sleep(0.35)
            continue
    else:
        if not game_started:
            game_started = True
            start_time = time.time()
        stale_count = 0  # Resetear: el tablero tiene bloques reales

    # Resetear Hold al inicio de cada nuevo turno (El agente decide si usar el slot)
    agente.nuevo_turno()

    col, rot, spawn_col, usar_hold = agente.decidir(tablero, pieza, next_pieza)

    if usar_hold:
        ejecutar_hold()
        # Dar tiempo a TETR.IO para que cambie la UI del panel NEXT (50ms)
        time.sleep(0.05)
        # La pieza que estaba en NEXT ahora es la actual.
        # Necesitamos saber cuál es la NUEVA pieza en el panel NEXT
        next_pieza = ambiente._detectar_next()

    ejecutar_movimiento(col, rot, spawn_col)

    # Avanzar la pieza: la actual pasa a ser lo que era NEXT
    ambiente.avanzar_pieza(next_pieza)

    # Espera estable para que la pieza asiente + line clear animation termine (anti-ghosting)
    time.sleep(0.28)
