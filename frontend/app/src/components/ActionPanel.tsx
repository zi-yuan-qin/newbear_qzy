import type { ActorState, AuthUser, WorldState } from "../types/api";
import { ActorDetailPanel } from "./ActorDetailPanel";

type ActionPanelProps = {
  affair: string;
  isAutoStepEnabled: boolean;
  isBusy: boolean;
  selectedActor: ActorState | null;
  status: string;
  user: AuthUser;
  world: WorldState | null;
  onAffairChange: (value: string) => void;
  onAutoStepChange: (value: boolean) => void;
  onCloseActor: () => void;
  onResetWorld: () => void;
  onRunStep: () => void;
};

export function ActionPanel({
  affair,
  isAutoStepEnabled,
  isBusy,
  selectedActor,
  status,
  user,
  world,
  onAffairChange,
  onAutoStepChange,
  onCloseActor,
  onResetWorld,
  onRunStep,
}: ActionPanelProps) {
  return (
    <section className="bottom-panel">
      {selectedActor ? (
        <ActorDetailPanel actor={selectedActor} onClose={onCloseActor} />
      ) : null}

      <div className="status-row">
        <span>{status}</span>
        <span>{user.username}</span>
        <span>{world?.company?.clock || "09:00"}</span>
        <span>CNY {world?.company?.cash ?? 5000}</span>
      </div>

      <label className="input-box">
        <span>你想对同事说什么？</span>
        <input
          value={affair}
          onChange={(event) => onAffairChange(event.target.value)}
          placeholder="例如：我先了解一下大家手头的任务"
        />
      </label>

      <div className="action-row">
        <button type="button" onClick={onRunStep} disabled={isBusy}>
          {isBusy ? "推进中..." : "推进 30 分钟"}
        </button>
        <button
          className={`secondary-button ${isAutoStepEnabled ? "is-active" : ""}`}
          type="button"
          onClick={() => onAutoStepChange(!isAutoStepEnabled)}
          disabled={isBusy && !isAutoStepEnabled}
        >
          {isAutoStepEnabled ? "停止自动" : "自动推进"}
        </button>
        <button
          className="secondary-button"
          type="button"
          onClick={onResetWorld}
          disabled={isBusy}
        >
          重置世界
        </button>
      </div>
    </section>
  );
}
