from __future__ import annotations

import hashlib
import time
from collections.abc import Callable

from nonogram.clues import board_to_clues
from nonogram.models import PuzzleResponse, SolverStats, TimeoutResponse
from nonogram.prng import GENERATOR_VERSION, build_rng
from nonogram.solver import SolveTimeoutError, solve_nonogram
from nonogram.validator import is_valid_unique_puzzle


DEFAULT_DENSITY = 0.5

MAX_ATTEMPTS = 5000
TIMEOUT_SECONDS = 10.0
PER_PUZZLE_SOLVE_TIMEOUT_SECONDS = 5.0


def generate_solution_board(size: int, seed: int) -> list[list[int]]:
    rng = build_rng(seed, size, GENERATOR_VERSION)
    return [
        [1 if rng.random() < DEFAULT_DENSITY else 0 for _ in range(size)]
        for _ in range(size)
    ]


def build_puzzle_hash(size: int, row_clues: list[list[int]], col_clues: list[list[int]]) -> str:
    payload = f"{size}:{row_clues}:{col_clues}".encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


ProgressCallback = Callable[[int, int, float], None]


def generate_puzzle(
    input_seed: int,
    size: int,
    progress_callback: ProgressCallback | None = None,
) -> PuzzleResponse | TimeoutResponse:
    started_at = time.perf_counter()
    for attempt in range(MAX_ATTEMPTS):
        elapsed_seconds = time.perf_counter() - started_at
        if elapsed_seconds >= TIMEOUT_SECONDS:
            return TimeoutResponse(
                input_seed=input_seed,
                size=size,
                timeout_seconds=TIMEOUT_SECONDS,
                attempts_tried=attempt,
                elapsed_ms=elapsed_seconds * 1000,
                message=f"在 {TIMEOUT_SECONDS:g} 秒内没有找到唯一解谜题，请重试或换一个 seed。",
            )
        resolved_seed = input_seed + attempt
        if progress_callback is not None:
            progress_callback(attempt + 1, resolved_seed, elapsed_seconds * 1000)
        solution = generate_solution_board(size, resolved_seed)
        row_clues, col_clues = board_to_clues(solution)
        solver_deadline = time.perf_counter() + PER_PUZZLE_SOLVE_TIMEOUT_SECONDS
        try:
            result = solve_nonogram(size, row_clues, col_clues, deadline=solver_deadline)
        except SolveTimeoutError:
            continue
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
    elapsed_seconds = time.perf_counter() - started_at
    return TimeoutResponse(
        input_seed=input_seed,
        size=size,
        timeout_seconds=TIMEOUT_SECONDS,
        attempts_tried=MAX_ATTEMPTS,
        elapsed_ms=elapsed_seconds * 1000,
        message="在最大尝试次数内没有找到唯一解谜题，请重试或换一个 seed。",
    )
