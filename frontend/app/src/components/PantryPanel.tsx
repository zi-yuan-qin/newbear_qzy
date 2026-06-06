import { useEffect, useState } from "react";
import type { PantryState } from "../types/api";
import { TypewriterPanel } from "./TypewriterPanel";

const PANTRY_SCENE_ASSET = "/assets/pantry/room.png";
const PANTRY_TICK_INTERVAL_MS = 5200;
const PANTRY_ACTOR_ASSETS: Record<string, string> = {
  xionglaoban: "/assets/meeting/boss-front.png",
  xiongshichang: "/assets/actors/xiongshichang/idle_front.webp",
  xiongxingzheng: "/assets/meeting/admin-left.png",
  xiongjishu: "/assets/actors/xiongjishu/idle_front.webp",
};
const ACTOR_DISPLAY_NAMES: Record<string, string> = {
  xionglaoban: "熊老板",
  xiongshichang: "熊市场",
  xiongxingzheng: "熊行政",
  xiongjishu: "熊技术",
  user: "我",
};
const PANTRY_SEATS: Record<string, { left: number; top: number }> = {
  xiongshichang: { left: 28, top: 68 },
  xionglaoban: { left: 64, top: 53 },
  xiongxingzheng: { left: 41, top: 56 },
  xiongjishu: { left: 74, top: 65 },
};

type PantryPanelProps = {
  pantry: PantryState | null | undefined;
  isBusy: boolean;
  onSend: (message: string) => Promise<void> | void;
  onTick: () => Promise<void> | void;
  onLeave: () => Promise<void> | void;
};

export function PantryPanel({ pantry, isBusy, onSend, onTick, onLeave }: PantryPanelProps) {
  const [draft, setDraft] = useState("");
  const [introDone, setIntroDone] = useState(false);

  useEffect(() => {
    setIntroDone(false);
  }, [pantry?.pantry_id]);

  useEffect(() => {
    if (!pantry || !introDone || isBusy || draft.trim()) {
      return;
    }

    const timer = window.setInterval(() => {
      onTick();
    }, PANTRY_TICK_INTERVAL_MS);

    return () => window.clearInterval(timer);
  }, [draft, introDone, isBusy, onTick, pantry]);

  if (!pantry) {
    return null;
  }

  const introText = `${pantry.title || "茶水间闲聊"}\n\n${pantry.content || "这里的聊天比会议轻一点，但信息量不一定少。"}`;

  if (!introDone) {
    return (
      <section className="scene-page meeting-result-page">
        <TypewriterPanel
          actionLabel="进入茶水间"
          className="meeting-result-paper"
          chunkSize={2}
          intervalMs={70}
          kicker="茶水间 · 闲谈开始"
          title={pantry.title || "茶水间闲聊"}
          text={introText}
          onAction={() => setIntroDone(true)}
        />
      </section>
    );
  }

  function submit() {
    const message = draft.trim();
    if (!message) {
      return;
    }
    onSend(message);
    setDraft("");
  }

  return (
    <section className="scene-page pantry-scene-page">
      <div className="room-stage">
        <img className="room-stage-bg" src={PANTRY_SCENE_ASSET} alt="茶水间" />
        <div className="room-actors">
          {(pantry.participants ?? Object.keys(PANTRY_SEATS)).map((actorId) => {
            const seat = PANTRY_SEATS[actorId] ?? { left: 50, top: 68 };
            const latestLine = [...(pantry.transcript ?? [])]
              .reverse()
              .find((line) => line.actor_id === actorId);
            const latestSpeech = latestLine?.speech || latestLine?.text || latestLine?.content;
            return (
              <div
                className={`room-actor pantry-room-actor actor-${actorId}`}
                key={actorId}
                style={{ left: `${seat.left}%`, top: `${seat.top}%` }}
              >
                {latestSpeech ? (
                  <p className="room-bubble">{latestSpeech}</p>
                ) : null}
                <img src={PANTRY_ACTOR_ASSETS[actorId] || PANTRY_ACTOR_ASSETS.xionglaoban} alt={ACTOR_DISPLAY_NAMES[actorId] || actorId} />
                <strong>{latestLine?.display_name || ACTOR_DISPLAY_NAMES[actorId] || actorId}</strong>
              </div>
            );
          })}
        </div>
      </div>

      <aside className="room-side">
        <header className="feature-panel-header">
          <div>
            <p className="overlay-kicker">茶水间</p>
            <h2>{pantry.title || "茶水间闲聊"}</h2>
          </div>
          <button type="button" onClick={onLeave} disabled={isBusy}>
            离开
          </button>
        </header>

        <p>{pantry.content || "这里的聊天比会议轻一点，但信息量不一定少。"}</p>

        <div className="inline-input-row pantry-input-row">
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                submit();
              }
            }}
            placeholder="在茶水间说点什么"
          />
          <button type="button" onClick={submit} disabled={isBusy}>
            发送
          </button>
        </div>
      </aside>
    </section>
  );
}
