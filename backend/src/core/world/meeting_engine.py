from __future__ import annotations

from src.core.world.day_schedule import MEETING_SLOTS, scheduled_item, slot_index
from src.core.world.runtime_state import (
    ActiveMeetingState,
    MeetingEventRecord,
    WorldRuntimeState,
)


def trigger_meeting_for_clock(world: WorldRuntimeState, clock: str) -> ActiveMeetingState | None:
    normalized_clock = str(clock or "").strip()

    if world.active_meeting is not None:
        return world.active_meeting

    index = slot_index(normalized_clock, MEETING_SLOTS)
    if index is None:
        return None

    item = scheduled_item(
        "meetings",
        world.meeting_topic_ids,
        world.seed_id,
        MEETING_SLOTS,
        index,
    )
    if item is None:
        return None

    meeting_id = str(item.get("id") or f"meeting-slot-{index + 1}")

    if meeting_id in world.triggered_meeting_ids:
        return None

    participants = list(world.actors.keys())

    record = MeetingEventRecord(
        meeting_id=meeting_id,
        time=normalized_clock,
        title=str(item.get("title", "")),
        content=str(item.get("content", "")),
        participants=participants,
        day=world.company.day,
        step=world.company.step,
        clock=normalized_clock,
    )

    meeting = ActiveMeetingState(
        meeting_id=record.meeting_id,
        time=record.time,
        title=record.title,
        content=record.content,
        participants=record.participants,
        day=record.day,
        step=record.step,
        clock=record.clock,
        phase="intro",
        duration_seconds=120,
        remaining_seconds=120,
    )


    world.meetings.append(record)
    world.active_meeting = meeting
    world.triggered_meeting_ids.add(meeting_id)

    for actor_id in participants:
        actor = world.actors.get(actor_id)
        if actor:
            actor.location = "会议室"
            actor.intent = "communicate"
            actor.current_task = f"参加会议：{record.title}"

    world.company.logs.append(
        {
            "type": "meeting_triggered",
            "clock": normalized_clock,
            "meeting_id": meeting_id,
            "title": record.title,
            "participants": participants,
        }
    )

    return meeting

def enter_active_meeting(world: WorldRuntimeState) -> ActiveMeetingState | None:
    meeting = world.active_meeting
    if meeting is None:
        return None

    if meeting.phase == "intro":
        meeting.phase = "waiting"

    return meeting


def start_active_meeting(world: WorldRuntimeState) -> ActiveMeetingState | None:
    meeting = world.active_meeting
    if meeting is None:
        return None

    if meeting.phase in {"intro", "waiting"}:
        meeting.phase = "live"
        meeting.remaining_seconds = meeting.duration_seconds

    return meeting


def add_user_meeting_message(world: WorldRuntimeState, message: str) -> ActiveMeetingState | None:
    meeting = world.active_meeting
    clean_message = str(message or "").strip()

    if meeting is None or not clean_message:
        return meeting

    meeting.transcript.append(
        {
            "speaker": "产品经理",
            "actor_id": "user",
            "kind": "user",
            "content": clean_message,
        }
    )

    return meeting

def close_active_meeting(world: WorldRuntimeState) -> None:
    if world.active_meeting is None:
        return

    world.company.logs.append(
        {
            "type": "meeting_closed",
            "clock": world.company.clock,
            "meeting_id": world.active_meeting.meeting_id,
            "title": world.active_meeting.title,
        }
    )

    world.active_meeting = None
