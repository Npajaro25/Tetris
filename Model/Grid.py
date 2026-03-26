import numpy as np
import copy

class Grid:
    def __init__(self):
        self.rows = 20
        self.cols = 10
        self.grid = [[0]*self.cols for _ in range(self.rows)]

    def clone(self):
        g = Grid()
        g.grid = copy.deepcopy(self.grid)
        return g

    def place_piece(self, piece_matrix, col):
        """Simula caída de la pieza. Retorna grid o None."""
        grid = np.array(self.grid)
        piece_h, piece_w = piece_matrix.shape

        for row in range(self.rows - piece_h + 1):
            if self.check_collision(grid, piece_matrix, row, col):
                final_row = row - 1
                break
        else:
            final_row = self.rows - piece_h

        if final_row < 0:
            return None

        grid = self.merge(grid, piece_matrix, final_row, col)
        return grid

    def place_piece_with_row(self, piece_matrix, col):
        """Simula caída y devuelve (grid, landing_row) para landing height.
        landing_row es el índice de fila donde queda la parte superior de la pieza."""
        grid = np.array(self.grid)
        piece_h, piece_w = piece_matrix.shape

        for row in range(self.rows - piece_h + 1):
            if self.check_collision(grid, piece_matrix, row, col):
                final_row = row - 1
                break
        else:
            final_row = self.rows - piece_h

        if final_row < 0:
            return None, -1

        grid = self.merge(grid, piece_matrix, final_row, col)
        return grid, final_row

    def check_collision(self, grid, piece, row, col):
        for i in range(piece.shape[0]):
            for j in range(piece.shape[1]):
                if piece[i][j] != 0:
                    if row+i >= self.rows or col+j >= self.cols or grid[row+i][col+j] != 0:
                        return True
        return False

    def merge(self, grid, piece, row, col):
        new_grid = grid.copy()
        for i in range(piece.shape[0]):
            for j in range(piece.shape[1]):
                if piece[i][j] != 0:
                    new_grid[row+i][col+j] = 1
        return new_grid

    def clear_lines(self, grid):
        """Elimina filas completas y devuelve (nuevo_grid, cantidad_eliminadas)"""
        lines_cleared = 0
        new_rows = []
        for row in grid:
            if all(cell != 0 for cell in row):
                lines_cleared += 1
            else:
                new_rows.append(list(row))
        while len(new_rows) < self.rows:
            new_rows.insert(0, [0]*self.cols)
        return np.array(new_rows), lines_cleared

    # ========== HEURÍSTICAS DELLACHERIE/THIERY ========== #

    def calculate_heuristics(self, piece, col):
        """Algoritmo Dellacherie/Thiery — 6 features optimizadas.
        Pesos del paper 'Improvements on Learning Tetris with
        Cross-Entropy' (Thiery & Scherrer, 2009)."""
        piece_matrix = piece.get_optimized_current_matrix()
        piece_h = piece_matrix.shape[0]

        result = self.place_piece_with_row(piece_matrix, col)
        if result[0] is None:
            return [-9999], None
        placed_grid, landing_row = result

        # Contar líneas completadas y celdas de la pieza en ellas
        lines_cleared = 0
        piece_cells_eroded = 0
        for r in range(landing_row, min(landing_row + piece_h, self.rows)):
            if all(placed_grid[r][c] != 0 for c in range(self.cols)):
                lines_cleared += 1
                for c in range(self.cols):
                    pc = c - col
                    pr = r - landing_row
                    if 0 <= pc < piece_matrix.shape[1] and 0 <= pr < piece_h:
                        if piece_matrix[pr][pc] != 0:
                            piece_cells_eroded += 1

        # Limpiar líneas completas
        new_grid, _ = self.clear_lines(placed_grid)

        # Feature 1: Landing height — altura desde el FONDO del tablero
        # Centro de la pieza: (landing_row + landing_row + piece_h - 1) / 2
        # Altura desde fondo: self.rows - centro
        landing_height = self.rows - landing_row - (piece_h / 2.0)

        # Usar el grid modificado para los cálculos (col 9 ignorada en features espaciales)
        height_cols = self._get_column_heights(new_grid)
        alturas_0_8 = height_cols[:9]
        
        # 1. Aggregate Height (0-8)
        aggregate_height = sum(alturas_0_8)
        
        # 2. Bumpiness (0-8)
        bumpiness = 0
        for i in range(8):  # Diferencia entre col i y col i+1 (hasta col 8)
            bumpiness += abs(alturas_0_8[i] - alturas_0_8[i+1])
            
        # 3. Holes (0-8)
        holes = self._get_holes(new_grid)
        
        # Pesos heurísticos (Multiplicados por 100 para escalar con la lógica ofensiva)
        # Basados en pesos estándar de construcción plana (optimizados por algoritmos genéticos)
        score_base = (-51.0 * aggregate_height) + (-18.4 * bumpiness) + (-35.6 * holes)
        
        # ========== OFFENSIVE BLITZ SCORING (EL-TETRIS B2B STYLE) ========== #
        score_offensive = 0
        
        # Determinar altura máxima del tablero para el "Umbral de Pánico"
        # Usamos new_grid sin considerar la columna 9 (el pozo)
        height_cols = self._get_column_heights(new_grid)
        max_h = max(height_cols[:9]) if height_cols else 0
        
        # 1. EL POZO (RIGHT WELL): La columna 9 DEBE estar vacía
        h9 = height_cols[9]
        if h9 > 0:
            # Si tapamos el pozo sin hacer Tetris, castigo severo.
            if lines_cleared < 4:
                score_offensive -= 500 * h9
        
        # 2. SISTEMA DE RECOMPENSAS POR LÍNEAS Y CASTIGO POR HUECOS
        if lines_cleared == 4:
            # TETRIS
            score_offensive += 3000
        elif lines_cleared > 0:
            # CASTIGO POR QUEMAR LÍNEAS
            # Debe ser MENOR al castigo por huecos (-500) para que
            # prefiera quemar línea antes que dejar un hueco.
            score_offensive -= 100 * lines_cleared
            
        # 2.5 PERFECT CLEAR DREAMS (ALL CLEAR)
        # Si limpiar estas líneas resulta en un tablero matemáticamente vacío:
        if lines_cleared > 0 and not np.any(new_grid):
            # El juego da 3500 puntos oficiales.
            # Si ve un Perfect Clear a 2 piezas de distancia, sacrificará todo por él.
            score_offensive += 50000
                
        # 3. MANTENER EL TABLERO SANO Y PLANO PARA TETRISES
        # El rango de altura destruye implacablemente la tendencia natural de la IA
        # a construir escaleras infinitas en la pared izquierda.
        if alturas_0_8:
            rango_altura = max(alturas_0_8) - min(alturas_0_8)
            score_offensive -= 100.0 * rango_altura
            
        # Castigo BRUTAL (-500) para que nunca deje huecos.
        score_offensive -= 500 * holes

        heuristicas = [score_base, score_offensive]
        return heuristicas, None

    # ========== FEATURE FUNCTIONS ========== #

    def _get_holes(self, grid):
        """Cuenta huecos en las columnas 0-8. Un hueco es un 0 con al menos un 1 por encima."""
        holes = 0
        limit_col = self.cols - 1
        for col in range(limit_col):
            block_found = False
            for row in range(self.rows):
                if grid[row][col] != 0:
                    block_found = True
                elif block_found:
                    holes += 1
        return holes

    # ========== HELPERS ========== #

    def _get_column_heights(self, grid):
        heights = []
        for col in range(self.cols):
            h = 0
            for row in range(self.rows):
                if grid[row][col] != 0:
                    h = self.rows - row
                    break
            heights.append(h)
        return heights

    def get_aggregate_height(self, grid):
        return sum(self._get_column_heights(grid))

    def get_holes(self, grid):
        return self._get_holes(grid)

    def get_complete_lines(self, grid):
        return sum(1 for row in grid if all(cell != 0 for cell in row))

    def get_bumpiness(self, grid):
        heights = self._get_column_heights(grid)
        return self.get_bumpiness_from_heights(heights)

    def get_bumpiness_from_heights(self, heights):
        bumpiness = 0
        for i in range(len(heights)-1):
            bumpiness += abs(heights[i] - heights[i+1])
        return bumpiness