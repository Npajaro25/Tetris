import numpy as np
from Model.Grid import Grid
import Model.Pieces as Piece

class Tetris_IA:
    def __init__(self, grid: Grid):
        self.grid = grid

    def compute_piece_expand(self, piece: Piece, grid=None):
        """Evalúa todas las columnas posibles sin rotar.
        Si se pasa un grid custom, lo usa en vez del principal."""
        target_grid = grid if grid is not None else self.grid
        width = piece.get_optimized_current_matrix().shape[1]
        max_cols = 10 - width + 1

        best_value = float('-inf')
        best_col = 0
        best_indices = None

        for col in range(max_cols):
            heuristicas, indices = target_grid.calculate_heuristics(piece, col)
            valor = sum(heuristicas)

            if valor > best_value:
                best_value = valor
                best_col = col
                best_indices = indices
            elif valor == best_value:
                dist_actual = abs(best_col - 4.5)
                dist_nueva = abs(col - 4.5)
                if dist_nueva < dist_actual:
                    best_col = col
                    best_indices = indices

        return best_value, best_col, best_indices

    def compute_piece_all_rotations(self, piece: Piece, grid=None):
        """Evalúa todas las rotaciones."""
        resultados = []
        for rot in range(piece.computable_shapes):
            piece.set_current_shape(rot)
            valor, col, indices = self.compute_piece_expand(piece, grid)
            resultados.append((valor, col, rot, indices))
        piece.set_current_shape(0)
        return resultados

    def get_best_choice(self, piece: Piece):
        """Devuelve (valor, columna, rotación, indices) sin lookahead."""
        opciones = self.compute_piece_all_rotations(piece)
        mejor = max(opciones, key=lambda x: x[0])
        return mejor

    def get_best_choice_lookahead(self, piece: Piece, next_piece: Piece):
        """2-piece lookahead: evalúa cada colocación de la pieza actual,
        simula colocarla, y luego busca la mejor colocación de next_piece
        sobre ese tablero. Score = current + 0.5 * best_next."""
        best_total = float('-inf')
        best_col = 0
        best_rot = 0

        for rot in range(piece.computable_shapes):
            piece.set_current_shape(rot)
            piece_matrix = piece.get_optimized_current_matrix()
            width = piece_matrix.shape[1]
            max_cols = 10 - width + 1

            for col in range(max_cols):
                # Evaluar colocación actual
                heuristicas_actual, _ = self.grid.calculate_heuristics(piece, col)
                
                # Si place_piece falló, retorna [-9999, -9999]
                if heuristicas_actual[0] == -9999:
                    continue
                
                score_actual = sum(heuristicas_actual)

                # Simular colocación y limpiar líneas
                new_grid_arr = self.grid.place_piece(piece_matrix, col)
                if new_grid_arr is None:
                    continue

                new_grid_arr, _ = self.grid.clear_lines(new_grid_arr)

                # Crear grid temporal con el tablero post-colocación
                temp_grid = Grid()
                temp_grid.grid = new_grid_arr.tolist()

                # Buscar mejor colocación de next_piece sobre este tablero
                temp_ia = Tetris_IA(temp_grid)
                opciones_next = temp_ia.compute_piece_all_rotations(next_piece)
                best_next = max(opciones_next, key=lambda x: x[0])
                score_next = best_next[0]

                # Score combinado (next piece vale 50% para no ser miope)
                total = score_actual + 0.5 * score_next

                if total > best_total:
                    best_total = total
                    best_col = col
                    best_rot = rot

        piece.set_current_shape(0)
        return best_total, best_col, best_rot, None