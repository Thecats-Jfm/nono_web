import { useEffect, useState } from "react";

import ControlPanel from "./components/ControlPanel.jsx";
import PuzzleBoard from "./components/PuzzleBoard.jsx";
import PuzzleMeta from "./components/PuzzleMeta.jsx";
import { createEmptyPlayerBoard, isSolved, toggleEmptyState, toggleFilledState } from "./lib/board.js";
import { generatePuzzle } from "./lib/api.js";

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

  async function handleGenerate() {
    const parsedSeed = Number(seed);
    if (!Number.isInteger(parsedSeed)) {
      setError("Seed 必须是整数");
      return;
    }

    setLoading(true);
    setError("");
    setSolved(false);

    try {
      const nextPuzzle = await generatePuzzle(parsedSeed, size);
      setPuzzle(nextPuzzle);
      setPlayerBoard(createEmptyPlayerBoard(nextPuzzle.size));
    } catch (nextError) {
      setError(nextError.message || "生成失败");
    } finally {
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
