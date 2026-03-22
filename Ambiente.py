import cv2
import numpy as np
import mss

class Ambiente:
    def __init__(self):
        self.sct = mss.mss()
        self.monitor = self.seleccionar_region()

    def seleccionar_region(self):
        screen = np.array(self.sct.grab(self.sct.monitors[1]))
        roi = cv2.selectROI("Selecciona el tablero", screen)
        cv2.destroyAllWindows()

        x, y, w, h = roi

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

    def detectar_tablero(self, img):
        filas, columnas = 20, 10
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

                h_mean = np.mean(celda[:, :, 0])
                s_mean = np.mean(celda[:, :, 1])
                v_mean = np.mean(celda[:, :, 2])
                if s_mean > 40 and v_mean > 40:
                    tablero[i][j] = 1
                else:
                    tablero[i][j] = 0

        return tablero

    def detectar_pieza(self, img):
        # zona superior
        h, w, _ = img.shape
        pieza_zone = img[0:h//4, :]

        hsv = cv2.cvtColor(pieza_zone, cv2.COLOR_BGR2HSV)

        h_mean = np.mean(hsv[:, :, 0])
        s_mean = np.mean(hsv[:, :, 1])
        v_mean = np.mean(hsv[:, :, 2])

        print(f"H:{h_mean:.1f} S:{s_mean:.1f} V:{v_mean:.1f}")

      if s_mean < 20:
            return "I"

        if h_mean < 10:
            return "Z"
        elif h_mean < 25:
            return "L"
        elif h_mean < 45:
            return "O"
        elif h_mean < 90:
            return "S"
        elif h_mean < 140:
            return "T"
        else:
            return "J"

    def obtener_estado(self):
        img = self.capturar()
        tablero = self.detectar_tablero(img)
        pieza = self.detectar_pieza(img)

        print("Pieza detectada:", pieza)
        print(tablero)

        return tablero, pieza
