from __future__ import annotations

from pathlib import Path
from statistics import mean
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from nonogram.clues import board_to_clues
from nonogram.generator import DEFAULT_DENSITY
from nonogram.prng import GENERATOR_VERSION, build_rng
from experiments.other_solver.solver_impl import (
    compute_board_clues,
    decode_padded_clues,
    has_unique_nonogram_solution,
)


SIZE = 10
SEEDS = [12345, 20250419, 713231167, 670789976, 42424242]
MAX_ATTEMPTS = 5000
TOTAL_TIMEOUT_SECONDS = 10.0


def generate_solution_board(size: int, seed: int) -> list[list[int]]:
    rng = build_rng(seed, size, GENERATOR_VERSION)
    return [
        [1 if rng.random() < DEFAULT_DENSITY else 0 for _ in range(size)]
        for _ in range(size)
    ]


def run_trial(input_seed: int) -> dict[str, int | float | str | None]:
    started_at = time.perf_counter()
    for attempt in range(MAX_ATTEMPTS):
        if time.perf_counter() - started_at >= TOTAL_TIMEOUT_SECONDS:
            return {
                "seed": input_seed,
                "status": "timeout",
                "attempt": attempt,
                "elapsed_ms": round((time.perf_counter() - started_at) * 1000, 2),
                "resolved_seed": None,
            }

        resolved_seed = input_seed + attempt
        board = generate_solution_board(SIZE, resolved_seed)

        # Sanity check that clue extraction matches both implementations.
        main_row_clues, main_col_clues = board_to_clues(board)
        other_row_clues, other_col_clues = compute_board_clues(board)
        decoded_other_rows = tuple(decode_padded_clues(clue) for clue in other_row_clues)
        decoded_other_cols = tuple(decode_padded_clues(clue) for clue in other_col_clues)
        if tuple(tuple(clue) for clue in main_row_clues) != decoded_other_rows:
            raise RuntimeError("row clue mismatch between implementations")
        if tuple(tuple(clue) for clue in main_col_clues) != decoded_other_cols:
            raise RuntimeError("col clue mismatch between implementations")

        if has_unique_nonogram_solution(other_row_clues, other_col_clues):
            return {
                "seed": input_seed,
                "status": "ok",
                "attempt": attempt,
                "elapsed_ms": round((time.perf_counter() - started_at) * 1000, 2),
                "resolved_seed": resolved_seed,
            }

    return {
        "seed": input_seed,
        "status": "attempt_limit",
        "attempt": MAX_ATTEMPTS,
        "elapsed_ms": round((time.perf_counter() - started_at) * 1000, 2),
        "resolved_seed": None,
    }


def main() -> None:
    rows = [run_trial(seed) for seed in SEEDS]
    for row in rows:
        print(row)

    oks = [row for row in rows if row["status"] == "ok"]
    print(
        "summary",
        {
            "density": DEFAULT_DENSITY,
            "successes": len(oks),
            "avg_attempt": round(mean(row["attempt"] for row in oks), 2) if oks else None,
            "avg_elapsed_ms": round(mean(row["elapsed_ms"] for row in oks), 2) if oks else None,
        },
    )


if __name__ == "__main__":
    main()
