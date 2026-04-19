import { Fragment } from "react";

function formatClue(clue) {
  return clue.length ? clue.join(" ") : " ";
}

export default function PuzzleBoard({ puzzle, playerBoard, onCellMouseDown }) {
  if (!puzzle || !playerBoard) {
    return null;
  }

  return (
    <section className="board-shell">
      <div
        className="board-layout"
        style={{ gridTemplateColumns: `max-content repeat(${puzzle.size}, minmax(0, 1fr))` }}
      >
        <div className="corner-cell" />
        {puzzle.col_clues.map((clue, index) => (
          <div key={`col-${index}`} className="clue clue-col">
            {formatClue(clue)}
          </div>
        ))}

        {playerBoard.map((row, rowIndex) => (
          <Fragment key={`row-${rowIndex}`}>
            <div key={`row-clue-${rowIndex}`} className="clue clue-row">
              {formatClue(puzzle.row_clues[rowIndex])}
            </div>
            {row.map((cell, colIndex) => {
              const className = `cell cell-${cell}`;
              return (
                <button
                  key={`cell-${rowIndex}-${colIndex}`}
                  type="button"
                  className={className}
                  onMouseDown={(event) => onCellMouseDown(event, rowIndex, colIndex)}
                  onContextMenu={(event) => event.preventDefault()}
                >
                  {cell === "empty" ? "×" : ""}
                </button>
              );
            })}
          </Fragment>
        ))}
      </div>
    </section>
  );
}
