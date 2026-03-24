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

    def _get_best_choice_lookahead_recursive(self, piece: Piece, next_pieces: list[Piece], base_score=0.0, depth=1):
        """Función recursiva para N-piece lookahead.
        Retorna (mejor_score_total, best_col_inicial, best_rot_inicial)."""
        opciones_actuales = []

        for rot in range(piece.computable_shapes):
            piece.set_current_shape(rot)
            piece_matrix = piece.get_optimized_current_matrix()
            width = piece_matrix.shape[1]
            max_cols = 10 - width + 1

            for col in range(max_cols):
                heuristicas_actual, _ = self.grid.calculate_heuristics(piece, col)
                if heuristicas_actual[0] == -9999:
                    continue
                
                score_actual = sum(heuristicas_actual)
                opciones_actuales.append((score_actual, col, rot, piece_matrix))
        
        piece.set_current_shape(0)

        if not opciones_actuales:
            return float('-inf'), 0, 0
            
        # Si ya no hay más piezas a futuro para evaluar
        if not next_pieces:
            mejor = max(opciones_actuales, key=lambda x: x[0])
            return mejor[0], mejor[1], mejor[2]

        # BEAM SEARCH: Top K para profundizar
        TOP_K = 3
        opciones_actuales.sort(key=lambda x: x[0], reverse=True)
        mejores_opciones = opciones_actuales[:TOP_K]

        best_total = float('-inf')
        best_col = 0
        best_rot = 0
        
        next_p = next_pieces[0]
        rest_next = next_pieces[1:]
        
        # Descuento por profundidad (ej. piece 2 vale 50%, piece 3 vale 25%)
        # Penalizamos un poco el peso de las decisiones futuras lejanas.
        discount = 0.5 

        for score_actual, col, rot, piece_matrix in mejores_opciones:
            new_grid_arr = self.grid.place_piece(piece_matrix, col)
            if new_grid_arr is None:
                continue

            new_grid_arr, _ = self.grid.clear_lines(new_grid_arr)
            temp_grid = Grid()
            temp_grid.grid = new_grid_arr.tolist()
            temp_ia = Tetris_IA(temp_grid)
            
            # Llamada recursiva para obtener el mejor score sumado del futuro
            score_futuro, _, _ = temp_ia._get_best_choice_lookahead_recursive(
                next_p, rest_next, depth=depth+1
            )
            
            total = score_actual + (discount * score_futuro)

            if total > best_total:
                best_total = total
                best_col = col
                best_rot = rot

        return best_total, best_col, best_rot

    def get_best_choice_lookahead(self, piece: Piece, next_pieces: list[Piece]):
        """N-piece lookahead optimizado con BEAM SEARCH (Top-K recursivo).
        Acepta una lista de N piezas futuras.
        Retorna (score, col, rot, None)."""
        
        # Validación de seguridad si la lista viene vacía
        if not next_pieces:
            mejor = self.get_best_choice(piece) # fallback a 1-piece
            return mejor[0], mejor[1], mejor[2], None
            
        valor, col, rot = self._get_best_choice_lookahead_recursive(piece, next_pieces)
        return valor, col, rot, None