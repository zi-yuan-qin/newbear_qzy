import { useEffect, useMemo, useState } from "react";
import type { MeetingState } from "../types/api";
import { TypewriterPanel } from "./TypewriterPanel";

const MEETING_SCENE_ASSET = "/assets/meeting/room.jpg";
const MEETING_TICK_INTERVAL_MS = 9000;
const MEETING_ACTOR_ASSETS: Record<string, string> = {
  xionglaoban: "/assets/meeting/boss-front.png",
  xiongshichang: "/assets/meeting/market-left.png",
  xiongxingzheng: "/assets/meeting/admin-left.png",
  xiongjishu: "/assets/meeting/tech-right.png",
};
const ACTOR_DISPLAY_NAMES: Record<string, string> = {
  xionglaoban: "熊老板",
  xiongshichang: "熊市场",
  xiongxingzheng: "熊行政",
  xiongjishu: "熊技术",
  user: "我",
};
const MEETING_SEATS: Record<string, { left: number; top: number }> = {
  xionglaoban: { left: 75, top: 62 },
  xiongshichang: { left: 23, top: 62 },
  xiongxingzheng: { left: 40, top: 45 },
  xiongjishu: { left: 60, top: 75 },
};

type MeetingPanelProps = {
  meeting: MeetingState | null | undefined;
  isBusy: boolean;
  onStart: () => Promise<void> | void;
  onSend: (message: string) => Promise<void> | void;
  onTick: () => Promise<void> | void;
  onFinish: () => Promise<void> | void;
  onClose: () => Promise<void> | void;
};

function formatSeconds(seconds: number) {
  const safe = Math.max(0, Math.floor(seconds));
  const minutes = String(Math.floor(safe / 60)).padStart(2, "0");
  const rest = String(safe % 60).padStart(2, "0");

  return `${minutes}:${rest}`;
}

function conciseResultText(text: string, maxLength = 56) {
  const normalized = String(text || "").replace(/\s+/g, " ").trim();

  if (normalized.length <= maxLength + 14) {
    return normalized;
  }

  const punctuationIndexes = ["。", "！", "？", ";", "；"].map((mark) =>
    normalized.indexOf(mark),
  );
  const sentenceEnd = punctuationIndexes
    .filter((index) => index >= Math.floor(maxLength * 0.65) && index <= maxLength + 14)
    .sort((a, b) => a - b)[0];

  if (sentenceEnd !== undefined) {
    return normalized.slice(0, sentenceEnd + 1);
  }

  return normalized.slice(0, maxLength);
}

