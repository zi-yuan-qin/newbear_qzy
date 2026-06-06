from __future__ import annotations

import json
import re
from typing import Any

from src.core.llm.ark_client import ArkClientError, ark_chat
from src.core.world.seed_loader import load_world_seed
from src.core.world.runtime_state import WorldRuntimeState
from src.core.world.memory_engine import append_actor_memory


def run_meeting_tick(world: WorldRuntimeState) -> list[dict[str, str]]:
    meeting = world.active_meeting
    if meeting is None or meeting.phase != "live":
        return []

    participants = [
        actor_id
        for actor_id in meeting.participants
        if actor_id in world.actors
    ]

    if not participants:
        return []

    seed = load_world_seed()
    character_by_id = {
        item["actor_id"]: item
        for item in seed["characters"]
    }

    actors_payload = []
    for actor_id in participants:
        runtime_actor = world.actors[actor_id]
        character = character_by_id.get(actor_id, {})

        actors_payload.append(
            {
                "actor_id": actor_id,
                "display_name": runtime_actor.display_name,
                "job_role": character.get("job_profile", {}).get("role_name", ""),
                "personality": character.get("character_profile", {}).get("personality", {}),
                "current_task": runtime_actor.current_task,
                "last_speech": runtime_actor.last_speech,
            }
        )

    messages = _build_meeting_tick_messages(
        meeting={
            "title": meeting.title,
            "content": meeting.content,
            "clock": meeting.clock,
        },
        actors=actors_payload,
        transcript=meeting.transcript[-16:],
    )

    try:
        raw_reply = ark_chat(messages=messages, max_tokens=700)
        parsed = _parse_json_object(raw_reply)
        lines = _normalize_lines(parsed.get("lines", []), participants)
    except (ArkClientError, ValueError):
        lines = _fallback_lines(world, participants)

    if not lines:
        lines = _fallback_lines(world, participants)

    for line in lines:
        actor_id = line["actor_id"]
        actor = world.actors.get(actor_id)
        if actor is None:
            continue

        actor.last_speech = line["content"]
        actor.current_task = f"参与会议讨论：{meeting.title}"

        meeting.transcript.append(
            {
                "speaker": actor.display_name,
                "actor_id": actor_id,
                "kind": "actor",
                "content": line["content"],
            }
        )

    meeting.transcript = meeting.transcript[-80:]
    return lines


def finish_meeting(world: WorldRuntimeState) -> dict[str, str] | None:
    meeting = world.active_meeting
    if meeting is None:
        return None

    if meeting.phase == "result" and meeting.result:
        return {
            "title": str(meeting.result.get("title", "")),
            "summary": str(meeting.result.get("summary", "")),
        }

    result = _generate_meeting_result(world)
    meeting.result = result
    meeting.phase = "result"
    meeting.remaining_seconds = 0

    memory_text = f"{world.company.clock} 会议结果：{meeting.title}。{result['summary']}"
    for actor_id in meeting.participants:
        append_actor_memory(
            world,
            actor_id=actor_id,
            kind="meeting",
            text=memory_text,
            clock=world.company.clock,
            related_actor_ids=[item for item in meeting.participants if item != actor_id],
            tags=["meeting", "meeting_result"],
        )

    world.company.logs.append(
        {
            "type": "meeting_result",
            "clock": world.company.clock,
            "meeting_id": meeting.meeting_id,
            "title": meeting.title,
            "summary": result["summary"],
        }
    )

    return result


def _generate_meeting_result(world: WorldRuntimeState) -> dict[str, str]:
    meeting = world.active_meeting
    if meeting is None:
        return {"title": "会议结果", "summary": "会议已结束。"}

    transcript_text = "\n".join(
        f"{line.get('speaker') or line.get('actor_id')}: {line.get('content') or line.get('speech') or ''}"
        for line in meeting.transcript[-60:]
    )
    messages = [
        {
            "role": "system",
            "content": "\n".join(
                [
                    "你是会议纪要整理器。",
                    "请根据会议主题、背景和全部发言，生成一个清晰、可执行的最终会议结果。",
                    "summary 必须是一句话，50 个汉字左右，保留决定和关键理由，不要展开长篇分析。",
                    "不要奉承产品经理，也不要回避风险。",
                    "只输出 JSON，不要 Markdown，不要解释。",
                    'JSON 格式：{"title":"会议结果标题","summary":"一句约50字的最终方案"}',
                ]
            ),
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    f"会议标题：{meeting.title}",
                    f"会议内容：{meeting.content}",
                    "会议发言：",
                    transcript_text,
                ]
            ),
        },
    ]

    try:
        raw_reply = ark_chat(messages=messages, max_tokens=180)
        parsed = _parse_json_object(raw_reply)
        title = str(parsed.get("title", "") or "会议结果").strip()
        summary = str(parsed.get("summary", "") or "").strip()
        if summary:
            return {"title": title[:80], "summary": _compact_meeting_summary(summary)}
    except (ArkClientError, ValueError):
        pass

    return {
        "title": "会议结果",
        "summary": _compact_meeting_summary(
            f"围绕“{meeting.title}”，团队决定先按风险可控的方式推进，明确数据边界、责任归属和下一步行动。"
        ),
    }


