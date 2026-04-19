from __future__ import annotations

import hashlib

from nonogram.clues import board_to_clues
from nonogram.models import PuzzleResponse, SolverStats
from nonogram.prng import GENERATOR_VERSION, build_rng
from nonogram.solver import solve_nonogram
from nonogram.validator import is_valid_unique_puzzle


DENSITY_BY_SIZE = {
    5: 0.48,
    10: 0.44,
    20: 0.39,
    30: 0.36,
}

MAX_ATTEMPTS = 5000


def generate_solution_board(size: int, seed: int) -> list[list[int]]:
    rng = build_rng(seed, size, GENERATOR_VERSION)
    density = DENSITY_BY_SIZE[size]
    return [
        [1 if rng.random() < density else 0 for _ in range(size)]
        for _ in range(size)
    ]


def build_puzzle_hash(size: int, row_clues: list[list[int]], col_clues: list[list[int]]) -> str:
    payload = f"{size}:{row_clues}:{col_clues}".encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def generate_puzzle(input_seed: int, size: int) -> PuzzleResponse:
    for attempt in range(MAX_ATTEMPTS):
        resolved_seed = input_seed + attempt
        solution = generate_solution_board(size, resolved_seed)
        row_clues, col_clues = board_to_clues(solution)
        result = solve_nonogram(size, row_clues, col_clues)
        if is_valid_unique_puzzle(result):
            return PuzzleResponse(
                input_seed=input_seed,
                resolved_seed=resolved_seed,
                attempt=attempt,
                puzzle_hash=build_puzzle_hash(size, row_clues, col_clues),
                size=size,
                row_clues=row_clues,
                col_clues=col_clues,
                solution=solution,
                solver=SolverStats(
                    unique=result.unique,
                    solve_time_ms=result.solve_time_ms,
                    nodes_visited=result.nodes_visited,
                    solutions_found=result.solutions_found,
                    max_depth=result.max_depth,
                ),
            )
    raise RuntimeError("Failed to generate a unique puzzle within the attempt budget")
