from __future__ import annotations

from src.core.world.day_schedule import INCIDENT_SLOTS, scheduled_item, slot_index
from src.core.world.runtime_state import IncidentRecord, WorldRuntimeState


def trigger_incident_for_clock(world: WorldRuntimeState, clock: str) -> IncidentRecord | None:
    normalized_clock = str(clock or "").strip()
    index = slot_index(normalized_clock, INCIDENT_SLOTS)

    if index is None:
        return None

    item = scheduled_item(
        "incidents",
        world.incident_pool_ids,
        world.seed_id,
        INCIDENT_SLOTS,
        index,
    )
    if item is None:
        return None

    incident_id = str(item.get("id") or f"incident-slot-{index + 1}")

    if incident_id in world.triggered_incident_ids:
        return None

    incident = IncidentRecord(
        incident_id=incident_id,
        time=normalized_clock,
        title=str(item.get("title", "")).strip(),
        content=str(item.get("content", "")).strip(),
        day=world.company.day,
        step=world.company.step,
        clock=normalized_clock,
    )

    world.pending_incident = incident
    world.incidents.append(incident)
    world.triggered_incident_ids.add(incident_id)

    return incident
