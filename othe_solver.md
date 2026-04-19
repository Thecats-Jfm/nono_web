# Nonogram Generation And Solver Export

This file is a compact export of the nonogram data-generation and uniqueness-solver logic used in this repository, prepared for side-by-side comparison with another implementation.

## Scope

- Core generation and uniqueness filtering:
  `tasks/nonogram/data.py`
- Dataset-generation CLI:
  `scripts/generate_nonogram_dataset.py`
- Real historical run summary for the `1m` dataset:
  `data/nonogram10x10_1m/dataset_summary.json`

## High-Level Pipeline

The generation flow in this repo is:

1. Sample a random binary `board_size x board_size` solution board.
2. Reject boards that are empty/full or outside the filled-count range derived from `fill_ratio_min` and `fill_ratio_max`.
3. Compute row and column clues from the sampled board.
4. Run the uniqueness solver and keep only boards whose clues have exactly one solution.
5. De-duplicate accepted samples.
6. Bucket accepted samples by `filled_count`.
7. Perform a round-robin selection across filled-count buckets to make the final dataset more balanced by density.
8. Save `puzzles`, `solutions`, `row_clues`, `col_clues`, and `meta` into `.pt` bundle files.

Important detail:

- `attempts` counts every sampled candidate board, including candidates rejected by the filled-ratio filter, uniqueness filter, or de-duplication.
- The stored `puzzles` tensor is initialized as all `NONOGRAM_UNKNOWN = -1`, not a partially revealed board.

## Constants And Clue Encoding

Source: `tasks/nonogram/data.py`

```python
NONOGRAM_BOARD_SIZE = 10
NONOGRAM_MAX_CLUE_LEN = 5
NONOGRAM_EMPTY = 0
NONOGRAM_FILLED = 1
NONOGRAM_UNKNOWN = -1


def default_max_clue_len(board_size: int) -> int:
    return int((int(board_size) + 1) // 2)


def compute_line_clues(line: torch.Tensor | list[int] | tuple[int, ...]) -> tuple[int, ...]:
    values = [int(value) for value in line]
    runs: list[int] = []
    current = 0
    for value in values:
        if value == NONOGRAM_FILLED:
            current += 1
            continue
        if current > 0:
            runs.append(current)
            current = 0
    if current > 0:
        runs.append(current)
    return tuple(runs)


def encode_clues(clues: tuple[int, ...], *, max_len: int = NONOGRAM_MAX_CLUE_LEN) -> torch.Tensor:
    encoded = torch.zeros(max_len, dtype=torch.long)
    if len(clues) > max_len:
        raise ValueError(f"clue length {len(clues)} exceeds max_len={max_len}")
    if clues:
        encoded[-len(clues) :] = torch.tensor(clues, dtype=torch.long)
    return encoded


def compute_board_clues(
    solution: torch.Tensor,
    *,
    max_clue_len: int | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    if solution.dim() != 2 or solution.shape[0] != solution.shape[1]:
        raise ValueError(
            f"Expected square solution shape [S, S], got {tuple(solution.shape)}"
        )
    board_size = int(solution.shape[0])
    max_clue_len = int(default_max_clue_len(board_size) if max_clue_len is None else max_clue_len)
    row_clues = torch.stack(
        [encode_clues(compute_line_clues(solution[row].tolist()), max_len=max_clue_len) for row in range(solution.shape[0])],
        dim=0,
    )
    col_clues = torch.stack(
        [
            encode_clues(compute_line_clues(solution[:, col].tolist()), max_len=max_clue_len)
            for col in range(solution.shape[1])
        ],
        dim=0,
    )
    return row_clues, col_clues


def decode_padded_clues(clue_tensor: torch.Tensor | list[int] | tuple[int, ...]) -> tuple[int, ...]:
    return tuple(int(value) for value in clue_tensor if int(value) > 0)
```

Notes:

- Clues are right-aligned and zero-padded.
- For the default `10x10` setup, `max_clue_len = 5`.

## Uniqueness Solver

Source: `tasks/nonogram/data.py`

The uniqueness check works in two stages:

1. For each row clue and each column clue, enumerate all line patterns matching that clue.
2. Do a row-by-row DFS while maintaining column prefixes; prune any branch whose column prefix can no longer match any legal column pattern.

This is the exact solver logic:

