import { Fragment } from "react";

function buildLineRuns(line) {
  const runs = [];
  let streak = 0;

  line.forEach((cell) => {
    if (cell === "filled") {
      streak += 1;
      return;
    }

    if (streak > 0) {
      runs.push(streak);
      streak = 0;
    }
  });

  if (streak > 0) {
    runs.push(streak);
  }

  return runs;
}

function arraysEqual(left, right) {
  if (left.length !== right.length) {
    return false;
  }

  return left.every((value, index) => value === right[index]);
}

function isLineComplete(line, clue) {
  if (line.includes("unknown")) {
    return false;
  }

  return arraysEqual(buildLineRuns(line), clue);
}

function cellSizeForBoard(size) {
  if (size >= 30) {
    return 24;
  }
  if (size >= 20) {
    return 28;
  }
  if (size >= 15) {
    return 32;
  }
  if (size >= 10) {
    return 36;
  }
  return 42;
}

function renderClueItems(clue, axis, complete) {
  if (!clue.length) {
    return <span className={`clue-empty-dot ${complete ? "clue-empty-dot-complete" : ""}`.trim()} aria-hidden="true" />;
  }

  return clue.map((value, index) => (
    <span
      key={`${axis}-${index}-${value}`}
      className={`clue-chip ${complete ? "clue-chip-complete" : ""}`.trim()}
    >
      {value}
    </span>
  ));
}

export default function PuzzleBoard({ puzzle, playerBoard, solved, onCellMouseDown }) {
  if (!puzzle || !playerBoard) {
    return null;
  }

  const rowCompleted = playerBoard.map((row, rowIndex) => isLineComplete(row, puzzle.row_clues[rowIndex]));
  const colCompleted = puzzle.col_clues.map((clue, colIndex) => {
    const column = playerBoard.map((row) => row[colIndex]);
    return isLineComplete(column, clue);
  });
  const cellSize = cellSizeForBoard(puzzle.size);

  return (
    <section className={`board-shell ${solved ? "board-shell-solved" : ""}`.trim()}>
      {solved ? (
        <div className="board-badge" aria-live="polite">
          Puzzle Solved
        </div>
      ) : null}
      <div
        className="board-layout"
        style={{
          gridTemplateColumns: `max-content repeat(${puzzle.size}, var(--cell-size))`,
          "--cell-size": `${cellSize}px`,
        }}
      >
        <div className="corner-cell" />
        {puzzle.col_clues.map((clue, index) => (
          <div
            key={`col-${index}`}
            className={`clue clue-col ${colCompleted[index] ? "clue-complete" : ""}`.trim()}
          >
            <div className="clue-stack clue-stack-col">
              {renderClueItems(clue, `col-${index}`, colCompleted[index])}
            </div>
          </div>
        ))}

        {playerBoard.map((row, rowIndex) => (
          <Fragment key={`row-${rowIndex}`}>
            <div
              key={`row-clue-${rowIndex}`}
              className={`clue clue-row ${rowCompleted[rowIndex] ? "clue-complete" : ""}`.trim()}
            >
              <div className="clue-stack clue-stack-row">
                {renderClueItems(puzzle.row_clues[rowIndex], `row-${rowIndex}`, rowCompleted[rowIndex])}
              </div>
            </div>
            {row.map((cell, colIndex) => {
              const groupClasses = [
                rowIndex % 5 === 0 ? "cell-group-top" : "",
                colIndex % 5 === 0 ? "cell-group-left" : "",
                rowIndex === puzzle.size - 1 ? "cell-group-bottom" : "",
                colIndex === puzzle.size - 1 ? "cell-group-right" : "",
              ]
                .filter(Boolean)
                .join(" ");
              const className = `cell cell-${cell} ${groupClasses}`.trim();
              return (
                <button
                  key={`cell-${rowIndex}-${colIndex}`}
                  type="button"
                  className={className}
                  onMouseDown={(event) => onCellMouseDown(event, rowIndex, colIndex)}
                  onContextMenu={(event) => event.preventDefault()}
                >
                  {cell === "empty" ? <span className="cell-cross">×</span> : null}
                </button>
              );
            })}
          </Fragment>
        ))}
      </div>
    </section>
  );
}
