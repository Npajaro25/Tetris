import cv2
import numpy as np
import mss
import time
import sys


class Ambiente:
    def __init__(self):
        self.sct = mss.mss()
        print(" Tienes 5 segundos para prepararte y enfocar la ventana del juego...")
        time.sleep(5)
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

        # Buscar píxeles con color vivo (S>80, V>80)
        mask = (hsv[:, :, 1] > 80) & (hsv[:, :, 2] > 80)
        n_pixels = np.sum(mask)

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
        elif h_median < 80:
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

                # Margen fijo de 1px para evitar líneas de grilla
                # (porcentaje era demasiado agresivo en columnas de borde)
                mx = min(1, max(0, cw // 6))
                my = min(1, max(0, ch // 6))
                if my > 0 and mx > 0:
                    centro = celda[my:-my, mx:-mx]
                else:
                    centro = celda

                v_channel = centro[:, :, 2].flatten()
                v_p75 = float(np.percentile(v_channel, 75))

                if v_p75 > 80:
                    tablero[i][j] = 1

        # Limpiar zona de spawn + countdown (filas 0-6)
        tablero[0:6, :] = 0

        return tablero

    def obtener_estado(self):
        """Retorna (tablero, pieza_actual).
        Doble lectura: captura 2 veces con 150ms de separación.
        Los bloques fijos NO se mueven → se mantienen en ambas lecturas.
        La pieza cayendo SÍ se mueve → desaparece con el AND."""
        img1 = self.capturar()
        pieza = self._detectar_pieza_por_color(img1)
        tablero1 = self._detectar_tablero(img1)

        time.sleep(0.15)

        img2 = self.capturar()
        tablero2 = self._detectar_tablero(img2)

        # AND lógico: solo quedan las celdas que están en AMBAS lecturas
        tablero = tablero1 & tablero2

        print(f"Pieza: {pieza}")
        print(tablero)

        return tablero, pieza
