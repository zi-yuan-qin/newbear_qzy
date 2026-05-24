from __future__ import annotations

from copy import deepcopy
from typing import Any

COMPANY_PROFILE: dict[str, object] = {
    "name": "熊起东方",
    "company_type": "早期创业阶段的游戏化人格探索科技公司",
    "business": "通过多智能体交互与情境模拟技术，构建沉浸式的职场与社会互动体验产品，用于帮助用户进行自我认知与职业人格探索。",
    "stage": "刚完成天使轮融资，处于产品验证与市场验证并行推进阶段。",
    "team_size": 4,
    "runway_days": 10,
    "funding_status": "账上现金仅能支撑约 10 天运营。",
    "short_term_goals": [
        "必须在极短时间内完成可演示版本（Demo）。",
        "需要尽快获取第一批真实用户反馈。",
        "尽快推出可验证价值的产品，并找到活下去的路径。",
    ],
    "external_pressure": "市场窗口期正在迅速缩短，竞争对手开始加速布局。",
    "team_history": "近期团队内部已经因需求反复与交付延期产生过明显摩擦。",
    "team_state": "团队信任与协作效率处于一个紧绷但仍可运转的状态。",
    "working_style": "团队规模极小，仅由 4 名核心成员组成，因此所有人都需要在高压力、高不确定性的环境下快速决策与协作。",
}


def build_company_profile(params: dict[str, Any]) -> dict[str, Any]:
    """根据 company_params 生成公司描述 dict。

    params 可选键：
        cash, runway_days, strategy_consensus, team_morale, resource_scarcity
    所有键可选，缺失时使用默认中位值，保证与旧版文案一致。
    """
    profile = deepcopy(dict(COMPANY_PROFILE))

    runway_days = int(params.get("runway_days", 10))
    cash = int(params.get("cash", 5000))
    consensus = int(params.get("strategy_consensus", 55))
    morale = int(params.get("team_morale", 60))
    scarcity = int(params.get("resource_scarcity", 50))

    # ── runway_days + funding_status ──
    profile["runway_days"] = runway_days

    if runway_days <= 6:
        profile["funding_status"] = (
            f"账上现金极度紧张，仅能支撑约 {runway_days} 天运营，"
            f"每一天的决策都生死攸关。"
        )
    elif runway_days <= 10:
        # 7-10 天：保留原版文案模板，与默认值一致
        profile["funding_status"] = (
            f"账上现金仅能支撑约 {runway_days} 天运营。"
        )
    else:
        profile["funding_status"] = (
            f"资金相对充裕，约能支撑 {runway_days} 天运营，"
            f"还有一定试错空间。"
        )

    # ── strategy_consensus → team_state ──
    if consensus > 65:
        profile["team_state"] = (
            "团队方向高度一致，大家对核心目标有清晰的共识，"
            "争论主要集中在执行层面。"
        )
    elif consensus >= 40:
        # 40-65：保留原版文案，与默认值一致
        pass
    else:
        profile["team_state"] = (
            "团队在核心方向上有明显分歧，"
            "各成员对'什么是最重要的事'看法不一致，"
            "讨论时常触及根本路线。"
        )

    # ── team_morale → team_history ──
    if morale > 70:
        profile["team_history"] = (
            "近期团队氛围不错，即使有压力也愿意互相兜底。"
        )
    elif morale >= 45:
        # 45-70：保留原版文案，与默认值一致
        pass
    else:
        profile["team_history"] = (
            "近期团队氛围有些低落，成员之间因压力产生过明显摩擦，"
            "信任需要修复。"
        )

    # ── resource_scarcity → working_style ──
    if scarcity > 70:
        profile["working_style"] = (
            f"{COMPANY_PROFILE['working_style']}"
            f"同时资源极度紧张——人手、预算、时间都紧，"
            f"所有人都需要在高压力下做出取舍。"
        )
    elif scarcity < 40:
        profile["working_style"] = (
            f"{COMPANY_PROFILE['working_style']}"
            f"目前资源尚可调配，团队有一定空间去做选择和尝试。"
        )
    # 40-70：保留原版文案，与默认值一致

    return profile
