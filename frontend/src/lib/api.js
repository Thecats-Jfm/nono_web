export async function startGeneratePuzzle(seed, size) {
  let response;

  try {
    response = await fetch("/api/puzzles/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ seed, size }),
    });
  } catch (error) {
    throw new Error("无法连接后端服务，请确认 uvicorn 正在 8000 端口运行。");
  }

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "生成谜题失败");
  }

  return response.json();
}

export async function getGeneratePuzzleJob(jobId) {
  let response;

  try {
    response = await fetch(`/api/puzzles/jobs/${jobId}`);
  } catch (error) {
    throw new Error("无法连接后端服务，请确认 uvicorn 正在 8000 端口运行。");
  }

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "获取生成进度失败");
  }

  return response.json();
}
