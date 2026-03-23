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

    def crear_pieza(self, pieza_str):
        nombre = self.mapa_piezas[pieza_str]
        clase = getattr(Piece, nombre)
        return clase()

    def decidir(self, tablero, pieza_str, next_pieza_str=None):
        self.grid.grid = tablero.tolist()

        pieza = self.crear_pieza(pieza_str)

        # Evaluación simple (sin lookahead — más rápido y confiable)
        valor, col, rot, _ = self.ia.get_best_choice(pieza)

        # Obtener spawn_col DESPUÉS de la rotación elegida
        pieza.set_current_shape(rot)
        spawn_col = pieza.grid_position

        print(f"Mejor jugada: ({valor}, {col}, {rot}, None)")
        print(f"  → target_col={col}, rot={rot}, spawn_col={spawn_col}, desplazamiento={col - spawn_col}")

        return col, rot, spawn_col
