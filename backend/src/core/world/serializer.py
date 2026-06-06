from __future__ import annotations

from src.core.world.runtime_state import WorldRuntimeState
from src.core.world.seed_loader import load_world_seed
from typing import Any


def serialize_world_state(world: WorldRuntimeState) -> dict:
    """把运行时世界状态转换成可 JSON 化的 dict。"""

    return {
        "seed": {
            "seed_id": world.seed_id,
            "summary": world.seed_summary,
            "incident_pool_ids": world.incident_pool_ids,
            "meeting_topic_ids": world.meeting_topic_ids,
            "pantry_topic_ids": world.pantry_topic_ids,
            "report_template_ids": world.report_template_ids,
            "session_record_id": world.session_record_id,
        },
        "company": {
            "name": world.company.name,
            "cash": world.company.cash,
            "day": world.company.day,
            "step": world.company.step,
            "clock": world.company.clock,
            "phase": world.company.phase,
            "logs": world.company.logs,
        },
        "actors": [
            {
                "actor_id": actor.actor_id,
                "display_name": actor.display_name,
                "location": actor.location,
                "stress": actor.stress,
                "energy": actor.energy,
                "mood": actor.mood,
                "current_task": actor.current_task,
                "intent": actor.intent,
                "move_to": actor.move_to,
                "last_speech": actor.last_speech,
                "memory": actor.memory,
                "pending_action": actor.pending_action,
                "memory_stream": [
                    {
                        "memory_id": item.memory_id,
                        "kind": item.kind,
                        "text": item.text,
                        "clock": item.clock,
                        "importance": item.importance,
                        "tags": item.tags,
                        "related_actor_ids": item.related_actor_ids,
                    }
                    for item in actor.memory_stream[-10:]
                ],
                "reflection_importance_buffer": actor.reflection_importance_buffer,

            }
            for actor in world.actors.values()
        ],
        "user_inputs": [
            {
                "input_id": record.input_id,
                "raw_text": record.raw_text,
                "is_empty": record.is_empty,
                "day": record.day,
                "step": record.step,
                "clock": record.clock,
                "actor_reactions": record.actor_reactions,
            }
            for record in world.user_inputs
        ],
        "map": world.map_data,
        "encounters": [
            {
                "encounter_id": encounter.encounter_id,
                "location": encounter.location,
                "actor_ids": encounter.actor_ids,
                "actor_names": encounter.actor_names,
                "summary": encounter.summary,
                "day": encounter.day,
                "step": encounter.step,
                "clock": encounter.clock,
                "display_names": encounter.actor_names,
                "dialogue": encounter.dialogue,
            }
            for encounter in world.encounters
        ],
        "pending_incident": (
            {
                "incident_id": world.pending_incident.incident_id,
                "time": world.pending_incident.time,
                "title": world.pending_incident.title,
                "content": world.pending_incident.content,
                "day": world.pending_incident.day,
                "step": world.pending_incident.step,
                "clock": world.pending_incident.clock,
            }
            if world.pending_incident
            else None
        ),
        "incidents": [
            {
                "incident_id": incident.incident_id,
                "time": incident.time,
                "title": incident.title,
                "content": incident.content,
                "day": incident.day,
                "step": incident.step,
                "clock": incident.clock,
            }
            for incident in world.incidents
        ],
        "active_meeting": (
            {
                "meeting_id": world.active_meeting.meeting_id,
                "time": world.active_meeting.time,
                "title": world.active_meeting.title,
                "content": world.active_meeting.content,
                "participants": world.active_meeting.participants,
                "day": world.active_meeting.day,
                "step": world.active_meeting.step,
                "clock": world.active_meeting.clock,
                "phase": world.active_meeting.phase,
                "duration_seconds": world.active_meeting.duration_seconds,
                "remaining_seconds": world.active_meeting.remaining_seconds,
                "transcript": world.active_meeting.transcript,
                "result": world.active_meeting.result,
            }
            if world.active_meeting
            else None
        ),
        "meetings": [
            {
                "meeting_id": meeting.meeting_id,
                "time": meeting.time,
                "title": meeting.title,
                "content": meeting.content,
                "participants": meeting.participants,
                "day": meeting.day,
                "step": meeting.step,
                "clock": meeting.clock,
            }
            for meeting in world.meetings
        ],
        "active_pantry": serialize_active_pantry(world.active_pantry),
        "active_report": serialize_active_report(world.active_report),
        "onboarding": serialize_onboarding(),
            }


def serialize_onboarding() -> dict[str, Any]:
    seed = load_world_seed()
    company = seed["company"]

    characters: list[dict[str, Any]] = []
    for character in seed["characters"]:
        profile = character.get("character_profile", {}) or {}
        job = character.get("job_profile", {}) or {}
        personality = profile.get("personality", {}) or {}
        work = profile.get("work", {}) or {}

        characters.append(
            {
                "actor_id": character.get("actor_id", ""),
                "display_name": character.get("display_name", ""),
                "work_title": profile.get("work_title", ""),
                "job_title": profile.get("job_title", ""),
                "role_name": job.get("role_name", ""),
                "age": profile.get("age", ""),
                "education": profile.get("education", ""),
                "commute": profile.get("commute", ""),
                "marital_status": profile.get("marital_status", ""),
                "economic_status": profile.get("economic_status", ""),
                "core_drives": personality.get("core_drives", []) or [],
                "habits": personality.get("habits", []) or [],
                "speaking_style": personality.get("speaking_style", ""),
                "shadow_pattern": personality.get("shadow_pattern", ""),
                "company_lens": work.get("company_lens", ""),
                "responsibility": job.get("responsibility", ""),
                "power": job.get("power", ""),
                "kpi": job.get("kpi", ""),
            }
        )

    return {
        "company": company,
        "characters": characters,
    }


def serialize_active_pantry(pantry: Any) -> dict[str, Any] | None:
    if pantry is None:
        return None

    return {
        "pantry_id": pantry.pantry_id,
        "time": pantry.time,
        "title": pantry.title,
        "content": pantry.content,
        "participants": pantry.participants,
        "day": pantry.day,
        "step": pantry.step,
        "clock": pantry.clock,
        "phase": pantry.phase,
        "transcript": pantry.transcript,
        "result": pantry.result,
        "active": True,
        "actors": [
            {
                "actor_id": actor_id,
            }
            for actor_id in pantry.participants
        ],
    }


def serialize_active_report(report: Any) -> dict[str, Any] | None:
    if report is None:
        return None

    return {
        "report_id": report.report_id,
        "time": report.time,
        "title": report.title,
        "trait_summary": report.trait_summary,
        "letter_title": report.letter_title,
        "letter_body": report.letter_body,
        "scores": report.scores,
        "radar_items": report.radar_items,
        "evidence": report.evidence,
        "day": report.day,
        "step": report.step,
        "clock": report.clock,
        "provider": report.provider,
        "visible": report.visible,
    }
