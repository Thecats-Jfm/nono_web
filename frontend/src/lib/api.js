const API_BASE = "http://127.0.0.1:8000";

export async function generatePuzzle(seed, size) {
  const response = await fetch(`${API_BASE}/api/puzzles/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ seed, size }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "生成谜题失败");
  }

  return response.json();
}
