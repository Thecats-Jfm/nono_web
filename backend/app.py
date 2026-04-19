from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nonogram.generator import generate_puzzle
from nonogram.models import GeneratePuzzleRequest, PuzzleResponse


app = FastAPI(title="Nonogram API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/puzzles/generate", response_model=PuzzleResponse)
def generate(request: GeneratePuzzleRequest) -> PuzzleResponse:
    return generate_puzzle(request.seed, request.size)
