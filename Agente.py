from Model.IA import Tetris_IA
from Model.Grid import Grid
import Model.Pieces as Piece

class Agente:
    def __init__(self):
        self.grid = Grid()
        self.ia = Tetris_IA(self.grid)

        self.mapa_piezas = {
            "I": "Cian_l",
            "T": "Fucsia_T",
            "S": "Green_S",
            "Z": "Red_Z",
            "O": "Yellow_sq",
            "L": "Orange_L",
            "J": "Purple_L"
        }

        # Estado del Hold
        self.hold_piece_str = None  # Pieza guardada (string: "T", "I", etc.)
        self.can_hold = True        # Se resetea cada nuevo turno

    def crear_pieza(self, pieza_str):
        nombre = self.mapa_piezas[pieza_str]
        clase = getattr(Piece, nombre)
        return clase()

    def _evaluar_pieza(self, tablero, pieza_str):
        """Evalúa la mejor jugada para una pieza dada sobre el tablero actual.
        Retorna (score, col, rot, spawn_col)."""
        self.grid.grid = tablero.tolist()
        pieza = self.crear_pieza(pieza_str)
        valor, col, rot, _ = self.ia.get_best_choice(pieza)

        pieza.set_current_shape(rot)
        spawn_col = pieza.grid_position
        return valor, col, rot, spawn_col

    def _evaluar_pieza_lookahead(self, tablero, pieza_str, next_pieza_str):
        """Evalúa con 2-piece lookahead.
        Retorna (score, col, rot, spawn_col)."""
        self.grid.grid = tablero.tolist()
        pieza = self.crear_pieza(pieza_str)
        next_pieza = self.crear_pieza(next_pieza_str)
        valor, col, rot, _ = self.ia.get_best_choice_lookahead(pieza, next_pieza)

        pieza.set_current_shape(rot)
        spawn_col = pieza.grid_position
        return valor, col, rot, spawn_col

    def decidir(self, tablero, pieza_str, next_piezas=None):
        """Decide la mejor acción: jugar pieza actual o usar Hold.

        Retorna (col, rot, spawn_col, usar_hold)
        - usar_hold=True → Main.py debe ejecutar hold ANTES del movimiento
        - usar_hold=False → jugar la pieza actual directamente"""

        # Usar la primera pieza para un lookahead rápido y efectivo (2 piezas = <20ms)
        # Buscar ramas con 3 piezas a profundidad toma >600ms y te haría perder.
        next_pieza_str = next_piezas[0] if (next_piezas and len(next_piezas) > 0) else None
        siguiente_lookahead = next_pieza_str
        
        # ========== FIX: LOOKAHEAD TIMELINE SCHISM ========== #
        # Si la pieza que viene es 'I', y NO la vamos a usar para hacer Tetris ahora mismo
        # (porque la robaremos para el HOLD), el lookahead no debe creer que tiene la 'I' disponible.
        # Debe creer que tiene la pieza que saldrá del HOLD, o la 2da pieza en la cola NEXT.
        if next_pieza_str == "I" and self.hold_piece_str != "I":
            if self.hold_piece_str is not None:
                siguiente_lookahead = self.hold_piece_str
            elif next_piezas and len(next_piezas) > 1:
                siguiente_lookahead = next_piezas[1]
            else:
                siguiente_lookahead = None

        # Evaluar pieza actual (con lookahead si tenemos next)
        # Evaluar pieza actual (con lookahead si tenemos next válido)
        if siguiente_lookahead:
            score_current, col_c, rot_c, spawn_c = self._evaluar_pieza_lookahead(
                tablero, pieza_str, siguiente_lookahead)
        else:
            score_current, col_c, rot_c, spawn_c = self._evaluar_pieza(tablero, pieza_str)

        # Inicializar variables de retorno
        usar_hold = False
        best_col, best_rot, best_spawn = col_c, rot_c, spawn_c

        # ========== LÓGICA DE HOLD NATURAL CON PREFERENCIA DE 'I' ========== #
        # Le damos un bono moderado (+500) a cualquier decisión que resulte en 
        # tener la pieza 'I' en el slot de HOLD. Así la IA preferirá guardarla,
        # pero la soltará si hacer un Tetris (+3000) o sobrevivir vale más la pena.
        
        bonus_I = 500
        efectivo_current = score_current + (bonus_I if self.hold_piece_str == "I" else 0)

        if self.can_hold:
            if self.hold_piece_str is not None:
                # Hold OCUPADO: comparar Play Current vs Play Hold
                # Hold OCUPADO: comparar Play Current vs Play Hold
                if siguiente_lookahead:
                    score_hold, col_h, rot_h, spawn_h = self._evaluar_pieza_lookahead(
                        tablero, self.hold_piece_str, siguiente_lookahead)
                else:
                    score_hold, col_h, rot_h, spawn_h = self._evaluar_pieza(
                        tablero, self.hold_piece_str)

                # Si el score efectivo del hold es legítimamente mejor:
                efectivo_hold = score_hold + (bonus_I if pieza_str == "I" else 0)
                
                if efectivo_hold > efectivo_current:
                    usar_hold = True
                    best_col, best_rot, best_spawn = col_h, rot_h, spawn_h
                    pieza_que_sale = self.hold_piece_str
                    self.hold_piece_str = pieza_str
                    self.can_hold = False
                    reason = "BETTER SCORE"
                    # print(f"  HOLD: guardó {pieza_str}, juega {pieza_que_sale} [{reason}]")

            else:
                # Hold VACÍO: comparar Play Current vs Play Next (Hold Current)
                # Ojo: si jugamos Next, la que sigue de Lookahead será la que estaba 2da en la cola.
                lookahead_si_jugamos_next = next_piezas[1] if (next_piezas and len(next_piezas) > 1) else None
                if next_pieza_str:
                    if lookahead_si_jugamos_next:
                        score_next, col_n, rot_n, spawn_n = self._evaluar_pieza_lookahead(
                            tablero, next_pieza_str, lookahead_si_jugamos_next)
                    else:
                        score_next, col_n, rot_n, spawn_n = self._evaluar_pieza(
                            tablero, next_pieza_str)

                    efectivo_next = score_next + (bonus_I if pieza_str == "I" else 0)
                    
                    if efectivo_next > efectivo_current + 5: # Ligeramente conservador para cambiar un hold vacío
                        usar_hold = True
                        best_col, best_rot, best_spawn = col_n, rot_n, spawn_n
                        self.hold_piece_str = pieza_str
                        self.can_hold = False
                        reason = "BETTER SCORE"
                        # print(f"  HOLD (1st): guardó {pieza_str}, juega {next_pieza_str} [{reason}]")

        if not usar_hold:
            mode = "LA" if next_pieza_str else "1P"
            # print(f"[{mode}] {pieza_str} col={best_col} rot={best_rot}")

        return best_col, best_rot, best_spawn, usar_hold

    def nuevo_turno(self):
        """Llamar al inicio de cada nuevo turno para resetear el bloqueo de Hold."""
        self.can_hold = True
