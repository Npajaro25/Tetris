import sys
from Model.Grid import Grid
from Model.IA import Tetris_IA
import Model.Pieces as Pieces
import numpy as np

def run_test():
    grid = Grid()
    t_piece = Pieces.Fucsia_T()
    
    print("Testing T Piece on Empty Board:")
    for rot in range(t_piece.computable_shapes):
        t_piece.set_current_shape(rot)
        for col in range(10 - t_piece.get_optimized_current_matrix().shape[1] + 1):
            heuristicas, indices = grid.calculate_heuristics(t_piece, col)
            total = sum(heuristicas)
            if col in [0, 5]:
                print(f"Col {col}, Rot {rot}: Base={heuristicas[0]}, Off={heuristicas[1]}, Total={total}")

    print("\nSimulating build on left (T rot 0 at col 0):")
    t_piece.set_current_shape(0)
    m = t_piece.get_optimized_current_matrix()
    grid.grid = grid.place_piece(m, 0).tolist()
    
    print("Placed T:")
    print(np.array(grid.grid))
    
    t_piece2 = Pieces.Fucsia_T()
    for rot in range(t_piece2.computable_shapes):
        t_piece2.set_current_shape(rot)
        for col in range(10 - t_piece2.get_optimized_current_matrix().shape[1] + 1):
            heuristicas, _ = grid.calculate_heuristics(t_piece2, col)
            if col in [0, 5]:
                print(f"Col {col}, Rot {rot}: Base={heuristicas[0]}, Off={heuristicas[1]}, Total={sum(heuristicas)}")

if __name__ == "__main__":
    run_test()
