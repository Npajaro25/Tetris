import cv2
import numpy as np
import mss
import time
import sys

class Ambiente:
    def __init__(self):
        self.sct = mss.mss()
        self.monitor = self.seleccionar_region()

    def seleccionar_region(self):
        print(" Tienes 5 segundos para prepararte y enfocar la ventana del juego...")
        time.sleep(5)
        screen = np.array(self.sct.grab(self.sct.monitors[1]))
        roi = cv2.selectROI("Selecciona el tablero", screen)
        cv2.destroyAllWindows()

        x, y, w, h = roi
        if w <= 0 or h <= 0:
            print("Error: Region invalida.")
            sys.exit(1)

        return {
            "top": int(y),
            "left": int(x),
            "width": int(w),
            "height": int(h)
        }

    def capturar(self):
        img = np.array(self.sct.grab(self.monitor))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

    def _detectar_tablero_raw(self, img):
        """Detecta celdas ocupadas sin filtrar pieza cayendo."""
        filas, columnas = 20, 10
        h, w, _ = img.shape

        # Recortar 3% de cada borde para excluir bordes del ROI
        margin_top = int(h * 0.03)
        margin_bot = int(h * 0.03)
        margin_left = int(w * 0.03)
        margin_right = int(w * 0.03)
        img = img[margin_top:h - margin_bot, margin_left:w - margin_right]
        h, w, _ = img.shape

        celda_h = h // filas
        celda_w = w // columnas

        tablero = np.zeros((filas, columnas), dtype=int)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        for i in range(filas):
            for j in range(columnas):
                y1 = i * celda_h
                y2 = (i + 1) * celda_h
                x1 = j * celda_w
                x2 = (j + 1) * celda_w

                celda = hsv[y1:y2, x1:x2]

                # Usar centro de la celda (evitar bordes de cuadrícula)
                margin_y = celda_h // 4
                margin_x = celda_w // 4
                if margin_y > 0 and margin_x > 0:
                    celda = celda[margin_y:-margin_y, margin_x:-margin_x]

                s_mean = np.mean(celda[:, :, 1])
                v_mean = np.mean(celda[:, :, 2])

                if s_mean > 70 and v_mean > 70:
                    tablero[i][j] = 1

        return tablero

    def obtener_estado(self):
        """Lee el tablero DOS VECES para separar bloques colocados de la pieza cayendo.
        Los bloques colocados NO se mueven entre lecturas -> se mantienen.
        La pieza cayendo SÍ se mueve -> se filtra."""

        tablero1 = self._detectar_tablero_raw(self.capturar())
        time.sleep(0.15)
        tablero2 = self._detectar_tablero_raw(self.capturar())

        # Solo mantener celdas que son 1 en AMBAS lecturas (bloques estáticos)
        tablero = np.where((tablero1 == 1) & (tablero2 == 1), 1, 0)

        # Ignorar zona de spawn (top 4 filas)
        tablero[0:4, :] = 0

        # La detección de pieza por color es demasiado frágil para TETR.IO.
        # Usamos T como pieza por defecto — es la más versátil (3 ancho, 4 rotaciones).
        pieza = "T"

        print("Pieza:", pieza)
        print(tablero)

        return tablero, pieza