```python
@lru_cache(maxsize=None)
def _line_patterns_for_clue(clue: tuple[int, ...], line_length: int = NONOGRAM_BOARD_SIZE) -> tuple[int, ...]:
    matches: list[int] = []
    for pattern in range(1 << line_length):
        bits = tuple((pattern >> shift) & 1 for shift in range(line_length - 1, -1, -1))
        if compute_line_clues(bits) == clue:
            matches.append(pattern)
    return tuple(matches)


def _prefix_value(pattern: int, *, prefix_len: int, line_length: int = NONOGRAM_BOARD_SIZE) -> int:
    if prefix_len <= 0:
        return 0
    shift = line_length - prefix_len
    return int(pattern >> shift)


def count_nonogram_solutions(
    row_clues: torch.Tensor,
    col_clues: torch.Tensor,
    *,
    max_count: int = 2,
) -> int:
    board_size = int(row_clues.shape[0])
    decoded_rows = [decode_padded_clues(row_clues[row].tolist()) for row in range(board_size)]
    decoded_cols = [decode_padded_clues(col_clues[col].tolist()) for col in range(board_size)]
    row_candidates = [_line_patterns_for_clue(clue, board_size) for clue in decoded_rows]
    col_candidates = [_line_patterns_for_clue(clue, board_size) for clue in decoded_cols]
    col_prefix_sets = [
        {
            prefix_len: {
                _prefix_value(pattern, prefix_len=prefix_len, line_length=board_size)
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


def has_unique_nonogram_solution(row_clues: torch.Tensor, col_clues: torch.Tensor) -> bool:
    return count_nonogram_solutions(row_clues, col_clues, max_count=2) == 1
```

Comparison notes:

- This solver enumerates all `2^line_length` patterns per unique clue, then caches them with `lru_cache`.
- Uniqueness is only checked up to `max_count=2`; as soon as a second solution is found, DFS returns early.
- The pruning condition is entirely prefix-based on column feasibility.

## Generation Logic

Source: `tasks/nonogram/data.py`

This is the exact generation core:

```python
def generate_nonogram_dataset(
    *,
    num_samples: int,
    seed: int,
    board_size: int = NONOGRAM_BOARD_SIZE,
    max_clue_len: int | None = None,
    fill_ratio_min: float = 0.2,
    fill_ratio_max: float = 0.8,
    max_attempts: int | None = None,
    show_progress: bool = False,
    progress_desc: str | None = None,
) -> GeneratedNonogramBundle:
    if num_samples <= 0:
        raise ValueError(f"num_samples must be > 0, got {num_samples}")
    if not 0.0 < fill_ratio_min <= fill_ratio_max < 1.0:
        raise ValueError(
            f"Expected 0 < fill_ratio_min <= fill_ratio_max < 1, got {fill_ratio_min}, {fill_ratio_max}"
        )
    board_size = int(board_size)
    if board_size <= 0:
        raise ValueError(f"board_size must be > 0, got {board_size}")
    max_clue_len = int(default_max_clue_len(board_size) if max_clue_len is None else max_clue_len)
    if max_clue_len <= 0:
        raise ValueError(f"max_clue_len must be > 0, got {max_clue_len}")
    max_attempts = max_attempts if max_attempts is not None else max(num_samples * 200, 1000)
    generator = torch.Generator().manual_seed(int(seed))

    bucketed_samples: dict[int, list[tuple[torch.Tensor, torch.Tensor, torch.Tensor]]] = {}
    seen_keys: set[tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]] = set()
    progress_bar = None
    if show_progress and tqdm is not None:
        progress_bar = tqdm(total=num_samples, desc=progress_desc or "nonogram_generate", unit="sample")

    attempts = 0
    min_filled = int(round(fill_ratio_min * board_size * board_size))
    max_filled = int(round(fill_ratio_max * board_size * board_size))
    try:
        while len(seen_keys) < num_samples and attempts < max_attempts:
            attempts += 1
            candidate = torch.randint(
                low=0,
                high=2,
                size=(board_size, board_size),
                generator=generator,
                dtype=torch.long,
            )
            filled_count = int(candidate.sum().item())
            if filled_count <= 0 or filled_count >= board_size * board_size:
                continue
            if filled_count < min_filled or filled_count > max_filled:
                continue
            row_clues, col_clues = compute_board_clues(candidate, max_clue_len=max_clue_len)
            if not has_unique_nonogram_solution(row_clues, col_clues):
                continue
            key = (
                tuple(int(value) for value in row_clues.view(-1).tolist()),
                tuple(int(value) for value in col_clues.view(-1).tolist()),
                tuple(int(value) for value in candidate.view(-1).tolist()),
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            bucketed_samples.setdefault(filled_count, []).append((candidate, row_clues, col_clues))
            if progress_bar is not None:
                progress_bar.update(1)
                if len(seen_keys) % 200 == 0 or len(seen_keys) == num_samples:
                    progress_bar.set_postfix(
                        attempts=int(attempts),
                        accept_rate=f"{len(seen_keys) / max(int(attempts), 1):.3f}",
                    )
    finally:
        if progress_bar is not None:
            progress_bar.close()
```

