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

    def _evaluar_pieza_lookahead(self, tablero, pieza_str, next_piezas_strs):
        """Evalúa con N-piece lookahead.
        Retorna (score, col, rot, spawn_col)."""
        self.grid.grid = tablero.tolist()
        pieza = self.crear_pieza(pieza_str)
        
        # Convertir lista de strings a objetos Piece
        next_piezas = [self.crear_pieza(n_str) for n_str in next_piezas_strs if n_str]
        
        valor, col, rot, _ = self.ia.get_best_choice_lookahead(pieza, next_piezas)

        pieza.set_current_shape(rot)
        spawn_col = pieza.grid_position
        return valor, col, rot, spawn_col

    def decidir(self, tablero, pieza_str, next_piezas=None):
        """Decide la mejor acción: jugar pieza actual o usar Hold."""
        
        # Construir la cola de N piezas para el multi-lookahead
        upcoming_queue = []
        if next_piezas:
            upcoming_queue = next_piezas.copy()
            
        next_pieza_str = upcoming_queue[0] if upcoming_queue else None

        # N-Depth Beam Search: Tomar 1 pieza NEXT (Depth=2 total, idéntico al récord de 60k pero 10x más rápido)
        candidatos_lookahead = upcoming_queue[:1]
        
        # ========== FIX: LOOKAHEAD TIMELINE SCHISM ========== #
        # Si la pieza que viene inminentemente es 'I', y nuestro Hold NO es 'I',
        # es altamente probable que la capturemos en el Hold en vez de jugarla.
        # Para que el lookahead lineal no se confunda y la estrelle contra el suelo,
        # la sustituimos lógicamente por la pieza de Hold o la adelantamos.
        if next_pieza_str == "I" and self.hold_piece_str != "I":
            if self.hold_piece_str is not None:
                candidatos_lookahead[0] = self.hold_piece_str
            elif len(upcoming_queue) > 1:
                candidatos_lookahead = upcoming_queue[1:4]
            else:
                candidatos_lookahead = []

        # Evaluar pieza actual
        if candidatos_lookahead:
            score_current, col_c, rot_c, spawn_c = self._evaluar_pieza_lookahead(
                tablero, pieza_str, candidatos_lookahead)
        else:
            score_current, col_c, rot_c, spawn_c = self._evaluar_pieza(tablero, pieza_str)

        # Inicializar variables de retorno
        usar_hold = False
        best_col, best_rot, best_spawn = col_c, rot_c, spawn_c

        # ========== LÓGICA DE HOLD NATURAL CON PREFERENCIA DE 'I' ========== #
        bonus_I = 500
        efectivo_current = score_current + (bonus_I if self.hold_piece_str == "I" else 0)

        if self.can_hold:
            if self.hold_piece_str is not None:
                # Hold OCUPADO: comparar Play Current vs Play Hold
                if candidatos_lookahead:
                    score_hold, col_h, rot_h, spawn_h = self._evaluar_pieza_lookahead(
                        tablero, self.hold_piece_str, candidatos_lookahead)
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
                # Hold VACÍO: comparar Play Current vs Play Next
                # Ojo: si jugamos Next, la cola de lookahead se desplaza 1 posición
                lookahead_si_jugamos_next = upcoming_queue[1:4] if len(upcoming_queue) > 1 else []
                if next_pieza_str:
                    if lookahead_si_jugamos_next:
                        score_next, col_n, rot_n, spawn_n = self._evaluar_pieza_lookahead(
                            tablero, next_pieza_str, lookahead_si_jugamos_next)
                    else:
                        score_next, col_n, rot_n, spawn_n = self._evaluar_pieza(
                            tablero, next_pieza_str)

                    efectivo_next = score_next + (bonus_I if pieza_str == "I" else 0)
                    
                    if efectivo_next > efectivo_current + 5: # Conservador para cambiar hold vacío
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
