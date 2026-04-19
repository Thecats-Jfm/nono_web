from __future__ import annotations

from statistics import mean
import time

from experiments.other_solver.solver_impl import generate_nonogram_sample


SEEDS = [12345, 20250419, 713231167, 670789976, 42424242]


def main() -> None:
    rows: list[dict[str, float | int]] = []
    for seed in SEEDS:
        started_at = time.perf_counter()
        sample = generate_nonogram_sample(
            seed=seed,
            board_size=10,
            fill_ratio_min=0.0,
            fill_ratio_max=1.0,
            max_attempts=5000,
        )
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        row = {
            "seed": seed,
            "attempts": sample.attempts,
            "filled_count": sample.filled_count,
            "elapsed_ms": round(elapsed_ms, 2),
        }
        rows.append(row)
        print(row)

    print(
        "summary",
        {
            "avg_attempts": round(mean(row["attempts"] for row in rows), 2),
            "avg_elapsed_ms": round(mean(row["elapsed_ms"] for row in rows), 2),
        },
    )


if __name__ == "__main__":
    main()
