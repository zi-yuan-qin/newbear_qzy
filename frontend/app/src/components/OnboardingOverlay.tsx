import { useEffect, useMemo, useState } from "react";
import type { OnboardingCharacter, OnboardingState } from "../types/api";
import { TypewriterPanel } from "./TypewriterPanel";

const ACTOR_PORTRAITS: Record<string, string> = {
  xionglaoban: "/assets/actors/xionglaoban/idle_front.webp",
  xiongjishu: "/assets/actors/xiongjishu/idle_front.webp",
  xiongshichang: "/assets/actors/xiongshichang/idle_front.webp",
  xiongxingzheng: "/assets/actors/xiongxingzheng/idle_front.webp",
};

type OnboardingOverlayProps = {
  onboarding: OnboardingState | undefined;
  open: boolean;
  onClose: () => void;
};

function buildCompanyText(onboarding: OnboardingState) {
  const company = onboarding.company ?? {};
  const goals = Array.isArray(company.short_term_goals) ? company.short_term_goals : [];

  return [
    `欢迎来到${company.name || "熊起东方"}。这家公司不大，梦想倒是挺大：${company.business || "把产品做出来，把用户留下来"}。现在处在${company.stage || "要命但还挺有希望"}阶段，现金像早高峰电梯一样紧张，大家说话都很有理，账上数字更有理。`,
    `团队目前的状态是：${company.team_state || "各有各的本事，也各有各的压力"}。短期目标先记住一句话，${goals[0] || "把 Demo 做稳，把发布会扛过去"}。`,
    `${company.external_pressure ? `外面也不太消停：${company.external_pressure}。` : ""}${company.working_style ? `这里的工作方式偏${company.working_style}，所以你最好多听、多问、少闭门造车。` : ""}`,
    "你是这家公司的产品经理。记得和你的搭子多交流，点击自动推进，这个世界才会运行。",
  ]
    .filter(Boolean)
    .join("\n\n");
}

function buildCharacterIntro(character: OnboardingCharacter) {
  const name = character.display_name || "这位同事";
  const role = character.work_title || character.job_title || character.role_name || character.role || "公司搭子";
  const lens = character.company_lens || character.kpi || "";
  const speaking = character.speaking_style || "";
  const drives = Array.isArray(character.core_drives)
    ? character.core_drives.slice(0, 2).join("、")
    : "";

  return `${name}，${role}。${lens || "他看公司的角度很现实，基本不相信空口画饼。"}${drives ? `心里惦记着${drives}。` : ""}${speaking ? `说话风格是：${speaking}。` : ""}跟他合作的秘诀很简单：把事情说具体，把锅放桌面上。`;
}

export function OnboardingOverlay({ onboarding, open, onClose }: OnboardingOverlayProps) {
  const [mode, setMode] = useState<"company" | "characters">("company");

  const companyText = useMemo(
    () => (onboarding ? buildCompanyText(onboarding) : ""),
    [onboarding],
  );

  useEffect(() => {
    if (!open) {
      setMode("company");
    }
  }, [open]);

  if (!open || !onboarding) {
    return null;
  }

  const company = onboarding.company ?? {};
  const characters = onboarding.characters ?? [];

  return (
    <section className="overlay-backdrop onboarding-backdrop">
      {mode === "company" ? (
        <TypewriterPanel
          actionLabel="认识团队"
          className="onboarding-card onboarding-printer"
          kicker="入职培训 · 公司背景"
          title={`欢迎加入${company.name || "熊起东方"}`}
          text={companyText}
          onAction={() => setMode("characters")}
        />
      ) : (
        <article className="overlay-card onboarding-card onboarding-roster">
          <header>
            <div>
              <p className="overlay-kicker">入职培训 · 团队成员</p>
              <h2>你将和这些小熊一起推进项目</h2>
            </div>
            <button type="button" onClick={onClose}>
              开始模拟
            </button>
          </header>
          <div className="onboarding-grid">
            {characters.map((character) => (
              <article className={`roster-card actor-${character.actor_id}`} key={character.actor_id}>
                <div className="roster-portrait">
                  <img
                    src={ACTOR_PORTRAITS[character.actor_id] || ACTOR_PORTRAITS.xionglaoban}
                    alt={character.display_name || character.actor_id}
                  />
                </div>
                <div>
                  <strong>{character.display_name || character.actor_id}</strong>
                  <span>{character.role || character.job_title || character.work_title || "团队成员"}</span>
                  <p>{buildCharacterIntro(character)}</p>
                </div>
              </article>
            ))}
          </div>
        </article>
      )}
    </section>
  );
}
