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
        """Simula caída de la pieza"""
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

    # ---------------- HEURÍSTICAS ---------------- #

    def calculate_heuristics(self, piece, col):
        piece_matrix = piece.get_optimized_current_matrix()

        new_grid = self.place_piece(piece_matrix, col)

        if new_grid is None:
            return [-9999], None

        # Eliminar líneas completas ANTES de evaluar heurísticas
        new_grid, lineas = self.clear_lines(new_grid)

        heights = self._get_column_heights(new_grid)
        altura_agg = sum(heights)
        max_height = max(heights)
        huecos = self.get_holes(new_grid)
        bumpiness = self.get_bumpiness_from_heights(heights)

        # Pesos finales — fuertemente penalizar torres y recompensar líneas
        heuristicas = [
            -0.510066 * altura_agg,
            +8.000000 * lineas,
            -0.800000 * huecos,
            -0.300000 * bumpiness,
            -1.500000 * max_height,   # ANTI-TORRE: penaliza la columna más alta
        ]

        return heuristicas, None

    def _get_column_heights(self, grid):
        """Devuelve la altura de cada columna como lista."""
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
        holes = 0
        for col in range(self.cols):
            block_found = False
            for row in range(self.rows):
                if grid[row][col] != 0:
                    block_found = True
                elif block_found:
                    holes += 1
        return holes

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