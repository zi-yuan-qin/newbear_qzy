from __future__ import annotations

import random
import string
from datetime import datetime, timezone
from typing import Any

from src.core.config.content_pool import load_pool
from src.core.config.content_pool import select_items as pool_select
from src.core.world.seed_loader import SessionSeed

# ── 参数采样范围 ──
_CASH_RANGE = (2000, 8000)
_CASH_STEP = 500
_RUNWAY_RANGE = (5, 15)
_CONSENSUS_RANGE = (20, 80)
_MORALE_RANGE = (30, 90)
_STRESS_OFFSET = 10
_ENERGY_OFFSET = 10

# ── 每局选中的内容池条目数量 ──
_INCIDENT_COUNT = 2
_MEETING_COUNT = 2
_PANTRY_COUNT = 2
_REPORT_COUNT = 1


def generate(user_id: int | None = None) -> SessionSeed:
    """生成完整的 SessionSeed。

    1. 随机采样公司参数
    2. 如有 user_id，尝试从 user_profile 加载画像并加权
    3. 从内容池中确定性选取条目
    """
    seed_id = _generate_seed_id()

    # ── 1. 公司参数 ──
    company_params = {
        "cash": _random_step(*_CASH_RANGE, _CASH_STEP),
        "runway_days": random.randint(*_RUNWAY_RANGE),
        "strategy_consensus": random.randint(*_CONSENSUS_RANGE),
        "team_morale": random.randint(*_MORALE_RANGE),
        "resource_scarcity": random.randint(20, 80),
    }

    # ── 2. 用户画像加权 ──
    profile = _load_user_profile(user_id)
    if profile:
        company_params = _apply_profile_weighting(company_params, profile)

    # ── 3. 角色 modifier ──
    character_modifiers = _generate_character_modifiers()

    # ── 4. 内容池选取 ──
    incident_ids = _select_pool_ids("incidents", _INCIDENT_COUNT, seed_id, company_params)
    meeting_ids = _select_pool_ids("meetings", _MEETING_COUNT, seed_id, company_params)
    pantry_ids = _select_pool_ids("pantry", _PANTRY_COUNT, seed_id, company_params)
    report_ids = _select_pool_ids("reports", _REPORT_COUNT, seed_id, company_params)

    return SessionSeed(
        seed_id=seed_id,
        company_params=company_params,
        character_modifiers=character_modifiers,
        incident_pool_ids=incident_ids,
        meeting_topic_ids=meeting_ids,
        pantry_topic_ids=pantry_ids,
        report_template_ids=report_ids,
    )


def preview(user_id: int | None = None) -> dict[str, Any]:
    """生成种子预览（调试用），返回人类可读摘要。"""
    seed = generate(user_id)
    return {
        "seed_id": seed.seed_id,
        "summary": _build_summary(seed),
    }


# ─────────────────── 内部函数 ───────────────────


def _generate_seed_id() -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand_hex = "".join(random.choices(string.hexdigits[:16], k=4))
    return f"seed-{date_str}-{rand_hex}"


def _random_step(low: int, high: int, step: int) -> int:
    """从 range(low, high+1) 中按 step 间隔随机采样。"""
    steps = list(range(low, high + 1, step))
    return random.choice(steps) if steps else low


def _load_user_profile(user_id: int | None) -> dict[str, Any] | None:
    if user_id is None:
        return None
    try:
        from src.core.db.user_profile import get_user_profile
        return get_user_profile(user_id)
    except Exception:
        return None


def _apply_profile_weighting(
    company_params: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    """根据用户画像调整种子参数。"""
    personality = profile.get("personality_data", {})
    if not isinstance(personality, dict):
        return company_params

    # openness > 70 → 高变体事件权重（这里通过提高 morale 模拟更多探索欲）
    openness = personality.get("openness", 50)
    if isinstance(openness, (int, float)) and openness > 70:
        company_params["team_morale"] = min(90, company_params["team_morale"] + 10)

    # conflict_style = "avoid" → 降低冲突概率（通过降低 consensus 分歧度）
    conflict_style = personality.get("conflict_style", "")
    if conflict_style == "avoid":
        company_params["strategy_consensus"] = min(80, company_params["strategy_consensus"] + 15)

    # closest_ally → 影响团队状态（通过 morale 体现）
    ally = personality.get("closest_ally")
    if ally:
        company_params["team_morale"] = min(90, company_params["team_morale"] + 5)

    return company_params


def _generate_character_modifiers() -> dict[str, dict[str, Any]]:
    """为每个角色生成随机的 stress/energy 偏移。"""
    from src.core.config.character_profiles import CHARACTER_ORDER

    modifiers: dict[str, dict[str, Any]] = {}
    for actor_id in CHARACTER_ORDER:
        modifiers[actor_id] = {
            "stress_base_offset": random.randint(-_STRESS_OFFSET, _STRESS_OFFSET),
            "energy_base_offset": random.randint(-_ENERGY_OFFSET, _ENERGY_OFFSET),
        }
    return modifiers


def _select_pool_ids(
    category: str,
    count: int,
    seed_id: str,
    company_params: dict[str, Any],
) -> list[str]:
    """从内容池中选出 count 个条目的 id 列表。"""
    all_items = load_pool(category)
    if not all_items:
        return []

    # 按公司参数条件过滤
    from src.core.config.content_pool import filter_by_conditions
    filtered = filter_by_conditions(all_items, company_params)
    if not filtered:
        filtered = all_items  # fallback to all items

    selected = pool_select(category, [], count, seed_id)
    # If select_items returned empty or not enough, fallback
    if not selected:
        selected = pool_select(category, [], count, seed_id)

    return [item["id"] for item in selected[:count]]


def _build_summary(seed: SessionSeed) -> str:
    """生成人类可读的种子摘要。"""
    cash = seed.company_params.get("cash", 5000)
    runway = seed.company_params.get("runway_days", 10)
    morale = seed.company_params.get("team_morale", 60)

    if cash < 3500:
        cash_desc = "资金紧张"
    elif cash > 6000:
        cash_desc = "资金相对充裕"
    else:
        cash_desc = "资金处于临界线"

    if morale > 70:
        morale_desc = "团队士气高昂"
    elif morale < 45:
        morale_desc = "团队气氛有些低落"
    else:
        morale_desc = "团队状态平稳"

    return f"本局资金{cash_desc}（${cash}），可支撑{runway}天，{morale_desc}。"
