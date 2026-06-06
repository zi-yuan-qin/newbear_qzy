from __future__ import annotations

from typing import Any

from src.core.config.content_pool import load_pool, select_items

INCIDENT_SLOTS = ("10:30", "14:30")
MEETING_SLOTS = ("12:00", "16:00")
PANTRY_SLOTS = ("17:30",)


def slot_index(clock: str, slots: tuple[str, ...]) -> int | None:
    normalized_clock = str(clock or "").strip()
    try:
        return slots.index(normalized_clock)
    except ValueError:
        return None


def scheduled_item(
    category: str,
    pool_ids: list[str],
    seed_id: str,
    slots: tuple[str, ...],
    index: int,
) -> dict[str, Any] | None:
    if pool_ids:
        items_by_id = {str(item.get("id")): item for item in load_pool(category)}
        ordered_items = [items_by_id[item_id] for item_id in pool_ids if item_id in items_by_id]
    else:
        ordered_items = select_items(category, [], len(slots), seed_id)

    if index >= len(ordered_items):
        return None

    return ordered_items[index]
