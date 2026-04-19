from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import random


EMPTY = 0
FILLED = 1


def default_max_clue_len(board_size: int) -> int:
    return (int(board_size) + 1) // 2


def compute_line_clues(line: list[int] | tuple[int, ...]) -> tuple[int, ...]:
    values = [int(value) for value in line]
    runs: list[int] = []
    current = 0
    for value in values:
        if value == FILLED:
            current += 1
            continue
        if current > 0:
            runs.append(current)
            current = 0
    if current > 0:
        runs.append(current)
    return tuple(runs)


def encode_clues(clues: tuple[int, ...], max_len: int) -> tuple[int, ...]:
    if len(clues) > max_len:
        raise ValueError(f"clue length {len(clues)} exceeds max_len={max_len}")
    padding = (0,) * (max_len - len(clues))
    return padding + clues


def decode_padded_clues(clue_tensor: tuple[int, ...] | list[int]) -> tuple[int, ...]:
    return tuple(int(value) for value in clue_tensor if int(value) > 0)


def compute_board_clues(
    solution: list[list[int]],
    *,
    max_clue_len: int | None = None,
) -> tuple[list[tuple[int, ...]], list[tuple[int, ...]]]:
    board_size = len(solution)
    max_clue_len = default_max_clue_len(board_size) if max_clue_len is None else max_clue_len
    row_clues = [
        encode_clues(compute_line_clues(tuple(solution[row])), max_len=max_clue_len)
        for row in range(board_size)
    ]
    col_clues = [
        encode_clues(
            compute_line_clues(tuple(solution[row][col] for row in range(board_size))),
            max_len=max_clue_len,
        )
        for col in range(board_size)
    ]
    return row_clues, col_clues


@lru_cache(maxsize=None)
def line_patterns_for_clue(clue: tuple[int, ...], line_length: int) -> tuple[int, ...]:
    matches: list[int] = []
    for pattern in range(1 << line_length):
        bits = tuple((pattern >> shift) & 1 for shift in range(line_length - 1, -1, -1))
        if compute_line_clues(bits) == clue:
            matches.append(pattern)
    return tuple(matches)


def prefix_value(pattern: int, *, prefix_len: int, line_length: int) -> int:
    if prefix_len <= 0:
        return 0
    shift = line_length - prefix_len
    return int(pattern >> shift)


def count_nonogram_solutions(
    row_clues: list[tuple[int, ...]],
    col_clues: list[tuple[int, ...]],
    *,
    max_count: int = 2,
) -> int:
    board_size = len(row_clues)
    decoded_rows = [decode_padded_clues(clue) for clue in row_clues]
    decoded_cols = [decode_padded_clues(clue) for clue in col_clues]
    row_candidates = [line_patterns_for_clue(clue, board_size) for clue in decoded_rows]
    col_candidates = [line_patterns_for_clue(clue, board_size) for clue in decoded_cols]
    col_prefix_sets = [
        {
            prefix_len: {
                prefix_value(pattern, prefix_len=prefix_len, line_length=board_size)
                for pattern in patterns
            }
            for prefix_len in range(board_size + 1)
        }
        for patterns in col_candidates
    ]

    solution_count = 0

    def dfs(row_index: int, prefixes: list[int]) -> None:
        nonlocal solution_count
        if solution_count >= max_count:
            return
        if row_index >= board_size:
            solution_count += 1
            return
        for row_pattern in row_candidates[row_index]:
            next_prefixes: list[int] = []
            valid = True
            for col_index in range(board_size):
                bit = int((row_pattern >> (board_size - 1 - col_index)) & 1)
                next_prefix = (prefixes[col_index] << 1) | bit
                if next_prefix not in col_prefix_sets[col_index][row_index + 1]:
                    valid = False
                    break
                next_prefixes.append(next_prefix)
            if valid:
                dfs(row_index + 1, next_prefixes)
                if solution_count >= max_count:
                    return

    dfs(0, [0] * board_size)
    return int(solution_count)


def has_unique_nonogram_solution(
    row_clues: list[tuple[int, ...]],
    col_clues: list[tuple[int, ...]],
) -> bool:
    return count_nonogram_solutions(row_clues, col_clues, max_count=2) == 1


@dataclass
class GeneratedSample:
    seed: int
    attempts: int
    solution: list[list[int]]
    row_clues: list[tuple[int, ...]]
    col_clues: list[tuple[int, ...]]
    filled_count: int


def generate_nonogram_sample(
    *,
    seed: int,
    board_size: int = 10,
    fill_ratio_min: float = 0.0,
    fill_ratio_max: float = 1.0,
    max_attempts: int = 1000,
) -> GeneratedSample:
    if not 0.0 <= fill_ratio_min <= fill_ratio_max <= 1.0:
        raise ValueError("Expected 0 <= fill_ratio_min <= fill_ratio_max <= 1")

    generator = random.Random(int(seed))
    max_clue_len = default_max_clue_len(board_size)
    min_filled = int(round(fill_ratio_min * board_size * board_size))
    max_filled = int(round(fill_ratio_max * board_size * board_size))

    for attempts in range(1, max_attempts + 1):
        candidate = [
            [generator.randint(0, 1) for _ in range(board_size)]
            for _ in range(board_size)
        ]
        filled_count = sum(sum(row) for row in candidate)
        if filled_count <= 0 or filled_count >= board_size * board_size:
            continue
        if filled_count < min_filled or filled_count > max_filled:
            continue

        row_clues, col_clues = compute_board_clues(candidate, max_clue_len=max_clue_len)
        if not has_unique_nonogram_solution(row_clues, col_clues):
            continue

        return GeneratedSample(
            seed=seed,
            attempts=attempts,
            solution=candidate,
            row_clues=row_clues,
            col_clues=col_clues,
            filled_count=filled_count,
        )

    raise RuntimeError(
        f"Unable to generate a unique sample within {max_attempts} attempts for seed={seed}"
    )
