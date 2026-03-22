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
                    if row+i >= self.rows or grid[row+i][col+j] != 0:
                        return True
        return False

    def merge(self, grid, piece, row, col):
        new_grid = grid.copy()
        for i in range(piece.shape[0]):
            for j in range(piece.shape[1]):
                if piece[i][j] != 0:
                    new_grid[row+i][col+j] = 1
        return new_grid

    # ---------------- HEURÍSTICAS ---------------- #

    def calculate_heuristics(self, piece, col):
        piece_matrix = piece.get_optimized_current_matrix()

        new_grid = self.place_piece(piece_matrix, col)

        if new_grid is None:
            return [-9999], None

        altura = self.get_height(new_grid)
        huecos = self.get_holes(new_grid)
        lineas = self.get_complete_lines(new_grid)
        bumpiness = self.get_bumpiness(new_grid)

        # pesos clásicos
        heuristicas = [
            -0.5 * altura,
            -0.7 * huecos,
            1.0 * lineas,
            -0.3 * bumpiness
        ]

        return heuristicas, None

    def get_height(self, grid):
        for i, row in enumerate(grid):
            if any(row):
                return self.rows - i
        return 0

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
        heights = []
        for col in range(self.cols):
            h = 0
            for row in range(self.rows):
                if grid[row][col] != 0:
                    h = self.rows - row
                    break
            heights.append(h)

        bumpiness = 0
        for i in range(len(heights)-1):
            bumpiness += abs(heights[i] - heights[i+1])

        return bumpiness