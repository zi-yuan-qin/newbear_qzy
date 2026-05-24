# BE-005 company_profile 参数化模板 — 规划文档

## 模块概述

将 `company_profile.py` 从固定 dict 改为参数化函数 `build_company_profile(params)`，不同种子参数生成不同公司描述文案。向前兼容——空 params 返回默认值。

## 文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/src/core/config/company_profile.py` | 重写 | 保留默认常量 + 新增参数化函数 |

## 参数 → 文案映射

### cash / runway_days → funding_status

| 条件 | 文案 |
|------|------|
| `runway_days <= 6` | "账上现金极度紧张，仅能支撑约 N 天运营，每一天的决策都生死攸关。" |
| `runway_days 7-10` | "账上现金勉强维持，约能支撑 N 天运营，没有浪费的余地。" |
| `runway_days > 10` | "资金相对充裕，约能支撑 N 天运营，还有一定试错空间。" |

### strategy_consensus → team_state 策略方向感

| 条件 | 文案 |
|------|------|
| > 65 | "团队方向高度一致，大家对核心目标有清晰的共识，争论主要集中在执行层面。" |
| 40-65 | "团队方向大体一致，但在优先级和节奏上存在分歧，偶尔会因路径选择产生摩擦。" |
| < 40 | "团队在核心方向上有明显分歧，各成员对'什么是最重要的事'看法不一致，讨论时常触及根本路线。" |

### team_morale → team_history 近期氛围

| 条件 | 文案 |
|------|------|
| > 70 | "近期团队氛围不错，即使有压力也愿意互相兜底。" |
| 45-70 | "近期团队内部已经因需求反复与交付延期产生过明显摩擦。" |
| < 45 | "近期团队氛围有些低落，成员之间因压力产生过明显摩擦，信任需要修复。" |

### resource_scarcity → working_style 资源压力段

在现有 working_style 基础上增加一句资源描述：

| 条件 | 追加文案 |
|------|---------|
| > 70 | "同时资源极度紧张——人手、预算、时间都紧，所有人都需要在高压力下做出取舍。" |
| 40-70 | "资源偏紧但还能转得动，需要精打细算，但不到弹尽粮绝的程度。" |
| < 40 | "资源尚可调配，团队有一定空间去做选择和尝试。" |

## 接口定义

```python
def build_company_profile(params: dict) -> dict
```

`params` 键：`cash`(int), `runway_days`(int), `strategy_consensus`(int), `team_morale`(int), `resource_scarcity`(int)
所有键可选，缺失时用默认值。

## 假设清单

1. `params` 中的数值范围与 seed_generator 一致（cash 2000-8000, runway_days 5-15, consensus 20-80, morale 30-90, scarcity 未定义则默认 50）
2. 默认值取中位：cash=5000, runway_days=10, consensus=55, morale=60, scarcity=50
3. `build_company_profile({})` 返回与当前 `COMPANY_PROFILE` 完全一致的文案
4. 函数只改文案字段，不改 `name`/`business`/`team_size`/`short_term_goals` 等结构字段
