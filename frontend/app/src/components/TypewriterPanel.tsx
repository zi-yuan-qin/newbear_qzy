import { useEffect, useState } from "react";

const DEFAULT_INTERVAL_MS = 34;
const DEFAULT_CHUNK_SIZE = 3;

type TypewriterPanelProps = {
  kicker: string;
  title: string;
  text: string;
  actionLabel?: string;
  className?: string;
  intervalMs?: number;
  chunkSize?: number;
  onDone?: () => void;
  onAction?: () => void;
  surface?: "card" | "bare";
};

export function TypewriterPanel({
  kicker,
  title,
  text,
  actionLabel,
  className = "",
  intervalMs = DEFAULT_INTERVAL_MS,
  chunkSize = DEFAULT_CHUNK_SIZE,
  onDone,
  onAction,
  surface = "card",
}: TypewriterPanelProps) {
  const [visibleChars, setVisibleChars] = useState(0);
  const isDone = visibleChars >= text.length;

  useEffect(() => {
    setVisibleChars(0);
  }, [text]);

  useEffect(() => {
    if (isDone) {
      onDone?.();
      return;
    }

    const timer = window.setInterval(() => {
      setVisibleChars((current) => Math.min(text.length, current + chunkSize));
    }, intervalMs);

    return () => window.clearInterval(timer);
  }, [chunkSize, intervalMs, isDone, onDone, text.length]);

  return (
    <article className={`${surface === "card" ? "overlay-card " : ""}printer-card ${className}`}>
      <p className="overlay-kicker">{kicker}</p>
      <h2>{title}</h2>
      <pre>
        {text.slice(0, visibleChars)}
        {isDone ? "" : "▋"}
      </pre>
      {actionLabel && onAction ? (
        <button type="button" onClick={onAction} disabled={!isDone}>
          {actionLabel}
        </button>
      ) : null}
    </article>
  );
}
