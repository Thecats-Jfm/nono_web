export function createEmptyPlayerBoard(size) {
  return Array.from({ length: size }, () =>
    Array.from({ length: size }, () => "unknown"),
  );
}

export function toggleFilledState(current) {
  if (current === "filled") {
    return "unknown";
  }
  return "filled";
}

export function toggleEmptyState(current) {
  if (current === "empty") {
    return "unknown";
  }
  return "empty";
}

export function isSolved(playerBoard, solution) {
  for (let row = 0; row < solution.length; row += 1) {
    for (let col = 0; col < solution[row].length; col += 1) {
      const expected = solution[row][col] === 1 ? "filled" : "empty";
      if (playerBoard[row][col] !== expected) {
        return false;
      }
    }
  }
  return true;
}
