import { useEffect, useRef, useState } from "react";

import ControlPanel from "./components/ControlPanel.jsx";
import PuzzleBoard from "./components/PuzzleBoard.jsx";
import PuzzleMeta from "./components/PuzzleMeta.jsx";
import { createEmptyPlayerBoard, isSolved, toggleEmptyState, toggleFilledState } from "./lib/board.js";
import { getGeneratePuzzleJob, startGeneratePuzzle } from "./lib/api.js";

function buildRandomSeed() {
  return String(Math.floor(Math.random() * 1_000_000_000));
}

export default function App() {
  const [seed, setSeed] = useState(buildRandomSeed);
  const [size, setSize] = useState(10);
  const [puzzle, setPuzzle] = useState(null);
  const [playerBoard, setPlayerBoard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [solved, setSolved] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(null);
  const activeJobIdRef = useRef(null);

  async function pollGenerationJob(jobId) {
    while (activeJobIdRef.current === jobId) {
      const job = await getGeneratePuzzleJob(jobId);
      if (job.status === "queued" || job.status === "running") {
        setGenerationProgress(job);
        await new Promise((resolve) => window.setTimeout(resolve, 250));
        continue;
      }
      return job;
    }
    return null;
  }

  async function handleGenerate() {
    const parsedSeed = Number(seed);
    if (!Number.isInteger(parsedSeed)) {
      setError("Seed 必须是整数");
      return;
    }

    setLoading(true);
    setError("");
    setSolved(false);
    setPuzzle(null);
    setPlayerBoard(null);
    setGenerationProgress({
      status: "queued",
      input_seed: parsedSeed,
      size,
      attempts_tried: 0,
      current_seed: null,
      elapsed_ms: 0,
      message: "开始生成谜题...",
    });

    try {
      const job = await startGeneratePuzzle(parsedSeed, size);
      activeJobIdRef.current = job.job_id;
      const nextPuzzle = await pollGenerationJob(job.job_id);
      if (!nextPuzzle) {
        return;
      }
      if (nextPuzzle.status === "timeout") {
        setPuzzle(null);
        setPlayerBoard(null);
        setGenerationProgress(null);
        setError(nextPuzzle.message);
        return;
      }
      setPuzzle(nextPuzzle);
      setPlayerBoard(createEmptyPlayerBoard(nextPuzzle.size));
      setGenerationProgress(null);
    } catch (nextError) {
      setPuzzle(null);
      setPlayerBoard(null);
      setGenerationProgress(null);
      setError(nextError.message || "生成失败");
    } finally {
      activeJobIdRef.current = null;
      setLoading(false);
    }
  }

  function handleReset() {
    if (!puzzle) {
      return;
    }
    setPlayerBoard(createEmptyPlayerBoard(puzzle.size));
    setSolved(false);
  }

  function handleCellMouseDown(event, rowIndex, colIndex) {
    if (!playerBoard || !puzzle) {
      return;
    }

    const mouseButton = event.button;
    setPlayerBoard((current) => {
      const nextBoard = current.map((row) => [...row]);
      const currentValue = nextBoard[rowIndex][colIndex];
      if (mouseButton === 2) {
        nextBoard[rowIndex][colIndex] = toggleEmptyState(currentValue);
      } else {
        nextBoard[rowIndex][colIndex] = toggleFilledState(currentValue);
      }
      return nextBoard;
    });
  }

  useEffect(() => {
    if (!playerBoard || !puzzle) {
      return;
    }
    setSolved(isSolved(playerBoard, puzzle.solution));
  }, [playerBoard, puzzle]);

  return (
    <main className="app-shell">
      <header className="hero">
        <p className="eyebrow">Nonogram v1</p>
        <h1>给老婆玩的随机 Seed 填图站</h1>
        <p className="intro">
          每个格子独立随机生成，只要我们的 solver 证明它是唯一解，这题就成立。
        </p>
      </header>

      <ControlPanel
        seed={seed}
        size={size}
        loading={loading}
        onSeedChange={setSeed}
        onSizeChange={setSize}
        onRandomSeed={() => setSeed(buildRandomSeed())}
        onGenerate={handleGenerate}
        onReset={handleReset}
      />

      <PuzzleMeta puzzle={puzzle} />

      {loading && generationProgress ? (
        <section className="panel progress">
          <div>{generationProgress.message}</div>
          <div>当前尺寸: {generationProgress.size} x {generationProgress.size}</div>
          <div>已尝试谜题: {generationProgress.attempts_tried}</div>
          <div>
            当前 seed:
            {" "}
            {generationProgress.current_seed ?? "-"}
          </div>
          <div>已用时: {(generationProgress.elapsed_ms / 1000).toFixed(2)} s</div>
        </section>
      ) : null}

      {error ? <section className="panel error">{error}</section> : null}
      {solved ? <section className="panel success">通关啦，这一题已经完全填对了。</section> : null}

      <PuzzleBoard
        puzzle={puzzle}
        playerBoard={playerBoard}
        onCellMouseDown={handleCellMouseDown}
      />
    </main>
  );
}
