from nonogram.solver import SolveResult
from nonogram.validator import is_valid_unique_puzzle


def test_validator_accepts_exactly_one_solution() -> None:
    result = SolveResult(True, 1.0, 10, 1, 3)
    assert is_valid_unique_puzzle(result) is True


def test_validator_rejects_non_unique_puzzle() -> None:
    result = SolveResult(False, 1.0, 10, 2, 3)
    assert is_valid_unique_puzzle(result) is False
