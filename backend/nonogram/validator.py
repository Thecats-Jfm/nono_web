from __future__ import annotations

from nonogram.solver import SolveResult


def is_valid_unique_puzzle(result: SolveResult) -> bool:
    return result.solutions_found == 1
