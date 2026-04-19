from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from nonogram.clues import board_to_clues
from nonogram.solver import solve_nonogram


SIZE = 4
CELL_COUNT = SIZE * SIZE


@dataclass
class VerificationSummary:
    total_boards: int
    unique_clue_sets: int
    matching_clue_sets: int
    mismatching_clue_sets: int
    avg_solver_time_ms: float


def int_to_board(value: int, size: int) -> list[list[int]]:
    bits = [(value >> shift) & 1 for shift in range(size * size - 1, -1, -1)]
    return [
        bits[row * size : (row + 1) * size]
        for row in range(size)
    ]


def normalize_clues(row_clues: list[list[int]], col_clues: list[list[int]]) -> tuple[tuple[tuple[int, ...], ...], tuple[tuple[int, ...], ...]]:
    return (
        tuple(tuple(clue) for clue in row_clues),
        tuple(tuple(clue) for clue in col_clues),
    )


def main() -> None:
    clue_solution_counts: dict[
        tuple[tuple[tuple[int, ...], ...], tuple[tuple[int, ...], ...]],
        int,
    ] = defaultdict(int)

    for value in range(1 << CELL_COUNT):
        board = int_to_board(value, SIZE)
        row_clues, col_clues = board_to_clues(board)
        clue_key = normalize_clues(row_clues, col_clues)
        clue_solution_counts[clue_key] += 1

    mismatches: list[dict[str, object]] = []
    solver_times_ms: list[float] = []

    for clue_key, true_solution_count in clue_solution_counts.items():
        row_clues = [list(clue) for clue in clue_key[0]]
        col_clues = [list(clue) for clue in clue_key[1]]

        started_at = time.perf_counter()
        solve_result = solve_nonogram(SIZE, row_clues, col_clues, deadline=None)
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        solver_times_ms.append(elapsed_ms)

        expected_unique = true_solution_count == 1
        actual_unique = solve_result.unique
        expected_bucket = min(true_solution_count, 2)
        actual_bucket = min(solve_result.solutions_found, 2)

        if expected_unique != actual_unique or expected_bucket != actual_bucket:
            mismatches.append(
                {
                    "row_clues": row_clues,
                    "col_clues": col_clues,
                    "true_solution_count": true_solution_count,
                    "solver_solutions_found": solve_result.solutions_found,
                    "solver_unique": solve_result.unique,
                    "solver_nodes": solve_result.nodes_visited,
                }
            )

    summary = VerificationSummary(
        total_boards=1 << CELL_COUNT,
        unique_clue_sets=len(clue_solution_counts),
        matching_clue_sets=len(clue_solution_counts) - len(mismatches),
        mismatching_clue_sets=len(mismatches),
        avg_solver_time_ms=(sum(solver_times_ms) / len(solver_times_ms)) if solver_times_ms else 0.0,
    )

    print("summary", summary)
    if mismatches:
        print("mismatches")
        for row in mismatches[:20]:
            print(row)
    else:
        print("solver matches brute-force truth for all 4x4 clue sets")


if __name__ == "__main__":
    main()
