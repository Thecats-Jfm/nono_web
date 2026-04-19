from nonogram import generator
from nonogram.generator import generate_puzzle
from nonogram.solver import SolveResult


def test_generator_is_deterministic() -> None:
    first = generate_puzzle(12345, 5)
    second = generate_puzzle(12345, 5)
    first_data = first.model_dump()
    second_data = second.model_dump()
    first_data["solver"].pop("solve_time_ms")
    second_data["solver"].pop("solve_time_ms")
    assert first_data == second_data


def test_attempt_matches_resolved_seed_offset() -> None:
    puzzle = generate_puzzle(100, 5)
    assert puzzle.attempt == puzzle.resolved_seed - puzzle.input_seed


def test_generator_supports_15x15() -> None:
    puzzle = generate_puzzle(12345, 15)
    assert puzzle.size == 15
    assert len(puzzle.solution) == 15
    assert len(puzzle.solution[0]) == 15


def test_generator_returns_timeout_response(monkeypatch) -> None:
    timestamps = iter([0.0, 0.0, 10.5])

    def fake_perf_counter() -> float:
        return next(timestamps)

    def fake_solve_nonogram(size, row_clues, col_clues):
        return SolveResult(False, 0.0, 1, 2, 1)

    monkeypatch.setattr(generator.time, "perf_counter", fake_perf_counter)
    monkeypatch.setattr(generator, "solve_nonogram", fake_solve_nonogram)

    result = generate_puzzle(12345, 5)
    data = result.model_dump()
    assert data["status"] == "timeout"
    assert data["input_seed"] == 12345
    assert data["size"] == 5
    assert data["attempts_tried"] == 1


def test_generator_skips_solver_timeout(monkeypatch) -> None:
    calls = {"count": 0}

    def fake_solve_nonogram(size, row_clues, col_clues, deadline=None):
        calls["count"] += 1
        if calls["count"] == 1:
            raise generator.SolveTimeoutError
        return SolveResult(True, 1.0, 10, 1, 3)

    monkeypatch.setattr(generator, "solve_nonogram", fake_solve_nonogram)

    result = generate_puzzle(12345, 5)
    assert result.status == "ok"
    assert result.attempt == 1
