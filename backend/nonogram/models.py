from typing import Literal

from pydantic import BaseModel, Field, field_validator


ALLOWED_SIZES = (5, 10, 15, 20, 30)


class GeneratePuzzleRequest(BaseModel):
    seed: int
    size: int = Field(..., description="Board size")

    @field_validator("size")
    @classmethod
    def validate_size(cls, value: int) -> int:
        if value not in ALLOWED_SIZES:
            raise ValueError(f"size must be one of {ALLOWED_SIZES}")
        return value


class SolverStats(BaseModel):
    unique: bool
    solve_time_ms: float
    nodes_visited: int
    solutions_found: int
    max_depth: int


class PuzzleResponse(BaseModel):
    status: Literal["ok"] = "ok"
    input_seed: int
    resolved_seed: int
    attempt: int
    puzzle_hash: str
    size: int
    row_clues: list[list[int]]
    col_clues: list[list[int]]
    solution: list[list[int]]
    solver: SolverStats


class TimeoutResponse(BaseModel):
    status: Literal["timeout"] = "timeout"
    input_seed: int
    size: int
    timeout_seconds: float
    attempts_tried: int
    elapsed_ms: float
    message: str


class GenerationJobStartResponse(BaseModel):
    job_id: str
    status: Literal["queued"] = "queued"


class GenerationJobProgressResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running"]
    input_seed: int
    size: int
    attempts_tried: int
    current_seed: int | None = None
    elapsed_ms: float
    message: str
