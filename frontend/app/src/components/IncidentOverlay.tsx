import type { IncidentRecord } from "../types/api";
import { TypewriterPanel } from "./TypewriterPanel";

type IncidentOverlayProps = {
  incident: IncidentRecord | null | undefined;
  onClose: () => void;
};

export function IncidentOverlay({ incident, onClose }: IncidentOverlayProps) {
  if (!incident) {
    return null;
  }

  return (
    <section className="overlay-backdrop incident-backdrop">
      <TypewriterPanel
        actionLabel="我知道了"
        className="incident-card"
        kicker={`${incident.clock || incident.time || "突发事件"} · 固定事件`}
        title={incident.title || "新的情况出现了"}
        text={incident.content || "团队需要你尽快做出判断。"}
        onAction={onClose}
      />
    </section>
  );
}
