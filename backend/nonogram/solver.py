from __future__ import annotations

import time
from functools import lru_cache
from typing import NamedTuple


Line = tuple[int, ...]
Clue = tuple[int, ...]


class SolveTimeoutError(Exception):
    """Raised when a single solver run exceeds its deadline."""


class SolveResult(NamedTuple):
    unique: bool
    solve_time_ms: float
    nodes_visited: int
    solutions_found: int
    max_depth: int


@lru_cache(maxsize=None)
def generate_line_patterns(length: int, clues: Clue) -> tuple[Line, ...]:
    if not clues:
        return (tuple(0 for _ in range(length)),)

    results: list[Line] = []
    clue_total = sum(clues)
    min_spaces = len(clues) - 1
    max_start = length - clue_total - min_spaces

    def build(clue_index: int, position: int, current: list[int]) -> None:
        if clue_index == len(clues):
            results.append(tuple(current + [0] * (length - len(current))))
            return

        remaining_clues = clues[clue_index:]
        remaining_total = sum(remaining_clues)
        remaining_spaces = len(remaining_clues) - 1
        last_start = length - remaining_total - remaining_spaces

        for start in range(position, last_start + 1):
            prefix = current + [0] * (start - len(current)) + [1] * clues[clue_index]
            next_position = len(prefix)
            if clue_index < len(clues) - 1:
                prefix.append(0)
                next_position += 1
            build(clue_index + 1, next_position, prefix)

    build(0, 0, [])
    return tuple(results)


@lru_cache(maxsize=None)
def prefix_is_feasible(prefix: Line, clues: Clue, total_length: int) -> bool:
    prefix_length = len(prefix)

    @lru_cache(maxsize=None)
    def dp(position: int, clue_index: int, run_length: int) -> bool:
        if position == prefix_length:
            return can_finish(clue_index, run_length, total_length - prefix_length)

        value = prefix[position]

        if value == 1:
            if clue_index >= len(clues):
                return False
            next_run = run_length + 1
            if next_run > clues[clue_index]:
                return False
            return dp(position + 1, clue_index, next_run)

        if run_length > 0:
            if clue_index >= len(clues) or run_length != clues[clue_index]:
                return False
            return dp(position + 1, clue_index + 1, 0)

        return dp(position + 1, clue_index, 0)

    @lru_cache(maxsize=None)
    def can_finish(clue_index: int, run_length: int, cells_left: int) -> bool:
        if cells_left < 0:
            return False

        if run_length > 0:
            if clue_index >= len(clues) or run_length > clues[clue_index]:
                return False
            remaining = (clues[clue_index] - run_length,) + clues[clue_index + 1 :]
        else:
            remaining = clues[clue_index:]

        if not remaining:
            return True

        min_required = sum(remaining) + max(0, len(remaining) - 1)
        return min_required <= cells_left

    return dp(0, 0, 0)


def solve_nonogram(
    size: int,
    row_clues: list[list[int]],
    col_clues: list[list[int]],
    deadline: float | None = None,
) -> SolveResult:
    row_patterns = [
        generate_line_patterns(size, tuple(clues))
        for clues in row_clues
    ]
    col_clue_tuples = [tuple(clues) for clues in col_clues]

    start = time.perf_counter()
    nodes_visited = 0
    max_depth = 0
    solutions_found = 0

    def search(row_index: int, column_prefixes: tuple[Line, ...]) -> None:
        nonlocal nodes_visited, max_depth, solutions_found
        if deadline is not None and time.perf_counter() >= deadline:
            raise SolveTimeoutError
        if solutions_found >= 2:
            return
        max_depth = max(max_depth, row_index)
        if row_index == size:
            solutions_found += 1
            return

        for pattern in row_patterns[row_index]:
            nodes_visited += 1
            next_prefixes: list[Line] = []
            valid = True
            for col_index, cell in enumerate(pattern):
                next_prefix = column_prefixes[col_index] + (cell,)
                if not prefix_is_feasible(next_prefix, col_clue_tuples[col_index], size):
                    valid = False
                    break
                next_prefixes.append(next_prefix)
            if valid:
                search(row_index + 1, tuple(next_prefixes))
                if solutions_found >= 2:
                    return

    initial_prefixes = tuple(tuple() for _ in range(size))
    search(0, initial_prefixes)
    elapsed_ms = (time.perf_counter() - start) * 1000

    return SolveResult(
        unique=solutions_found == 1,
        solve_time_ms=elapsed_ms,
        nodes_visited=nodes_visited,
        solutions_found=solutions_found,
        max_depth=max_depth,
    )
