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
        return clase( )

    def decidir(self, tablero, pieza_str):
        self.grid.grid = tablero.tolist()

        pieza = self.crear_pieza(pieza_str)

        valor, col, rot, _ = self.ia.get_best_choice(pieza)

        # IMPORTANTE: obtener posición de spawn DESPUÉS de la rotación elegida,
        # porque rotar cambia la posición de la pieza (ej: I vertical se mueve de col 3 a col 5)
        pieza.set_current_shape(rot)
        spawn_col = pieza.grid_position

        print(f"  → target_col={col}, rot={rot}, spawn_col={spawn_col}, desplazamiento={col - spawn_col}")

        return col, rot, spawn_col
