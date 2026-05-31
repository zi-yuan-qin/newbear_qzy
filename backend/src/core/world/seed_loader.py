from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from src.core.config.character_profiles import (
    CHARACTER_ORDER,
    CHARACTER_PROFILES,
    RELATIONSHIP_NOTES,
)
from src.core.config.company_profile import COMPANY_PROFILE
from src.core.config.job_profiles import JOB_PROFILES


@dataclass
class SessionSeed:
    """一局游戏的参数化种子，由 seed_generator 生成。"""

    seed_id: str
    company_params: dict[str, Any] = field(default_factory=dict)
    character_modifiers: dict[str, dict[str, Any]] = field(default_factory=dict)
    incident_pool_ids: list[str] = field(default_factory=list)
    meeting_topic_ids: list[str] = field(default_factory=list)
    pantry_topic_ids: list[str] = field(default_factory=list)
    report_template_ids: list[str] = field(default_factory=list)


def load_world_seed(user_id: int | None = None) -> dict[str, Any]:
    """把公司表、岗位表、人物表装配成一个统一的世界初始对象。

    user_id=None 时走固定配置（兼容旧版）；user_id 非空时接入种子生成器。
    """

    if user_id is not None:
        from src.core.config.company_profile import build_company_profile

        from src.core.config.seed_generator import generate

        seed = generate(user_id)
        company = build_company_profile(seed.company_params)

        characters: list[dict[str, Any]] = []
        for actor_id in CHARACTER_ORDER:
            character_profile = deepcopy(CHARACTER_PROFILES[actor_id])
            job_key = str(character_profile.get("job_key", "general")).strip() or "general"
            job_profile = deepcopy(JOB_PROFILES.get(job_key, JOB_PROFILES["general"]))
            relationships = deepcopy(RELATIONSHIP_NOTES.get(actor_id, {}))

            characters.append(
                {
                    "actor_id": actor_id,
                    "display_name": character_profile.get("display_name", actor_id),
                    "job_key": job_key,
                    "character_profile": character_profile,
                    "job_profile": job_profile,
                    "relationships": relationships,
                    "_modifier": seed.character_modifiers.get(actor_id, {}),
                }
            )

        return {
            "company": company,
            "characters": characters,
        }

    # ── user_id=None：固定配置（兼容旧版） ──

    company = deepcopy(COMPANY_PROFILE)

    characters: list[dict[str, Any]] = []

    for actor_id in CHARACTER_ORDER:
        character_profile = deepcopy(CHARACTER_PROFILES[actor_id])

        job_key = str(character_profile.get("job_key", "general")).strip() or "general"
        job_profile = deepcopy(JOB_PROFILES.get(job_key, JOB_PROFILES["general"]))

        relationships = deepcopy(RELATIONSHIP_NOTES.get(actor_id, {}))

        characters.append(
            {
                "actor_id": actor_id,
                "display_name": character_profile.get("display_name", actor_id),
                "job_key": job_key,
                "character_profile": character_profile,
                "job_profile": job_profile,
                "relationships": relationships,
            }
        )

    return {
        "company": company,
        "characters": characters,
    }
