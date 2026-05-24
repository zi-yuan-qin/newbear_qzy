# P0-002 Shared 层接口定义 — 开发日志

## 当前状态：Phase 5 完成 → 待用户确认后进入 P0-002 完成

---

## 变更记录

| 时间 | 阶段 | 变更 | 原因 |
|------|------|------|------|
| 2026-05-22 | Phase 1 | 需求澄清：向前兼容策略（无参=旧行为，传参=新行为） | 不阻塞孙迦勒，不破坏 server.py |
| 2026-05-22 | Phase 2 | 创建规划文档 `docs/plan-p0-002-shared-interface.md` | 按 vibecoding-workflow 规范 |
| 2026-05-22 | Phase 3 | 修改 `seed_loader.py`：新增 SessionSeed dataclass + build_company_profile 签名 + load_world_seed(user_id=None) | 按规划文档执行 |
| 2026-05-22 | Phase 3 | 修改 `world_factory.py`：create_initial_world_state(seed=None) 向前兼容 | 按规划文档执行 |
| 2026-05-22 | Phase 5 | 验证：SessionSeed 可 import/实例化、旧 test 通过、server 启动正常 | 兼容性确认 |

---

## 决策记录

| # | 问题 | 决策 | 理由 |
|---|------|------|------|
| 1 | 旧代码还是兼容 | 向前兼容：`load_world_seed(user_id=None)` | 旧调用不传参走默认，新调用走种子 |
| 2 | SessionSeed 放哪 | 放在 `seed_loader.py` 内 | 孙迦勒/陈鸿淼已依赖 seed_loader 的 load_world_seed |
| 3 | build_company_profile 签名的 params 类型 | dict（扁平键值对） | 与 SessionSeed.company_params 一致 |
