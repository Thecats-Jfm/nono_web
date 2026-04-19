from __future__ import annotations


Board = list[list[int]]


def line_clues(line: list[int]) -> list[int]:
    runs: list[int] = []
    run_length = 0
    for value in line:
        if value == 1:
            run_length += 1
        elif run_length:
            runs.append(run_length)
            run_length = 0
    if run_length:
        runs.append(run_length)
    return runs


def board_to_clues(board: Board) -> tuple[list[list[int]], list[list[int]]]:
    row_clues = [line_clues(row) for row in board]
    col_clues = [line_clues([board[row][col] for row in range(len(board))]) for col in range(len(board[0]))]
    return row_clues, col_clues
