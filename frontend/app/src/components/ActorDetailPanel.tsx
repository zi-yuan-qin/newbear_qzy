import type { ActorState } from "../types/api";

type ActorDetailPanelProps = {
  actor: ActorState;
  onClose: () => void;
};

export function ActorDetailPanel({ actor, onClose }: ActorDetailPanelProps) {
  return (
    <article className="actor-detail">
      <header>
        <strong>{actor.display_name}</strong>
        <button className="mini-close-button" type="button" onClick={onClose}>
          关闭
        </button>
      </header>

      <div className="actor-detail-grid">
        <span>位置：{actor.location || "未知"}</span>
        <span>压力：{actor.stress ?? "-"}</span>
        <span>精力：{actor.energy ?? "-"}</span>
        <span>心情：{actor.mood || "-"}</span>
      </div>

      {actor.current_task ? <p>任务：{actor.current_task}</p> : null}
      {actor.last_speech ? <p>最近发言：{actor.last_speech}</p> : null}
    </article>
  );
}