Critical comparison notes:

- `attempts += 1` happens before any filtering. Out-of-range filled ratios still count as attempts.
- Sampling is iid Bernoulli via `torch.randint(low=0, high=2, size=(board_size, board_size))`, so the raw density distribution is centered near `50%` fill.
- The de-duplication key includes:
  - flattened `row_clues`
  - flattened `col_clues`
  - flattened full board
- This means duplicates are checked after uniqueness filtering, not before.

## Density Range And Filled-Count Interpretation

For the default `10x10` case:

```python
min_filled = int(round(0.2 * 10 * 10))  # 20
max_filled = int(round(0.8 * 10 * 10))  # 80
```

So the filter is:

- accept only boards with `20 <= filled_count <= 80`
- both boundaries are inclusive

However, this is only a candidate filter. It does not mean the final accepted dataset will actually contain examples at every filled count from `20` through `80`.

## Post-Filter Balancing By Filled Count

Source: `tasks/nonogram/data.py`

After enough unique-solution samples are accepted, the code rebalances them by filled-count bucket:

```python
    total_candidates = sum(len(samples) for samples in bucketed_samples.values())
    if total_candidates < num_samples:
        raise RuntimeError(
            f"Unable to generate {num_samples} unique nonogram samples within {max_attempts} attempts. "
            f"Generated {total_candidates} samples."
        )

    eligible_filled_counts = sorted(bucketed_samples)
    selected_samples: list[tuple[torch.Tensor, torch.Tensor, torch.Tensor]] = []
    bucket_offsets = {filled_count: 0 for filled_count in eligible_filled_counts}
    for filled_count in eligible_filled_counts:
        samples = bucketed_samples[filled_count]
        if len(samples) <= 1:
            continue
        permutation = torch.randperm(len(samples), generator=generator).tolist()
        bucketed_samples[filled_count] = [samples[index] for index in permutation]

    while len(selected_samples) < num_samples:
        made_progress = False
        for filled_count in eligible_filled_counts:
            offset = bucket_offsets[filled_count]
            samples = bucketed_samples[filled_count]
            if offset >= len(samples):
                continue
            selected_samples.append(samples[offset])
            bucket_offsets[filled_count] = offset + 1
            made_progress = True
            if len(selected_samples) >= num_samples:
                break
        if not made_progress:
            break
```

Notes:

- Balancing is done after collecting accepted samples.
- The round-robin pass reduces over-dominance of common densities.
- Buckets with only one sample are not shuffled, but they are still eligible for selection during the round-robin stage.

## Bundle Payload And Train/Val/Test Split

Source: `tasks/nonogram/data.py`

The payload writer and split logic:

```python
    solution_tensor = torch.stack([sample[0] for sample in selected_samples], dim=0)
    row_clues_tensor = torch.stack([sample[1] for sample in selected_samples], dim=0)
    col_clues_tensor = torch.stack([sample[2] for sample in selected_samples], dim=0)
    puzzles = torch.full_like(solution_tensor, fill_value=NONOGRAM_UNKNOWN)

    meta = {
        "task": "nonogram",
        "board_size": board_size,
        "max_clue_len": max_clue_len,
        "encoding": "binary",
        "unique_solution": True,
        "seed": int(seed),
        "attempts": int(attempts),
        "generated_candidate_count": int(total_candidates),
        "fill_ratio_min": float(fill_ratio_min),
        "fill_ratio_max": float(fill_ratio_max),
        "balanced_by_filled_count": True,
        "filled_count_histogram": filled_count_histogram,
    }
```

```python
def split_generated_nonogram_bundle(
    bundle: GeneratedNonogramBundle,
    *,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    seed: int = 0,
) -> dict[str, GeneratedNonogramBundle]:
    total = int(bundle.solutions.shape[0])
    ...
    generator = torch.Generator().manual_seed(int(seed))
    permutation = torch.randperm(total, generator=generator)
    ...
```

Notes:

- `puzzles` is all `-1`, so supervision is fully clue-driven from the observation/rendered input.
- Split shuffling is a second seeded random permutation after generation is complete.

