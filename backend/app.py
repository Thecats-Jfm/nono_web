from threading import Lock, Thread
from typing import Union
from uuid import uuid4

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from nonogram.generator import generate_puzzle
from nonogram.models import (
    GeneratePuzzleRequest,
    GenerationJobProgressResponse,
    GenerationJobStartResponse,
    PuzzleResponse,
    TimeoutResponse,
)


app = FastAPI(title="Nonogram API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs_lock = Lock()
jobs: dict[str, dict] = {}


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


def run_generation_job(job_id: str, seed: int, size: int) -> None:
    def update_progress(attempts_tried: int, current_seed: int, elapsed_ms: float) -> None:
        with jobs_lock:
            job = jobs.get(job_id)
            if job is None:
                return
            job.update(
                {
                    "status": "running",
                    "attempts_tried": attempts_tried,
                    "current_seed": current_seed,
                    "elapsed_ms": elapsed_ms,
                    "message": f"已经尝试 {attempts_tried} 题，还没有找到唯一解。",
                }
            )

    result = generate_puzzle(seed, size, progress_callback=update_progress)
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            return
        job["result"] = result.model_dump()
        job["status"] = result.status
        if result.status == "timeout":
            job["message"] = result.message


@app.post("/api/puzzles/generate", response_model=GenerationJobStartResponse)
def generate(request: GeneratePuzzleRequest) -> GenerationJobStartResponse:
    job_id = uuid4().hex
    with jobs_lock:
        jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "input_seed": request.seed,
            "size": request.size,
            "attempts_tried": 0,
            "current_seed": None,
            "elapsed_ms": 0.0,
            "message": "开始生成谜题...",
            "result": None,
        }
    thread = Thread(target=run_generation_job, args=(job_id, request.seed, request.size), daemon=True)
    thread.start()
    return GenerationJobStartResponse(job_id=job_id)


@app.get(
    "/api/puzzles/jobs/{job_id}",
    response_model=Union[GenerationJobProgressResponse, PuzzleResponse, TimeoutResponse],
)
def get_generation_job(job_id: str) -> GenerationJobProgressResponse | PuzzleResponse | TimeoutResponse:
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        if job["result"] is not None:
            result = job["result"]
            if result["status"] == "ok":
                return PuzzleResponse(**result)
            return TimeoutResponse(**result)
        return GenerationJobProgressResponse(
            job_id=job_id,
            status=job["status"],
            input_seed=job["input_seed"],
            size=job["size"],
            attempts_tried=job["attempts_tried"],
            current_seed=job["current_seed"],
            elapsed_ms=job["elapsed_ms"],
            message=job["message"],
        )
