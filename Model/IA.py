import numpy as np
from Model.Grid import Grid
import Model.Pieces as Piece

class Tetris_IA:
    def __init__(self, grid: Grid):
        self.grid = grid

    def compute_piece_expand(self, piece: Piece):
        """Evalúa todas las columnas posibles sin rotar"""
        width = piece.get_optimized_current_matrix().shape[1]
        max_cols = 10 - width + 1

        best_value = float('-inf')
        best_col = 0
        best_indices = None

        for col in range(max_cols):
            heuristicas, indices = self.grid.calculate_heuristics(piece, col)
            valor = sum(heuristicas)

            if valor > best_value:
                best_value = valor
                best_col = col
                best_indices = indices
            elif valor == best_value:
                # Desempate: preferir columna más cercana al centro (col 4-5)
                dist_actual = abs(best_col - 4.5)
                dist_nueva = abs(col - 4.5)
                if dist_nueva < dist_actual:
                    best_col = col
                    best_indices = indices

        return best_value, best_col, best_indices

    def compute_piece_all_rotations(self, piece: Piece):
        """Evalúa todas las rotaciones"""
        resultados = []

        for rot in range(piece.computable_shapes):
            piece.set_current_shape(rot)
            valor, col, indices = self.compute_piece_expand(piece)
            resultados.append((valor, col, rot, indices))

        piece.set_current_shape(0)  # reset

        return resultados

    def get_best_choice(self, piece: Piece):
        """Devuelve (valor, columna, rotación, indices)"""
        opciones = self.compute_piece_all_rotations(piece)

        mejor = max(opciones, key=lambda x: x[0])

        print("Mejor jugada:", mejor)

        return mejor