## Dataset-Generation CLI

Source: `scripts/generate_nonogram_dataset.py`

The main script that was used to create dataset artifacts:

```python
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate 10x10 unique-solution nonogram dataset artifacts.")
    parser.add_argument("--output-dir", type=str, default="data/nonogram10x10")
    parser.add_argument("--num-samples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--board-size", type=int, default=NONOGRAM_BOARD_SIZE)
    parser.add_argument("--max-clue-len", type=int, default=NONOGRAM_MAX_CLUE_LEN)
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--cell-size", type=int, default=16)
    parser.add_argument("--fill-ratio-min", type=float, default=0.2)
    parser.add_argument("--fill-ratio-max", type=float, default=0.8)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--max-attempts", type=int, default=None)
    parser.add_argument("--preview-samples", type=int, default=16)
    parser.add_argument("--preview-cols", type=int, default=4)
    parser.add_argument("--cache-observations", action="store_true")
    parser.add_argument("--cache-num-workers", type=int, default=1)
    parser.add_argument("--cache-chunk-size", type=int, default=256)
    parser.add_argument("--no-progress", action="store_true")
    return parser.parse_args()
```

```python
generated = generate_nonogram_dataset(
    num_samples=int(args.num_samples),
    seed=int(args.seed),
    board_size=int(args.board_size),
    max_clue_len=int(args.max_clue_len),
    fill_ratio_min=float(args.fill_ratio_min),
    fill_ratio_max=float(args.fill_ratio_max),
    max_attempts=(None if args.max_attempts is None else int(args.max_attempts)),
    show_progress=not bool(args.no_progress),
    progress_desc=f"nonogram{int(args.board_size)}x{int(args.board_size)}",
)
splits = split_generated_nonogram_bundle(
    generated,
    train_ratio=float(args.train_ratio),
    val_ratio=float(args.val_ratio),
    seed=int(args.seed),
)
```

Notes:

- This script adds preview images and a JSON summary in addition to the `.pt` bundles.
- Observation caching can be done at generation time with `--cache-observations`, though our workflow also used a separate caching step later.

## Historical `1m` Dataset Configuration In This Repo

Source: `data/nonogram10x10_1m/dataset_summary.json`

This repository currently contains a real generated dataset summary with the following key values:

```json
{
  "config": {
    "output_dir": "data/nonogram10x10_1m",
    "num_samples": 1000000,
    "seed": 0,
    "board_size": 10,
    "max_clue_len": 5,
    "image_size": 256,
    "cell_size": 16,
    "fill_ratio_min": 0.2,
    "fill_ratio_max": 0.8,
    "train_ratio": 0.98,
    "val_ratio": 0.01,
    "max_attempts": null
  },
  "generation": {
    "attempts": 1867712,
    "generated_candidate_count": 1000000,
    "balanced_by_filled_count": true
  }
}
```

Interpretation:

- The `1m` dataset was generated with the `0.2 ~ 0.8` filled-ratio filter included.
- `attempts = 1,867,712` means all sampled candidates, including boards rejected by density, uniqueness, or de-duplication.
- `generated_candidate_count = 1,000,000` is the number of accepted unique-solution candidates collected before or at final balancing.

Approximate command matching that historical run:

```bash
python scripts/generate_nonogram_dataset.py \
  --output-dir data/nonogram10x10_1m \
  --num-samples 1000000 \
  --seed 0 \
  --board-size 10 \
  --max-clue-len 5 \
  --image-size 256 \
  --cell-size 16 \
  --fill-ratio-min 0.2 \
  --fill-ratio-max 0.8 \
  --train-ratio 0.98 \
  --val-ratio 0.01
```

## Quick Cross-Comparison Checklist

If you are comparing another implementation against this one, the highest-signal differences to check are:

1. Whether `attempts` is incremented before or after density filtering.
2. Whether clue encoding is right-aligned zero padding or another convention.
3. Whether uniqueness is checked with:
   - a full-board search,
   - a line-pattern search,
   - or an external CSP/ILP solver.
4. Whether the solver stops at `2` solutions or counts all solutions.
5. Whether de-duplication happens before or after uniqueness checking.
6. Whether the dataset is rebalanced by filled-count after acceptance.
7. Whether raw board sampling is iid Bernoulli or uses a constrained generator.
8. Whether empty/full boards are rejected explicitly.

## Source Pointers

- `tasks/nonogram/data.py`
- `scripts/generate_nonogram_dataset.py`
- `data/nonogram10x10_1m/dataset_summary.json`

