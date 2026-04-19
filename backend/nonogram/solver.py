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


def compute_line_clues(line: list[int] | tuple[int, ...]) -> tuple[int, ...]:
    values = [int(value) for value in line]
    runs: list[int] = []
    current = 0
    for value in values:
        if value == 1:
            current += 1
            continue
        if current > 0:
            runs.append(current)
            current = 0
    if current > 0:
        runs.append(current)
    return tuple(runs)


@lru_cache(maxsize=None)
def line_patterns_for_clue(clue: Clue, line_length: int) -> tuple[int, ...]:
    if not clue:
        return (0,)

    results: list[int] = []

    def build(clue_index: int, position: int, pattern: int) -> None:
        if clue_index == len(clue):
            results.append(pattern)
            return

        remaining_clues = clue[clue_index:]
        remaining_total = sum(remaining_clues)
        remaining_spaces = len(remaining_clues) - 1
        last_start = line_length - remaining_total - remaining_spaces

        for start in range(position, last_start + 1):
            next_pattern = pattern
            block_length = clue[clue_index]
            for bit_index in range(start, start + block_length):
                shift = line_length - 1 - bit_index
                next_pattern |= 1 << shift

            next_position = start + block_length
            if clue_index < len(clue) - 1:
                next_position += 1
            build(clue_index + 1, next_position, next_pattern)

    build(0, 0, 0)
    return tuple(results)


@lru_cache(maxsize=None)
def generate_line_patterns(length: int, clues: Clue) -> tuple[Line, ...]:
    patterns = tuple(
        tuple((pattern >> shift) & 1 for shift in range(length - 1, -1, -1))
        for pattern in line_patterns_for_clue(clues, length)
    )
    return tuple(sorted(patterns, reverse=True))


def prefix_value(pattern: int, *, prefix_len: int, line_length: int) -> int:
    if prefix_len <= 0:
        return 0
    shift = line_length - prefix_len
    return int(pattern >> shift)


@lru_cache(maxsize=None)
def build_column_prefix_sets(col_clues: tuple[Clue, ...], line_length: int) -> tuple[dict[int, set[int]], ...]:
    prefix_sets: list[dict[int, set[int]]] = []
    for clue in col_clues:
        patterns = line_patterns_for_clue(clue, line_length)
        prefix_sets.append(
            {
                prefix_len: {
                    prefix_value(pattern, prefix_len=prefix_len, line_length=line_length)
                    for pattern in patterns
                }
                for prefix_len in range(line_length + 1)
            }
        )
    return tuple(prefix_sets)


def solve_nonogram(
    size: int,
    row_clues: list[list[int]],
    col_clues: list[list[int]],
    deadline: float | None = None,
) -> SolveResult:
    row_clue_tuples = tuple(tuple(clues) for clues in row_clues)
    col_clue_tuples = tuple(tuple(clues) for clues in col_clues)

    if deadline is not None and time.perf_counter() >= deadline:
        raise SolveTimeoutError
    row_candidates = [line_patterns_for_clue(clue, size) for clue in row_clue_tuples]

    if deadline is not None and time.perf_counter() >= deadline:
        raise SolveTimeoutError
    col_prefix_sets = build_column_prefix_sets(col_clue_tuples, size)

    start = time.perf_counter()
    nodes_visited = 0
    max_depth = 0
    solutions_found = 0

    def search(row_index: int, prefixes: list[int]) -> None:
        nonlocal nodes_visited, max_depth, solutions_found
        if deadline is not None and time.perf_counter() >= deadline:
            raise SolveTimeoutError
        if solutions_found >= 2:
            return
        max_depth = max(max_depth, row_index)
        if row_index >= size:
            solutions_found += 1
            return

        for row_pattern in row_candidates[row_index]:
            nodes_visited += 1
            next_prefixes: list[int] = []
            valid = True
            for col_index in range(size):
                bit = int((row_pattern >> (size - 1 - col_index)) & 1)
                next_prefix = (prefixes[col_index] << 1) | bit
                if next_prefix not in col_prefix_sets[col_index][row_index + 1]:
                    valid = False
                    break
                next_prefixes.append(next_prefix)
            if valid:
                search(row_index + 1, next_prefixes)
                if solutions_found >= 2:
                    return

    search(0, [0] * size)
    elapsed_ms = (time.perf_counter() - start) * 1000

    return SolveResult(
        unique=solutions_found == 1,
        solve_time_ms=elapsed_ms,
        nodes_visited=nodes_visited,
        solutions_found=solutions_found,
        max_depth=max_depth,
    )
