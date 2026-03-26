import cv2
import numpy as np
import mss
import time
import sys
import os
import json


class Ambiente:
    def __init__(self):
        self.sct = mss.mss()
        self.config_file = "roi_config.json"
        
        if os.path.exists(self.config_file):
            print("Cargando ROIs desde roi_config.json...")
            with open(self.config_file, "r") as f:
                config = json.load(f)
            self.monitor = config["board"]
            self.monitor_next = config["next"]
            self.monitor_hold = config.get("hold")
        else:
            print(" Tienes 3 segundos para enfocar TETR.IO...")
            time.sleep(3)
            screen = np.array(self.sct.grab(self.sct.monitors[1]))

            # 1. ROI: Grilla del juego (10x20)
            roi_board = cv2.selectROI("1. Selecciona la GRILLA central (10x20) y presiona ENTER", screen)
            cv2.destroyAllWindows()
            if roi_board[2] <= 0 or roi_board[3] <= 0:
                print("Error: Region de grilla invalida.")
                sys.exit(1)
            
            # 2. ROI: NEXT queue (the 5 pieces)
            roi_next = cv2.selectROI("2. Selecciona toda la cola NEXT (5 piezas) y presiona ENTER", screen)
            cv2.destroyAllWindows()
            
            # 3. ROI: HOLD box
            roi_hold = cv2.selectROI("3. Selecciona la caja HOLD y presiona ENTER", screen)
            cv2.destroyAllWindows()

            self.monitor = {"top": int(roi_board[1]), "left": int(roi_board[0]), "width": int(roi_board[2]), "height": int(roi_board[3])}
            self.monitor_next = {"top": int(roi_next[1]), "left": int(roi_next[0]), "width": int(roi_next[2]), "height": int(roi_next[3])}
            self.monitor_hold = {"top": int(roi_hold[1]), "left": int(roi_hold[0]), "width": int(roi_hold[2]), "height": int(roi_hold[3])}
            
            # Guardar config
            with open(self.config_file, "w") as f:
                json.dump({
                    "board": self.monitor,
                    "next": self.monitor_next,
                    "hold": self.monitor_hold
                }, f)
            print("ROIs guardados en roi_config.json. Borra el archivo si cambias el tamaño de la ventana.")

        # === DETECCIÓN DE PIEZA BASADA EN NEXT ===
        self.pieza_actual = None
        self.ultima_next = None

    def capturar(self):
        img = np.array(self.sct.grab(self.monitor))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

    def _capturar_next(self):
        """Captura la region NEXT."""
        img = np.array(self.sct.grab(self.monitor_next))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

    def _hue_a_pieza(self, h_median):
        """Convierte un valor Hue mediano a tipo de pieza."""
        if h_median < 10 or h_median > 170:
            return "Z"   # Rojo
        elif h_median < 22:
            return "L"   # Naranja
        elif h_median < 38:
            return "O"   # Amarillo
        elif h_median < 75:
            return "S"   # Verde
        elif h_median < 105:
            return "I"   # Cian
        elif h_median < 135:
            return "J"   # Azul
        else:
            return "T"   # Purpura

    def _detectar_color_en_region(self, hsv_region, s_min=80, v_min=80):
        """Detecta pieza por color en una región HSV.
        Retorna el tipo de pieza o None si no hay suficientes píxeles."""
        mask = (hsv_region[:, :, 1] > s_min) & (hsv_region[:, :, 2] > v_min)
        n = int(np.sum(mask))
        if n < 5:
            return None
        hues = hsv_region[:, :, 0][mask]
        h_median = float(np.median(hues))
        return self._hue_a_pieza(h_median)

    def _detectar_pieza_spawn(self, img):
        """Fallback: detecta pieza en zona de spawn (filas 0-3) de la grilla.
        Solo se usa al inicio cuando aún no tenemos un NEXT previo."""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h_img = hsv.shape[0]
        ys = np.linspace(0, h_img, 21, dtype=int)
        # Filas 0-3: zona donde la pieza apenas entra
        spawn = hsv[ys[0]:ys[4], :, :]
        return self._detectar_color_en_region(spawn, s_min=100, v_min=100)

    def _capturar_hold(self):
        """Captura la region HOLD."""
        if not self.monitor_hold:
            return None
        img = np.array(self.sct.grab(self.monitor_hold))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

    def _detectar_hold(self):
        """Detecta la pieza contenida en la caja HOLD."""
        img = self._capturar_hold()
        if img is None:
            return None
        
        h, w = img.shape[:2]
        margin_y = h // 4
        margin_x = w // 10
        centro = img[margin_y:h-margin_y, margin_x:w-margin_x]
        
        hsv = cv2.cvtColor(centro, cv2.COLOR_BGR2HSV)
        mask = (hsv[:, :, 1] > 50) & (hsv[:, :, 2] > 60)
        n = int(np.sum(mask))
        if n < 5:
            return None
            
        hues = hsv[:, :, 0][mask]
        h_median = float(np.median(hues))
        return self._hue_a_pieza(h_median)

    def _detectar_next(self):
        """Detecta las 3 primeras piezas NEXT de la cola."""
        img = self._capturar_next()
        h, w = img.shape[:2]
        slice_h = h // 5
        
        piezas = []
        for i in range(3):
            img_next = img[i*slice_h : (i+1)*slice_h, :]
            
            margin_y = slice_h // 4
            margin_x = w // 10
            centro = img_next[margin_y:slice_h-margin_y, margin_x:w-margin_x]
            
            hsv = cv2.cvtColor(centro, cv2.COLOR_BGR2HSV)
            mask = (hsv[:, :, 1] > 50) & (hsv[:, :, 2] > 60)
            n = int(np.sum(mask))
            if n < 5:
                # Si no detecta, usa el fallback de ultima_next
                pieza = self.ultima_next[i] if self.ultima_next and len(self.ultima_next) > i else "T"
            else:
                hues = hsv[:, :, 0][mask]
                h_median = float(np.median(hues))
                pieza = self._hue_a_pieza(h_median)
                
            piezas.append(pieza)
            
        self.ultima_next = piezas
        return piezas

    def _detectar_tablero(self, img):
        """Detecta celdas ocupadas del tablero.
        NO limpia ninguna fila — la pieza spawn fuera de la grilla,
        así que no contamina la detección."""
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

                margin_y = ch // 4
                if j == 0 or j == 9:
                    margin_x = cw // 3
                else:
                    margin_x = cw // 4
                if margin_y > 0 and margin_x > 0:
                    centro = celda[margin_y:-margin_y, margin_x:-margin_x]
                else:
                    centro = celda

                s_channel = centro[:, :, 1].flatten()
                v_channel = centro[:, :, 2].flatten()
                
                s_med = float(np.median(s_channel))
                v_med = float(np.median(v_channel))

                # Requisito estricto de Saturación y Brillo para confirmar bloque sólido opaco
                # Los números del countdown (ej. "4") son semi-transparentes (V ~ 60-110).
                # Los bloques reales opacos superan V > 150 y S > 150.
                if v_med > 120 and s_med > 120:
                    tablero[i][j] = 1

        # ========== FILTRO ANTI-SPAWN GHOST v3 (Flood-Fill Robusto) ========== #
        # PROBLEMA v1 (Flood-Fill Row 19): Durante line clears, Row 19 queda vacía
        #   y toda la montaña se borra → pirámide central catastrófica.
        # PROBLEMA v2 (Wipe Row 0-3): A velocidad alta (Nivel 6+), la pieza cayendo
        #   llega a filas 4-7 antes del screenshot → torre central en endgame.
        #
        # SOLUCIÓN v3: Flood-Fill desde la FILA OCUPADA MÁS BAJA (no hardcoded Row 19).
        # Si hay un line clear animándose y Row 19 está vacía, Row 18 o 17 servirá.
        # Usa 4-conectividad (arriba/abajo/izq/der) para evitar conexiones diagonales falsas.
        
        # 1. Encontrar la fila más baja que tenga al menos un bloque
        floor_row = -1
        for r in range(filas - 1, -1, -1):
            if np.any(tablero[r] == 1):
                floor_row = r
                break
        
        # 2. Si no hay bloques, el tablero está limpio - no hacer nada
        if floor_row >= 0:
            anchored = np.zeros((filas, columnas), dtype=bool)
            queue = []
            
            # Sembrar desde TODOS los bloques en la fila más baja
            for j in range(columnas):
                if tablero[floor_row][j] == 1:
                    anchored[floor_row][j] = True
                    queue.append((floor_row, j))
            
            # 8-Way Flood Fill (diagonal incluida - necesaria porque S/Z crean conexiones diagonales)
            dirs = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]
            while queue:
                r, c = queue.pop(0)
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < filas and 0 <= nc < columnas:
                        if tablero[nr][nc] == 1 and not anchored[nr][nc]:
                            anchored[nr][nc] = True
                            queue.append((nr, nc))
            
            # Borrar cualquier bloque que no esté anclado (pieza cayendo o texto UI)
            for i in range(filas):
                for j in range(columnas):
                    if tablero[i][j] == 1 and not anchored[i][j]:
                        tablero[i][j] = 0

        return tablero

    def obtener_estado(self):
        """Retorna (tablero, pieza_actual, next_piezas_list)."""
        img = self.capturar()
        tablero = self._detectar_tablero(img)

        next_detectado = self._detectar_next()

        if self.pieza_actual is None:
            pieza = self._detectar_pieza_spawn(img)
            if pieza is None:
                pieza = "T"
            self.pieza_actual = pieza

        pieza = self.pieza_actual
        next_piezas = next_detectado if next_detectado else self.ultima_next

        mode = f"| Next: {next_piezas}" if next_piezas else "| Next: ???"
        # print(f"Pieza: {pieza} {mode}")
        # print(tablero)

        return tablero, pieza, next_piezas

    def avanzar_pieza(self, next_piezas):
        """Llamar DESPUÉS de colocar la pieza: la actual pasa a ser next_piezas[0]."""
        if next_piezas and len(next_piezas) > 0:
            self.ultima_next = next_piezas
            self.pieza_actual = next_piezas[0]
