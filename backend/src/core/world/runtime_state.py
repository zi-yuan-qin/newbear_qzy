from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ActorRuntimeState:
    actor_id: str
    display_name: str
    location: str = "开放办公区"
    stress: int = 30
    energy: int = 70
    mood: str = "normal"
    current_task: str = ""
    intent: str = ""
    move_to: str = ""
    last_speech: str = ""
    memory: list[str] = field(default_factory=list)
    pending_action: dict[str, Any] = field(default_factory=dict)
    memory_stream: list[MemoryRecord] = field(default_factory=list)
    memory_next_id: int = 1
    reflection_importance_buffer: int = 0




@dataclass
class CompanyRuntimeState:
    name: str
    cash: float = 5000.0
    day: int = 1
    step: int = 0
    clock: str = "09:00"
    phase: str = "prepare"
    logs: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class UserInputRecord:
    input_id: int
    raw_text: str
    is_empty: bool
    day: int
    step: int
    clock: str
    actor_reactions: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class EncounterRecord:
    encounter_id: int
    location: str
    actor_ids: list[str]
    actor_names: list[str]
    summary: str
    day: int
    step: int
    clock: str
    dialogue: list[dict[str, str]] = field(default_factory=list)
@dataclass
class IncidentRecord:
    incident_id: str
    time: str
    title: str
    content: str
    day: int
    step: int
    clock: str

@dataclass
class MeetingEventRecord:
    meeting_id: str
    time: str
    title: str
    content: str
    participants: list[str]
    day: int
    step: int
    clock: str


@dataclass
class ActiveMeetingState:
    meeting_id: str
    time: str
    title: str
    content: str
    participants: list[str]
    day: int
    step: int
    clock: str
    phase: str = "intro"
    duration_seconds: int = 120
    remaining_seconds: int = 120
    transcript: list[dict[str, str]] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
@dataclass
class ActivePantryState:
    pantry_id: str
    time: str
    title: str
    content: str
    participants: list[str]
    day: int
    step: int
    clock: str
    phase: str = "live"
    transcript: list[dict[str, str]] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActiveReportState:
    report_id: str
    time: str
    title: str
    trait_summary: str
    letter_title: str
    letter_body: str
    scores: dict[str, int]
    radar_items: list[dict[str, Any]]
    evidence: list[str]
    day: int
    step: int
    clock: str
    provider: str = "fallback"
    visible: bool = True


@dataclass
class MemoryRecord:
    memory_id: int
    kind: str
    text: str
    day: int
    step: int
    clock: str
    importance: int = 1
    tags: list[str] = field(default_factory=list)
    related_actor_ids: list[str] = field(default_factory=list)

@dataclass
class WorldRuntimeState:
    company: CompanyRuntimeState
    actors: dict[str, ActorRuntimeState]
    seed_id: str = ""
    seed_summary: dict[str, Any] = field(default_factory=dict)
    incident_pool_ids: list[str] = field(default_factory=list)
    meeting_topic_ids: list[str] = field(default_factory=list)
    pantry_topic_ids: list[str] = field(default_factory=list)
    report_template_ids: list[str] = field(default_factory=list)
    session_record_id: str = ""
    user_inputs: list[UserInputRecord] = field(default_factory=list)
    encounters: list[EncounterRecord] = field(default_factory=list)
    map_data: dict[str, Any] = field(default_factory=dict)
    pending_incident: IncidentRecord | None = None
    incidents: list[IncidentRecord] = field(default_factory=list)
    triggered_incident_ids: set[str] = field(default_factory=set)
    active_meeting: ActiveMeetingState | None = None
    meetings: list[MeetingEventRecord] = field(default_factory=list)
    triggered_meeting_ids: set[str] = field(default_factory=set)
    active_pantry: ActivePantryState | None = None
    triggered_pantry_ids: set[str] = field(default_factory=set)
    active_report: ActiveReportState | None = None
    report_generated: bool = False
    report_saved: bool = False

