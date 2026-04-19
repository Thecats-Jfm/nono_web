from nonogram.generator import generate_puzzle


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
