from __future__ import annotations

from src.core.map.map_loader import load_world_map
from src.core.map.map_semantics import normalize_location_name
from src.core.world.runtime_state import (
    ActorRuntimeState,
    CompanyRuntimeState,
    WorldRuntimeState,
)
from src.core.world.seed_loader import SessionSeed, load_world_seed


def create_initial_world_state(seed: SessionSeed | None = None) -> WorldRuntimeState:
    world_seed = load_world_seed()

    if seed is not None:
        cash = float(seed.company_params.get("cash", 5000.0))
    else:
        cash = 5000.0

    company = CompanyRuntimeState(
        name=world_seed["company"]["name"],
        cash=cash,
        day=1,
        step=0,
        clock="09:00",
    )

    actors = {}

    for character in world_seed["characters"]:
        work = character["character_profile"].get("work", {})
        actor_id = character["actor_id"]

        if seed is not None:
            modifier = seed.character_modifiers.get(actor_id, {})
        else:
            modifier = {}

        stress = 30 + int(modifier.get("stress_base_offset", 0))
        energy = 70 + int(modifier.get("energy_base_offset", 0))

        actors[actor_id] = ActorRuntimeState(
            actor_id=actor_id,
            display_name=character["display_name"],
            location=normalize_location_name(work.get("office", "开放办公区")),
            stress=max(0, min(100, stress)),
            energy=max(0, energy),
            mood="normal",
            current_task="",
            last_speech="",
        )

    return WorldRuntimeState(
        company=company,
        actors=actors,
        map_data=load_world_map(),
    )
