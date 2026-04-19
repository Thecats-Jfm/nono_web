from nonogram.clues import board_to_clues, line_clues


def test_line_clues_generates_runs() -> None:
    assert line_clues([0, 1, 1, 0, 1, 1, 1, 0]) == [2, 3]


def test_board_to_clues_works_for_rows_and_columns() -> None:
    board = [
        [1, 1, 0],
        [0, 1, 0],
        [1, 0, 1],
    ]
    row_clues, col_clues = board_to_clues(board)
    assert row_clues == [[2], [1], [1, 1]]
    assert col_clues == [[1, 1], [2], [1]]
