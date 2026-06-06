import type { ReportRadarItem, ReportState } from "../types/api";
import { TypewriterPanel } from "./TypewriterPanel";

type ReportOverlayProps = {
  report: ReportState | null | undefined;
  onClose: () => void;
};

function buildRadarPoints(items: ReportRadarItem[], radius: number, center: number) {
  const angleStep = (Math.PI * 2) / items.length;

  return items
    .map((item, index) => {
      const value = Math.max(0, Math.min(100, Number(item.value ?? 0)));
      const ratio = Math.max(0.18, value / 100);
      const angle = -Math.PI / 2 + index * angleStep;
      const x = center + Math.cos(angle) * radius * ratio;
      const y = center + Math.sin(angle) * radius * ratio;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

function RadarChart({ items }: { items: ReportRadarItem[] }) {
  const safeItems = items.slice(0, 5);

  if (safeItems.length < 3) {
    return <p className="empty-copy">暂无足够数据绘制雷达图</p>;
  }

  const size = 220;
  const center = size / 2;
  const radius = 68;
  const angleStep = (Math.PI * 2) / safeItems.length;
  const polygon = buildRadarPoints(safeItems, radius, center);

  return (
    <svg className="radar-chart" viewBox={`0 0 ${size} ${size}`} role="img" aria-label="工作倾向雷达图">
      {[0.25, 0.5, 0.75, 1].map((ratio) => {
        const points = safeItems
          .map((_, index) => {
            const angle = -Math.PI / 2 + index * angleStep;
            const x = center + Math.cos(angle) * radius * ratio;
            const y = center + Math.sin(angle) * radius * ratio;
            return `${x.toFixed(1)},${y.toFixed(1)}`;
          })
          .join(" ");

        return <polygon className="radar-ring" key={ratio} points={points} />;
      })}
      {safeItems.map((_, index) => {
        const angle = -Math.PI / 2 + index * angleStep;
        const x = center + Math.cos(angle) * radius;
        const y = center + Math.sin(angle) * radius;
        return <line className="radar-axis" key={index} x1={center} y1={center} x2={x} y2={y} />;
      })}
      <polygon className="radar-shape" points={polygon} />
      {safeItems.map((item, index) => {
        const angle = -Math.PI / 2 + index * angleStep;
        const x = center + Math.cos(angle) * radius * 1.28;
        const y = center + Math.sin(angle) * radius * 1.28;
        return (
          <text className="radar-label" key={item.code || item.label || index} x={x} y={y}>
            {item.label || item.code}
          </text>
        );
      })}
    </svg>
  );
}

export function ReportOverlay({ report, onClose }: ReportOverlayProps) {
  if (!report?.visible) {
    return null;
  }

  const evidence = report.evidence?.slice(0, 5) ?? [];
  const letterText = [
    "产品经理：",
    report.letter_body || report.trait_summary || "今天的表现已经被团队记录下来。",
    report.trait_summary || "",
    "熊起东方全体同事",
  ]
    .filter(Boolean)
    .join("\n\n");

  return (
    <section className="overlay-backdrop report-backdrop">
      <article className="overlay-card report-card">
        <header className="report-header">
          <div>
            <p className="overlay-kicker">{report.clock || report.time || "18:00"} · 熊起东方写给产品经理</p>
            <h2>{report.letter_title || "今天辛苦了，产品经理"}</h2>
          </div>
          <button type="button" onClick={onClose}>
            回到公司
          </button>
        </header>

        <div className="report-grid">
          <section className="report-body">
            <TypewriterPanel
              className="report-printer"
              chunkSize={2}
              intervalMs={50}
              kicker="日终报告 · 写给产品经理"
              surface="bare"
              title={report.letter_title || "今天辛苦了，产品经理"}
              text={letterText}
            />
            {evidence.length ? (
              <div className="report-evidence">
                <strong>今天让我们记住你的几件事</strong>
                {evidence.map((item) => (
                  <p key={item}>{item}</p>
                ))}
              </div>
            ) : null}
          </section>

          <aside className="report-radar">
            <h3>今天的工作倾向</h3>
            <RadarChart items={report.radar_items ?? []} />
          </aside>
        </div>
      </article>
    </section>
  );
}