export function MeetingPanel({
  meeting,
  isBusy,
  onStart,
  onSend,
  onTick,
  onFinish,
  onClose,
}: MeetingPanelProps) {
  const [draft, setDraft] = useState("");
  const [remainingSeconds, setRemainingSeconds] = useState(120);
  const [localLive, setLocalLive] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [introDone, setIntroDone] = useState(false);

  if (!meeting) {
    return null;
  }

  const resultText =
    typeof meeting.result === "string"
      ? meeting.result
      : meeting.result && typeof meeting.result === "object"
        ? String(
            meeting.result.summary ||
              meeting.result.decision ||
              meeting.result.result ||
              "",
          )
        : "";
  const resultTitle =
    meeting.result && typeof meeting.result === "object"
      ? String(meeting.result.title || "会议结果")
      : "会议结果";
  const isLive = meeting.phase === "live" || localLive;
  const hasResult = Boolean(resultText);
  const participantIds = useMemo(
    () => meeting.participants ?? Object.keys(MEETING_SEATS),
    [meeting.participants],
  );
  const introText = `${meeting.title || "会议"}\n\n${meeting.content || "团队需要围绕当前局面做一次对齐。"}`;

  useEffect(() => {
    setRemainingSeconds(Number(meeting.remaining_seconds || meeting.duration_seconds || 120));
    setLocalLive(meeting.phase === "live");
  }, [meeting.meeting_id, meeting.phase, meeting.remaining_seconds, meeting.duration_seconds]);

  useEffect(() => {
    setIntroDone(false);
  }, [meeting.meeting_id]);

  useEffect(() => {
    if (!isLive || hasResult) {
      return;
    }

    const countdownTimer = window.setInterval(() => {
      setRemainingSeconds((current) => Math.max(0, current - 1));
    }, 1000);

    return () => window.clearInterval(countdownTimer);
  }, [hasResult, isLive]);

  useEffect(() => {
    if (!isLive || hasResult || isBusy) {
      return;
    }

    const tickTimer = window.setInterval(() => {
      onTick();
    }, MEETING_TICK_INTERVAL_MS);

    return () => window.clearInterval(tickTimer);
  }, [hasResult, isBusy, isLive, onTick]);

  useEffect(() => {
    if (!isLive || hasResult || remainingSeconds > 0 || isBusy) {
      return;
    }

    onFinish();
  }, [hasResult, isBusy, isLive, onFinish, remainingSeconds]);

  async function start() {
    if (isStarting || isLive || hasResult) {
      return;
    }

    setIsStarting(true);
    try {
      await onStart();
      setLocalLive(true);
    } finally {
      setIsStarting(false);
    }
  }

  function submit() {
    const message = draft.trim();
    if (!message) {
      return;
    }
    onSend(message);
    setDraft("");
  }

  if (hasResult) {
    return (
      <section className="scene-page meeting-result-page">
        <TypewriterPanel
          actionLabel="返回主世界"
          className="meeting-result-paper"
          chunkSize={2}
          intervalMs={70}
          kicker={`${meeting.clock || meeting.time || "会议"} · 会议结果`}
          title={resultTitle}
          text={conciseResultText(resultText)}
          onAction={onClose}
        />
      </section>
    );
  }

  if (!introDone) {
    return (
      <section className="scene-page meeting-result-page">
        <TypewriterPanel
          actionLabel="进入会议室"
          className="meeting-result-paper"
          chunkSize={2}
          intervalMs={70}
          kicker={`${meeting.clock || meeting.time || "会议"} · 固定会议`}
          title={meeting.title || "会议"}
          text={introText}
          onAction={() => setIntroDone(true)}
        />
      </section>
    );
  }

  return (
    <section className="scene-page meeting-scene-page">
      <div className="room-stage">
        <img className="room-stage-bg" src={MEETING_SCENE_ASSET} alt="会议室" />
        <div className="room-actors">
          {participantIds.map((actorId) => {
            const seat = MEETING_SEATS[actorId] ?? { left: 50, top: 60 };
            const latestLine = [...(meeting.transcript ?? [])]
              .reverse()
              .find((line) => line.actor_id === actorId);
            const latestSpeech = latestLine?.speech || latestLine?.text || latestLine?.content;
            return (
              <div
                className="room-actor"
                key={actorId}
                style={{ left: `${seat.left}%`, top: `${seat.top}%` }}
              >
                {latestSpeech ? (
                  <p className="room-bubble">{latestSpeech}</p>
                ) : null}
                <img src={MEETING_ACTOR_ASSETS[actorId] || MEETING_ACTOR_ASSETS.xionglaoban} alt={ACTOR_DISPLAY_NAMES[actorId] || actorId} />
                <strong>{latestLine?.display_name || ACTOR_DISPLAY_NAMES[actorId] || actorId}</strong>
              </div>
            );
          })}
        </div>
      </div>

      <aside className="room-side">
        <header className="feature-panel-header">
          <div>
            <p className="overlay-kicker">{meeting.clock || meeting.time || "会议"}</p>
            <h2>{meeting.title || "会议室"}</h2>
          </div>
        </header>

        <section className="meeting-control-panel">
          <p>{meeting.content || "团队正在等待会议开始。"}</p>
          <strong className={isLive ? "meeting-timer is-live" : "meeting-timer"}>
            {isLive ? formatSeconds(remainingSeconds) : "待开始"}
          </strong>
        </section>

        <div className="feature-actions meeting-actions">
          <button type="button" onClick={start} disabled={isBusy || isStarting || isLive}>
            {isStarting ? "启动中..." : isLive ? "会议进行中" : "开始会议"}
          </button>
        </div>

        <div className="inline-input-row">
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                submit();
              }
            }}
            placeholder="在会议中说点什么"
          />
          <button type="button" onClick={submit} disabled={isBusy}>
            发送
          </button>
        </div>
      </aside>
    </section>
  );
}
