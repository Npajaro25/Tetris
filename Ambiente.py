import cv2
import numpy as np
import mss
import time
import sys


class Ambiente:
    def __init__(self):
        self.sct = mss.mss()
        print(" Tienes 3 segundos para enfocar TETR.IO...")
        time.sleep(3)
        screen = np.array(self.sct.grab(self.sct.monitors[1]))
        roi = cv2.selectROI("Selecciona la GRILLA del Tetris (10x20)", screen)
        cv2.destroyAllWindows()
        x, y, w, h = roi
        if w <= 0 or h <= 0:
            print("Error: Region invalida.")
            sys.exit(1)
        self.monitor = {"top": int(y), "left": int(x), "width": int(w), "height": int(h)}
        self.ultima_pieza = "T"

    def capturar(self):
        img = np.array(self.sct.grab(self.monitor))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

    def _detectar_pieza_por_color(self, img):
        """Detecta la pieza actual analizando el color (Hue) de los píxeles
        brillantes en la zona de spawn (filas 0-5)."""
        h_img, w_img, _ = img.shape
        filas = 20
        ys = np.linspace(0, h_img, filas + 1, dtype=int)
        # Zona de spawn: filas 0-5
        spawn = img[ys[0]:ys[6], :, :]
        hsv = cv2.cvtColor(spawn, cv2.COLOR_BGR2HSV)

        # Umbrales para captar piezas reales sin incluir glow de fondo
        mask = (hsv[:, :, 1] > 100) & (hsv[:, :, 2] > 100)
        n_pixels = int(np.sum(mask))

        if n_pixels < 10:
            return self.ultima_pieza  # Fallback

        hues = hsv[:, :, 0][mask]
        h_median = float(np.median(hues))

        # Mapeo de Hue a pieza
        if h_median < 10 or h_median > 170:
            pieza = "Z"   # Rojo
        elif h_median < 22:
            pieza = "L"   # Naranja
        elif h_median < 38:
            pieza = "O"   # Amarillo
        elif h_median < 75:
            pieza = "S"   # Verde
        elif h_median < 105:
            pieza = "I"   # Cian
        elif h_median < 135:
            pieza = "J"   # Azul
        else:
            pieza = "T"   # Púrpura

        self.ultima_pieza = pieza
        return pieza

    def _detectar_tablero(self, img):
        """Detecta celdas ocupadas del tablero.
        Usa percentil 75 del Value para ignorar líneas de grilla.
        Usa linspace para que la última columna incluya todos los píxeles."""
        filas, columnas = 20, 10
        h, w, _ = img.shape

        ys = np.linspace(0, h, filas + 1, dtype=int)
        xs = np.linspace(0, w, columnas + 1, dtype=int)

        tablero = np.zeros((filas, columnas), dtype=int)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        for i in range(filas):
            for j in range(columnas):
                y1, y2 = ys[i], ys[i + 1]
                x1, x2 = xs[j], xs[j + 1]

                celda = hsv[y1:y2, x1:x2]
                ch, cw = celda.shape[:2]

                # Margen para evitar bordes de grilla del TETR.IO
                # Columnas 0 y 9 necesitan más margen (capturan borde de ventana)
                margin_y = ch // 4
                if j == 0 or j == 9:
                    margin_x = cw // 3  # Más agresivo en bordes
                else:
                    margin_x = cw // 4
                if margin_y > 0 and margin_x > 0:
                    centro = celda[margin_y:-margin_y, margin_x:-margin_x]
                else:
                    centro = celda

                v_channel = centro[:, :, 2].flatten()
                v_p75 = float(np.percentile(v_channel, 75))

                if v_p75 > 80:
                    tablero[i][j] = 1

        # Limpiar solo filas 0-1 (spawn inmediato, pieza recién aparece)
        tablero[0:2, :] = 0

        return tablero

    def obtener_estado(self):
        """Retorna (tablero, pieza_actual).
        Doble lectura con 150ms de separación.
        - Pieza: color de spawn zone en img1
        - Tablero: AND de ambas lecturas (elimina pieza cayendo)"""
        img1 = self.capturar()
        pieza = self._detectar_pieza_por_color(img1)
        tablero1 = self._detectar_tablero(img1)

        time.sleep(0.12)

        img2 = self.capturar()
        tablero2 = self._detectar_tablero(img2)

        # AND lógico: solo quedan las celdas fijas
        tablero = tablero1 & tablero2

        print(f"Pieza: {pieza}")

        return tablero, pieza
