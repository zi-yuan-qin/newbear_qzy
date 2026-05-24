# P0-002 Shared 层接口定义 — 规划文档

## 模块概述

在 `seed_loader.py` 中定义 `SessionSeed` dataclass 和三个参数化接口签名，作为秦梓源/孙迦勒/陈鸿淼三方并行开发的公共契约。保持向后兼容——不传参走默认固定配置，传参走参数化种子。

## 架构设计

### 契约边界

```
孙迦勒 (BE-001)               秦梓源 (BE-005/006)           陈鸿淼 (BE-007)
     │                              │                            │
     └──────── SessionSeed ──────────┼────────────────────────────┘
                                    │
                          seed_loader.py
                          ├── SessionSeed (dataclass)
                          ├── load_world_seed(user_id=None) → dict
                          ├── build_company_profile(params) → dict
                          └── create_initial_world_state(seed=None) → WorldRuntimeState
```

### 关键设计决策

**向前兼容策略**：
- `load_world_seed(user_id=None)` — 旧代码不传参，走现有固定配置逻辑，行为不变
- `load_world_seed(user_id="xxx")` — 新代码传 user_id，后续 BE-006 实现参数化逻辑
- `create_initial_world_state(seed=None)` — 不传 seed 走现有固定逻辑，传了走种子

## 文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/src/core/world/seed_loader.py` | 修改 | 新增 dataclass + 接口签名 + 旧函数签名改为兼容 |

## 接口定义

### SessionSeed dataclass

```python
@dataclass
class SessionSeed:
    seed_id: str
    company_params: dict
    character_modifiers: dict[str, dict]   # key = actor_id
    incident_pool_ids: list[str]
    meeting_topic_ids: list[str]
    pantry_topic_ids: list[str]
    report_template_ids: list[str]
```

### 三个接口签名

```python
from typing import Any

def load_world_seed(user_id: int | None = None) -> dict[str, Any]:
    """加载世界初始种子。user_id=None 时走固定配置（兼容旧版）。

    user_id 非空时，后续由 BE-006 实现调用 seed_generator.generate(user_id)。
    """

def build_company_profile(params: dict[str, Any]) -> dict[str, Any]:
    """根据 company_params 生成公司描述 dict。后续由 BE-005 实现参数化。"""

def create_initial_world_state(seed: SessionSeed | None = None) -> WorldRuntimeState:
    """创建初始世界状态。seed=None 时走固定逻辑（兼容旧版）。

    seed 非空时，后续由 BE-006 实现应用 character_modifiers 和 company_params。
    """
```

### 旧函数签名变更

| 旧签名 | 新签名 | 理由 |
|--------|--------|------|
| `load_world_seed()` | `load_world_seed(user_id=None)` | 加可选参数，默认行为不变 |
| `create_initial_world_state()` | `create_initial_world_state(seed=None)` | 加可选参数，默认行为不变 |

## 假设清单

1. `SessionSeed` 的 `company_params` 字段是扁平 dict（如 `{"cash": 5000, "runway_days": 10}`），不做嵌套结构
2. `character_modifiers` 的 key 是 actor_id 字符串（如 `"xionglaoban"`），value 是偏移量 dict
3. `build_company_profile` 的 params 参数结构与 `SessionSeed.company_params` 一致
4. `create_initial_world_state(seed=None)` 内部调用 `load_world_seed()`（不传参）走旧逻辑
5. 接口签名仅定义，真正的参数化实现留给 BE-005/006
6. 不修改 `world_factory.py`（那是 BE-006 的事）

## 风险点

| 风险 | 等级 | 预案 |
|------|------|------|
| 现有调用方 `world_factory.py` 调 `load_world_seed()` 无参，签名变更可能破坏 | 低 | Python 默认参数，旧调用语法不变 |
| 循环导入（seed_loader → world_factory 已有 import） | 低 | dataclass 定义在 seed_loader 中，world_factory 已依赖 seed_loader，方向正确 |
| `SessionSeed` 字段在后续实现中不够用 | 中 | 可以先加字段，dataclass 默认值兜底 |
