import { Fragment } from "react";

function renderClueItems(clue, axis) {
  if (!clue.length) {
    return <span className="clue-empty-dot" aria-hidden="true" />;
  }

  return clue.map((value, index) => (
    <span
      key={`${axis}-${index}-${value}`}
      className="clue-chip"
    >
      {value}
    </span>
  ));
}

export default function PuzzleBoard({ puzzle, playerBoard, solved, onCellMouseDown }) {
  if (!puzzle || !playerBoard) {
    return null;
  }

  return (
    <section className={`board-shell ${solved ? "board-shell-solved" : ""}`.trim()}>
      {solved ? (
        <div className="board-badge" aria-live="polite">
          Puzzle Solved
        </div>
      ) : null}
      <div
        className="board-layout"
        style={{ gridTemplateColumns: `max-content repeat(${puzzle.size}, minmax(0, 1fr))` }}
      >
        <div className="corner-cell" />
        {puzzle.col_clues.map((clue, index) => (
          <div key={`col-${index}`} className="clue clue-col">
            <div className="clue-stack clue-stack-col">
              {renderClueItems(clue, `col-${index}`)}
            </div>
          </div>
        ))}

        {playerBoard.map((row, rowIndex) => (
          <Fragment key={`row-${rowIndex}`}>
            <div key={`row-clue-${rowIndex}`} className="clue clue-row">
              <div className="clue-stack clue-stack-row">
                {renderClueItems(puzzle.row_clues[rowIndex], `row-${rowIndex}`)}
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
