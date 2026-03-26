import cv2
import numpy as np
import mss
import time
import sys
import os
import json

def hue_a_pieza(h_median):
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

def main():
    sct = mss.mss()
    config_file = "roi_config.json"
    
    if os.path.exists(config_file):
        print(f"Cargando ROIs desde {config_file}...")
        with open(config_file, "r") as f:
            config = json.load(f)
        monitor_board = config["board"]
        monitor_next = config["next"]
        monitor_hold = config.get("hold")
    else:
        print(" Tienes 3 segundos para enfocar TETR.IO...")
        time.sleep(3)
        screen = np.array(sct.grab(sct.monitors[1]))

        roi_board = cv2.selectROI("1. Selecciona la GRILLA central (10x20) y presiona ENTER", screen)
        cv2.destroyAllWindows()
        if roi_board[2] <= 0 or roi_board[3] <= 0:
            print("Error: Region de grilla invalida.")
            sys.exit(1)
        
        roi_next = cv2.selectROI("2. Selecciona toda la cola NEXT (5 piezas) y presiona ENTER (sin contar la parte blanca)", screen)
        cv2.destroyAllWindows()
        
        roi_hold = cv2.selectROI("3. Selecciona la caja HOLD y presiona ENTER (sin contar la parte blanca)", screen)
        cv2.destroyAllWindows()

        monitor_board = {"top": int(roi_board[1]), "left": int(roi_board[0]), "width": int(roi_board[2]), "height": int(roi_board[3])}
        monitor_next = {"top": int(roi_next[1]), "left": int(roi_next[0]), "width": int(roi_next[2]), "height": int(roi_next[3])}
        monitor_hold = {"top": int(roi_hold[1]), "left": int(roi_hold[0]), "width": int(roi_hold[2]), "height": int(roi_hold[3])}
        
        with open(config_file, "w") as f:
            json.dump({
                "board": monitor_board,
                "next": monitor_next,
                "hold": monitor_hold
            }, f)
        print("ROIs guardados en config. Borra el archivo json si cambias el tamaño de la ventana.")

    cv2.namedWindow("TETRIS AI DEBUG VISION", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("TETRIS AI DEBUG VISION", 800, 600)

    filas, columnas = 20, 10
    last_next_pieza = "?"

    try:
        while True:
            # Se captura toda la pantalla o al menos el bounding box de las 3 zonas
            min_x = min(monitor_board["left"], monitor_hold["left"], monitor_next["left"])
            min_y = min(monitor_board["top"], monitor_hold["top"], monitor_next["top"])
            max_r = max(monitor_board["left"]+monitor_board["width"], monitor_next["left"]+monitor_next["width"])
            max_b = max(monitor_board["top"]+monitor_board["height"], monitor_next["top"]+monitor_next["height"])
            
            w = max_r - min_x
            h = max_b - min_y
            
            # Padding
            debug_monitor = {"top": max(0, min_y - 20), "left": max(0, min_x - 20), "width": w + 40, "height": h + 40}
            
            img_bgbg = np.array(sct.grab(debug_monitor))
            debug_img = cv2.cvtColor(img_bgbg, cv2.COLOR_BGRA2BGR)
            hsv_debug = cv2.cvtColor(debug_img, cv2.COLOR_BGR2HSV)

            # ======== TABLERO ========
            offset_x = monitor_board["left"] - debug_monitor["left"]
            offset_y = monitor_board["top"] - debug_monitor["top"]
            bw, bh = monitor_board["width"], monitor_board["height"]

            cv2.rectangle(debug_img, (offset_x, offset_y), (offset_x + bw, offset_y + bh), (255, 255, 255), 2)
            ys = np.linspace(offset_y, offset_y + bh, filas + 1, dtype=int)
            xs = np.linspace(offset_x, offset_x + bw, columnas + 1, dtype=int)

            blocks_detected = 0

            for i in range(filas):
                for j in range(columnas):
                    y1, y2 = ys[i], ys[i + 1]
                    x1, x2 = xs[j], xs[j + 1]

                    celda = hsv_debug[y1:y2, x1:x2]
                    ch, cw = celda.shape[:2]
                    margin_y = ch // 4
                    margin_x = cw // 3 if (j == 0 or j == 9) else cw // 4
                    
                    if margin_y > 0 and margin_x > 0:
                        centro = celda[margin_y:-margin_y, margin_x:-margin_x]
                    else:
                        centro = celda

                    if centro.size == 0: continue

                    s_channel = centro[:, :, 1].flatten()
                    v_channel = centro[:, :, 2].flatten()
                    
                    s_med = float(np.median(s_channel))
                    v_med = float(np.median(v_channel))

                    is_solid = (v_med > 120 and s_med > 120)
                    if is_solid:
                        blocks_detected += 1
                        cv2.rectangle(debug_img, (x1+2, y1+2), (x2-2, y2-2), (0, 255, 0), -1)
                        if ch > 15:
                            cv2.putText(debug_img, f"S{int(s_med)}", (x1+2, y1+margin_y), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0,0,0), 1)
                    else:
                        cv2.rectangle(debug_img, (x1, y1), (x2, y2), (50, 50, 50), 1)
                        if v_med > 60:
                            cv2.putText(debug_img, f"V{int(v_med)} S{int(s_med)}", (x1+2, y1+margin_y), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0,0,255), 1)

            # ======== NEXT ========
            nx = monitor_next["left"] - debug_monitor["left"]
            ny = monitor_next["top"] - debug_monitor["top"]
            nw = monitor_next["width"]
            nh = monitor_next["height"]
            
            cv2.rectangle(debug_img, (nx, ny), (nx + nw, ny + nh), (255, 255, 0), 2)
            cv2.putText(debug_img, "NEXT QUEUE", (nx, ny - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)
            
            slice_h = nh // 5
            
            for i in range(3):
                nx_y = ny + (i * slice_h)
                cv2.rectangle(debug_img, (nx, nx_y), (nx + nw, nx_y + slice_h), (0, 255, 255), 1)
                
                celda_next = hsv_debug[nx_y:nx_y+slice_h, nx:nx+nw]
                if celda_next.size > 0:
                    h_n, w_n = celda_next.shape[:2]
                    m_y = h_n // 4
                    m_x = w_n // 10
                    centro_next = celda_next[m_y:h_n-m_y, m_x:w_n-m_x]
                    
                    if centro_next.size > 0:
                        mask = (centro_next[:, :, 1] > 50) & (centro_next[:, :, 2] > 60)
                        n_pixels = int(np.sum(mask))
                        if n_pixels >= 5:
                            hues = centro_next[:, :, 0][mask]
                            h_median = float(np.median(hues))
                            pieza = hue_a_pieza(h_median)
                            if i == 0: last_next_pieza = pieza
                            cv2.putText(debug_img, f"{pieza} ({int(h_median)})", (nx+w_n+5, nx_y + slice_h//2), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                        elif i == 0:
                            cv2.putText(debug_img, f"? ({last_next_pieza})", (nx+w_n+5, nx_y + slice_h//2), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

            # ======== HOLD ========
            if monitor_hold:
                hx = monitor_hold["left"] - debug_monitor["left"]
                hy = monitor_hold["top"] - debug_monitor["top"]
                hw = monitor_hold["width"]
                hh = monitor_hold["height"]
                cv2.rectangle(debug_img, (hx, hy), (hx + hw, hy + hh), (255, 0, 255), 2)
                cv2.putText(debug_img, "HOLD", (hx, hy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,255), 1)

                celda_hold = hsv_debug[hy:hy+hh, hx:hx+hw]
                if celda_hold.size > 0:
                    m_y = hh // 4
                    m_x = hw // 10
                    centro_hold = celda_hold[m_y:hh-m_y, m_x:hw-m_x]
                    
                    if centro_hold.size > 0:
                        mask = (centro_hold[:, :, 1] > 50) & (centro_hold[:, :, 2] > 60)
                        n_pixels = int(np.sum(mask))
                        if n_pixels >= 5:
                            hues = centro_hold[:, :, 0][mask]
                            h_median = float(np.median(hues))
                            pieza_hold = hue_a_pieza(h_median)
                            cv2.putText(debug_img, f"{pieza_hold} ({int(h_median)})", (hx + hw//3, hy + hh//2), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,255), 2)
                        else:
                            cv2.putText(debug_img, "VACIO", (hx + hw//4, hy + hh//2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100,100,100), 2)

            cv2.putText(debug_img, f"Blocks Detected: {blocks_detected}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            cv2.putText(debug_img, "Press 'Q' to quit", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)

            cv2.imshow("TETRIS AI DEBUG VISION", debug_img)
            if cv2.waitKey(50) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