def _compact_meeting_summary(text: str, max_length: int = 56) -> str:
    normalized = " ".join(str(text or "").split())
    if len(normalized) <= max_length + 14:
        return normalized

    for index, char in enumerate(normalized):
        if char in "。！？;；" and int(max_length * 0.65) <= index <= max_length + 14:
            return normalized[: index + 1]

    return normalized[:max_length]


def _build_meeting_tick_messages(
    *,
    meeting: dict[str, Any],
    actors: list[dict[str, Any]],
    transcript: list[dict[str, str]],
) -> list[dict[str, str]]:
    system_prompt = "\n".join(
        [
            "你是职场会议模拟器的对话生成器。",
            "这是一场固定节点触发的真实团队会议。",
            "你需要让参会角色围绕会议标题和内容继续讨论。",
            "所有人共享会议记录，必须接住前面的人和产品经理刚刚说过的话。",
            "用户是产品经理，大家重视他的发言，但不要奉承，不要无脑同意。",
            "每轮生成 1 到 3 句发言即可，不需要所有人都说。",
            "发言要短、具体、有角色岗位视角，避免空话。",
            "不要写旁白，不要写动作，只写说出口的话。",
            "只输出 JSON，不要 Markdown，不要解释。",
            'JSON 格式：{"lines":[{"actor_id":"角色ID","content":"一句发言"}]}',
        ]
    )

    user_prompt = "\n".join(
        [
            "会议：",
            json.dumps(meeting, ensure_ascii=False),
            "参会角色：",
            json.dumps(actors, ensure_ascii=False),
            "最近会议记录：",
            json.dumps(transcript, ensure_ascii=False),
            "请生成下一小轮会议发言。",
        ]
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _normalize_lines(raw_lines: Any, participants: list[str]) -> list[dict[str, str]]:
    if not isinstance(raw_lines, list):
        return []

    allowed = set(participants)
    lines: list[dict[str, str]] = []

    for item in raw_lines:
        if not isinstance(item, dict):
            continue

        actor_id = str(item.get("actor_id", "") or "").strip()
        content = str(item.get("content", "") or item.get("speech", "") or "").strip()

        if actor_id not in allowed or not content:
            continue

        lines.append(
            {
                "actor_id": actor_id,
                "content": content[:180],
            }
        )

    return lines[:3]


def _fallback_lines(world: WorldRuntimeState, participants: list[str]) -> list[dict[str, str]]:
    meeting = world.active_meeting
    if meeting is None:
        return []

    fallback_by_actor_id = {
        "xionglaoban": "先把这件事拆成收益、风险和底线，别只看眼前好处。",
        "xiongshichang": "我关心的是这个合作能不能换来真实流量，以及对外口径怎么说。",
        "xiongxingzheng": "我得先确认数据边界和成本，不能把后续风险留成窟窿。",
        "xiongjishu": "技术上可以配合，但数据怎么脱敏、接口怎么控权得先讲清楚。",
    }

    start = len(meeting.transcript) % max(1, len(participants))
    picked = participants[start : start + 2]
    if len(picked) < 2:
        picked = (participants + participants)[:2]

    return [
        {
            "actor_id": actor_id,
            "content": fallback_by_actor_id.get(actor_id, "我先把我的顾虑说清楚，方便大家继续往下定。"),
        }
        for actor_id in picked
    ]


def _parse_json_object(text: str) -> dict[str, Any]:
    source = str(text or "").strip()
    if not source:
        raise ValueError("empty response")

    try:
        data = json.loads(source)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", source, re.S)
        if not match:
            raise ValueError("no json object")
        data = json.loads(match.group(0))

    if not isinstance(data, dict):
        raise ValueError("response is not an object")

    return data
