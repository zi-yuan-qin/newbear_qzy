import type { WorldState } from "../types/api";

type DebugPanelProps = {
  world: WorldState | null;
};

export function DebugPanel({ world }: DebugPanelProps) {
  const locations = world?.map?.semantics?.locations ?? [];
  const actors = world?.actors ?? [];
  const logs = world?.company?.logs ?? [];
  const inputHistory = world?.user_inputs ?? [];

  return (
    <details className="debug-panel">
      <summary>调试信息 / 历史记录</summary>

      <section>
        <h3>区域</h3>
        {locations.slice(0, 8).map((location) => {
          const actorsHere = actors.filter((actor) => actor.location === location.name);
          return (
            <article className="debug-card" key={location.location_id || location.name}>
              <strong>{location.name}</strong>
              <p>{location.function || "暂无说明"}</p>
              <span>{actorsHere.map((actor) => actor.display_name).join("、") || "无人"}</span>
            </article>
          );
        })}
      </section>

      <section>
        <h3>输入历史</h3>
        {inputHistory.slice(-5).reverse().map((record, index) => (
          <article className="debug-card" key={record.input_id || index}>
            <strong>{record.clock || `第 ${record.step ?? "-"} 步`}</strong>
            <p>{record.is_empty ? "（空输入）" : record.raw_text || "暂无文本"}</p>
          </article>
        ))}
      </section>

      <section>
        <h3>时间步日志</h3>
        {logs.slice(-5).reverse().map((log, index) => (
          <article className="debug-card" key={`${log.step}-${index}`}>
            <strong>
              {log.from_clock || "-"} → {log.to_clock || "-"}
            </strong>
            <p>{log.affair || "无额外事务"}</p>
          </article>
        ))}
      </section>
    </details>
  );
}
