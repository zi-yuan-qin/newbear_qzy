# BE-006 seed_loader + world_factory 重写 — 规划文档

## 模块概述

实现 `load_world_seed(user_id)` 和 `create_initial_world_state(seed)` 的完整逻辑，接入孙迦勒的种子生成器，使每局游戏初始状态由种子参数驱动。

## 文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/src/core/world/seed_loader.py` | 修改 | load_world_seed(user_id) 实现新路径 |
| `backend/src/core/world/world_factory.py` | 修改 | create_initial_world_state(seed) 应用种子参数 |

## 数据流

```
load_world_seed(user_id=42)
  │
  ├─ seed_generator.generate(42) → SessionSeed
  ├─ build_company_profile(seed.company_params) → company dict
  └─ characters + _modifier[actor_id] = seed.character_modifiers[actor_id]
       │
       ▼
create_initial_world_state(seed=SessionSeed)
  │
  ├─ cash = seed.company_params.cash (or 5000 if seed=None)
  ├─ stress = 30 + modifier.stress_base_offset
  └─ energy = 70 + modifier.energy_base_offset
```

## 接口定义

无新增接口，仅实现 P0-002 中已定义的签名。

## 假设

1. `seed_generator.generate()` 总是返回有效的 SessionSeed
2. `character_modifiers` key 与 CHARACTER_ORDER 中的 actor_id 一一对应
3. 偏移量范围 [-10, 10] 不会导致 stress/energy 超出 [0, 100]
4. `_modifier` 挂载到 character dict 是内部实现细节，不影响 serializer

## 风险

| 风险 | 等级 | 预案 |
|------|------|------|
| seed_generator import 失败 | 低 | 已在 main 分支验证可用 |
| 偏移量导致 stress/energy 越界 | 低 | clamp(0, 100) 保护 |
