export default function ControlPanel({
  seed,
  size,
  loading,
  onSeedChange,
  onSizeChange,
  onRandomSeed,
  onGenerate,
  onReset,
}) {
  return (
    <section className="panel controls">
      <div className="field">
        <label htmlFor="seed-input">Seed</label>
        <input
          id="seed-input"
          type="number"
          value={seed}
          onChange={(event) => onSeedChange(event.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="size-select">尺寸</label>
        <select
          id="size-select"
          value={size}
          onChange={(event) => onSizeChange(Number(event.target.value))}
        >
          {[5, 10, 20, 30].map((item) => (
            <option key={item} value={item}>
              {item} x {item}
            </option>
          ))}
        </select>
      </div>

      <div className="button-row">
        <button type="button" onClick={onRandomSeed} disabled={loading}>
          随机 Seed
        </button>
        <button type="button" onClick={onGenerate} disabled={loading}>
          {loading ? "生成中..." : "生成谜题"}
        </button>
        <button type="button" onClick={onReset} disabled={loading}>
          重置当前盘面
        </button>
      </div>
    </section>
  );
}
