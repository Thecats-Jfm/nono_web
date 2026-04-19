export default function PuzzleMeta({ puzzle }) {
  if (!puzzle || puzzle.status === "timeout") {
    return (
      <section className="panel meta">
        <p>输入一个整数 seed，然后生成一题唯一解 nonogram。</p>
      </section>
    );
  }

  return (
    <section className="panel meta">
      <div>input seed: {puzzle.input_seed}</div>
      <div>resolved seed: {puzzle.resolved_seed}</div>
      <div>attempt: {puzzle.attempt}</div>
      <div>size: {puzzle.size} x {puzzle.size}</div>
      <div>solve time: {puzzle.solver.solve_time_ms.toFixed(2)} ms</div>
      <div>nodes: {puzzle.solver.nodes_visited}</div>
      <div>max depth: {puzzle.solver.max_depth}</div>
      <div>hash: {puzzle.puzzle_hash}</div>
    </section>
  );
}
