import pytest

from nonogram.solver import SolveTimeoutError, generate_line_patterns, solve_nonogram


def test_generate_line_patterns_for_single_block() -> None:
    patterns = generate_line_patterns(5, (2,))
    assert patterns == (
        (1, 1, 0, 0, 0),
        (0, 1, 1, 0, 0),
        (0, 0, 1, 1, 0),
        (0, 0, 0, 1, 1),
    )


def test_solver_detects_unique_solution() -> None:
    row_clues = [[1], [3], [5], [3], [1]]
    col_clues = [[1], [3], [5], [3], [1]]
    result = solve_nonogram(5, row_clues, col_clues)
    assert result.solutions_found == 1
    assert result.unique is True


def test_solver_detects_multiple_solutions() -> None:
    row_clues = [[1], [1]]
    col_clues = [[1], [1]]
    result = solve_nonogram(2, row_clues, col_clues)
    assert result.solutions_found >= 2
    assert result.unique is False


def test_solver_respects_deadline() -> None:
    row_clues = [[1], [1]]
    col_clues = [[1], [1]]
    with pytest.raises(SolveTimeoutError):
        solve_nonogram(2, row_clues, col_clues, deadline=0.0)
