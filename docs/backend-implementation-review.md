# 后端实现复盘：相对于原文档的变更与缺口

本文对照当前仓库中的后端规划文档，复盘后端已经改了什么、怎么改的，以及站在整个项目交付链路上还缺什么。

对照的原文档包括：

- `docs/plan-p0-001-database.md`
- `docs/plan-p0-002-shared-interface.md`
- `docs/plan-be-005-company-profile.md`
- `docs/plan-be-006-seed-worldfactory.md`
- `docs/frontend-backend-contract.md`

当前代码观察点：

- 当前分支：`feature/be-006-seed-loader-worldfactory`
- 当前分支相对 `main` 的显式 PR 改动：`seed_loader.py`、`world_factory.py`、`backend/test_be006.py`、两份 BE-006 文档
- 仓库内已有后端实现还包含 P0-001、P0-002、BE-005、seed_generator、认证、API、世界序列化等模块
- 工作区存在若干前端未提交改动，本文不纳入后端复盘

## 总体结论

后端已经完成了三类基础能力：

1. 用户、登录会话、用户输入、报告、用户画像、历史 session 记录的 SQLite 存储骨架。
2. `SessionSeed`、`load_world_seed(user_id=None)`、`create_initial_world_state(seed=None)` 这组 shared 层接口形状。
3. 公司画像参数化、种子生成器、角色初始状态 modifier、内容池选择的部分能力。

但从“用户真实玩一局游戏”的完整主链路看，参数化世界还没有闭环：

```text
用户注册/登录/重置
  -> 生成或读取该用户本局 SessionSeed
  -> 创建参数化 WorldRuntimeState
  -> 保存 seed_id / seed_summary / 内容池 id
  -> 事件、会议、茶水间、报告按本局 seed 选择内容
  -> session_records 和 user_profiles 随游戏推进更新
```

当前实际主链路仍然大多是：

```text
用户注册/登录/重置
  -> create_initial_world_state()
  -> load_world_seed()
  -> 固定公司/固定角色/固定内容主路径
```

所以现在的状态可以概括为：底层零件已经搭了一批，但服务端入口、运行时状态、内容事件系统、历史记录系统之间还没有完全接起来。

## P0-001 数据库扩展

### 原文档目标

`plan-p0-001-database.md` 要求新增：

- `user_profiles` 表，用于跨 session 保存用户人格画像。
- `session_records` 表，用于保存每一局游戏的 seed、报告、状态、历史记录。
- `user_profile.py`，封装 profile CRUD。
- `session_store.py`，封装 session record CRUD。
- `backend/test_database.py`，覆盖 5 条必需测试。

### 实际改动

实际代码已经在 `backend/src/core/db/database.py` 中新增了两张表：

- `user_profiles`
- `session_records`

并且保留了已有表：

- `users`
- `sessions`
- `user_messages`
- `reports`

新增了两个数据库封装模块：

- `backend/src/core/db/user_profile.py`
- `backend/src/core/db/session_store.py`

也新增了测试脚本：

- `backend/test_database.py`

### 怎么改的

`user_profiles` 记录用户级长期画像：

- `personality_data`：JSON 字符串，保存人格分析数据。
- `total_sessions`：累计局数。
- `total_playtime_seconds`：累计游玩时长。
- `preferred_decision_style`、`preferred_conflict_style`、`avg_input_length`：后续分析字段。
- `relationship_scores`：JSON 字符串。
- `created_at`、`updated_at`：时间戳。

`user_profile.py` 实现：

- `init_user_profile(user_id)`：`INSERT OR IGNORE` 初始化用户画像。
- `get_user_profile(user_id)`：读取并解析 JSON 字段。
- `update_user_profile(user_id, personality_data)`：将新人格数据 merge 到旧 JSON 中。
- `increment_session_count(user_id)`：累计局数 +1。

`session_records` 记录每一局游戏：

- `session_id`
- `user_id`
- `seed_id`
- `seed_summary`
- `day_completed`
- `final_clock`
- `report_id`
- `report_scores`
- `started_at`
- `ended_at`
- `status`

`session_store.py` 实现：

- `create_session_record(user_id, seed_id, seed_summary)`
- `get_session_record(session_id)`
- `list_user_sessions(user_id, limit=20)`
- `complete_session(session_id, report_id, scores)`
- `abandon_session(session_id)`

### 与原文档的符合度

基本符合 P0-001 的表结构和函数封装要求。

实现还额外保留了 `sessions.current_state_json` 作为当前世界状态 JSON 存储，这与原文档中“不新增 world_state 表，状态放在 JSON blob 里”的方向一致。

### 偏差与缺口

1. `auth_service.create_user()` 目前只创建 `users` 和 `sessions`，没有调用 `init_user_profile(user_id)`。
2. `server.py` 目前没有使用 `create_session_record()` 创建本局记录。
3. `/api/report/close` 目前只关闭报告视图，没有调用 `complete_session()`。
4. 游戏结束时没有把 `day_completed`、`final_clock`、`report_scores` 回写到 `session_records`。
5. 没有实现原规划中提到的历史接口：
   - `GET /api/sessions`
   - `GET /api/sessions/<id>`
   - `POST /api/sessions/replay`
6. `increment_session_count()` 已实现，但主流程没有调用。

## P0-002 Shared 层接口

### 原文档目标

`plan-p0-002-shared-interface.md` 要求先定义三方协作契约：

- `SessionSeed`
- `load_world_seed(user_id=None)`
- `build_company_profile(params)`
- `create_initial_world_state(seed=None)`

并要求旧调用方式保持兼容：

- 不传 `user_id` 走旧固定世界。
- 不传 `seed` 走旧固定初始状态。

### 实际改动

`SessionSeed` 定义在：

- `backend/src/core/world/seed_loader.py`

字段包括：

- `seed_id`
- `company_params`
- `character_modifiers`
- `incident_pool_ids`
- `meeting_topic_ids`
- `pantry_topic_ids`
- `report_template_ids`

`load_world_seed(user_id=None)` 已经改成可选参数形式。

`create_initial_world_state(seed=None)` 已经改成可选 seed 形式。

`build_company_profile(params)` 最终放在：

- `backend/src/core/config/company_profile.py`

而不是 `seed_loader.py`。

### 怎么改的

`SessionSeed` 是 dataclass，用来承载“一局游戏生成参数”，不是直接的世界状态。

`load_world_seed(user_id=None)` 分两条路径：

- `user_id is None`：复制固定 `COMPANY_PROFILE`、角色 profile、岗位 profile、关系备注。
- `user_id is not None`：调用 `seed_generator.generate(user_id)`，再用 `build_company_profile(seed.company_params)` 生成公司 profile，并给角色挂上 `_modifier`。

`create_initial_world_state(seed=None)` 分两条路径：

- `seed is None`：现金 5000，角色压力 30，精力 70。
- `seed is not None`：从 `seed.company_params["cash"]` 读取初始现金，从 `seed.character_modifiers` 读取角色压力/精力偏移。

### 与原文档的符合度

接口形状基本符合。

`build_company_profile` 的位置与 P0-002 文档中的接口草案不同，但从职责划分看，放在 `config/company_profile.py` 更合理。P0-002 只是 shared 契约文档，后续 BE-005 把它移到公司配置模块可以接受。

### 偏差与缺口

1. `create_initial_world_state(seed)` 内部仍然调用 `load_world_seed()`，没有把 seed 或 user_id 传入 `load_world_seed`。
2. `load_world_seed(user_id)` 生成出的 `_modifier` 目前不是 `world_factory` 实际使用的来源；`world_factory` 是直接读传入的 `seed.character_modifiers`。
3. `SessionSeed` 中的内容池 id 字段还没有进入 `WorldRuntimeState`。
4. `serialize_world_state()` 也没有输出 `seed_id`、`seed_summary`、本局内容池 id 等字段。

## BE-005 公司画像参数化

### 原文档目标

`plan-be-005-company-profile.md` 要求将固定公司 profile 改成参数化模板：

- `runway_days` 影响 `funding_status`
- `strategy_consensus` 影响 `team_state`
- `team_morale` 影响 `team_history`
- `resource_scarcity` 影响 `working_style`
- `build_company_profile({})` 必须与默认旧文案保持兼容

### 实际改动

`backend/src/core/config/company_profile.py` 保留了：

- `COMPANY_PROFILE`

并新增：

- `build_company_profile(params)`

### 怎么改的

`build_company_profile(params)` 先 `deepcopy` 默认公司 profile，然后读取：

- `runway_days`
- `cash`
- `strategy_consensus`
- `team_morale`
- `resource_scarcity`

再按阈值覆盖部分文案：

- runway 短：资金极度紧张。
- runway 中：保留类似默认文案。
- runway 长：资金相对充裕。
- consensus 高：团队方向高度一致。
- consensus 中：保留默认 `team_state`。
- consensus 低：核心方向明显分歧。
- morale 高：团队愿意互相兜底。
- morale 中：保留默认 `team_history`。
- morale 低：氛围低落、信任需要修复。
- scarcity 高：在 `working_style` 后追加资源极度紧张描述。
- scarcity 低：在 `working_style` 后追加资源尚可调配描述。

### 与原文档的符合度

核心能力已实现，参数字段和大部分阈值符合原文档。

### 偏差与缺口

1. 文档中 `runway_days 7-10` 的文案是“账上现金勉强维持...没有浪费的余地”，实际代码是“账上现金仅能支撑约 N 天运营。”，偏向保留旧文案。
2. 文档中 `strategy_consensus 40-65` 要生成“团队方向大体一致...”文案，实际代码选择 `pass`，保留默认文案。
3. 文档中 `resource_scarcity 40-70` 要追加“资源偏紧但还能转得动...”，实际代码选择保留默认文案。
4. `cash` 被读取但没有直接参与文案生成，主要通过 `_build_summary()` 或外部 runtime cash 表达。
5. 参数化公司 profile 只有在 `load_world_seed(user_id)` 被调用时才生效；当前真实服务端世界创建路径没有调用这个分支。

## BE-006 seed_loader + world_factory

### 原文档目标

`plan-be-006-seed-worldfactory.md` 要求：

- `load_world_seed(user_id)` 接入 `seed_generator.generate(user_id)`。
- 用 `build_company_profile(seed.company_params)` 生成公司信息。
- 将角色 modifier 挂到角色数据。
- `create_initial_world_state(seed)` 应用：
  - `cash`
  - `stress_base_offset`
  - `energy_base_offset`

### 实际改动

当前分支相对 `main` 的主要改动正是 BE-006：

- 修改 `backend/src/core/world/seed_loader.py`
- 修改 `backend/src/core/world/world_factory.py`
- 新增 `backend/test_be006.py`
- 新增 `docs/plan-be-006-seed-worldfactory.md`
- 新增 `docs/log-be-006-seed-worldfactory.md`

### 怎么改的

`load_world_seed(user_id)`：

1. 如果 `user_id is not None`：
   - 延迟导入 `generate`
   - 延迟导入 `build_company_profile`
   - 调用 `seed = generate(user_id)`
   - 调用 `company = build_company_profile(seed.company_params)`
   - 遍历 `CHARACTER_ORDER`
   - 复制角色 profile、岗位 profile、关系备注
   - 在角色 dict 中添加 `_modifier`
2. 如果 `user_id is None`：
   - 走旧固定公司和固定角色装配逻辑

`create_initial_world_state(seed)`：

1. 先调用 `world_seed = load_world_seed()`。
2. 如果传入 seed：
   - `company.cash = seed.company_params.get("cash", 5000.0)`
   - 每个 actor 的 `stress = 30 + stress_base_offset`
   - 每个 actor 的 `energy = 70 + energy_base_offset`
3. 如果没有 seed：
   - 保持旧默认值。

`backend/test_be006.py` 验证：

- 不传 seed 时旧行为不变。
- 手动传 `SessionSeed` 时 cash、stress、energy 会变化。
- `load_world_seed(user_id)` 能返回 4 个角色。
- 多次调用会产生随机差异。
- 旧 `load_world_seed()` 路径仍兼容。
- `SessionSeed` 和 `build_company_profile` import 正常。

### 与原文档的符合度

局部函数层面基本符合 BE-006 文档。

### 偏差与缺口

1. `create_initial_world_state(seed)` 仍然调用 `load_world_seed()`，所以公司文案没有应用 `seed.company_params`。
2. `load_world_seed(user_id)` 自己内部会生成一个 seed，但这个 seed 没有被返回给调用方，调用方也拿不到 `seed_id` 和内容池 id。
3. `create_initial_world_state(seed)` 使用的 seed 和 `load_world_seed(user_id)` 内部生成的 seed 不是同一个入口，两个设计方向有割裂。
4. `energy` 只做了下限保护 `max(0, energy)`，没有像 `stress` 一样限制到 100。
5. `backend/test_be006.py` 是脚本式测试，不是 pytest 风格；能验证局部逻辑，但不能验证真实 API 主流程。
6. 服务端没有在注册、登录、重置时生成 seed 或传入 seed。

## seed_generator 与内容池

### 原文档目标

虽然 `seed_generator.py` 不在 BE-006 PR diff 中，但它是 BE-006 依赖的上游。按当前代码，它承担：

- 生成随机公司参数。
- 读取用户画像并加权。
- 为角色生成压力/精力偏移。
- 从内容池选择 incident、meeting、pantry、report id。

### 实际改动

`backend/src/core/config/seed_generator.py` 已经实现：

- `generate(user_id=None)`
- `preview(user_id=None)`
- `_load_user_profile(user_id)`
- `_apply_profile_weighting(company_params, profile)`
- `_generate_character_modifiers()`
- `_select_pool_ids(category, count, seed_id, company_params)`

内容池目录已经存在：

- `content_pool/incidents/*.json`
- `content_pool/meetings/*.json`
- `content_pool/pantry/*.json`
- `content_pool/reports/*.json`

`content_pool/__init__.py` 实现：

- `load_pool(category)`
- `select_items(category, pool_ids, count, seed_id)`
- `filter_by_conditions(items, conditions)`

### 怎么改的

`generate()` 随机生成：

- `cash`：2000 到 8000，步长 500。
- `runway_days`：5 到 15。
- `strategy_consensus`：20 到 80。
- `team_morale`：30 到 90。
- `resource_scarcity`：20 到 80。

如果有 user profile：

- `openness > 70`：提高 `team_morale`。
- `conflict_style == "avoid"`：提高 `strategy_consensus`。
- `closest_ally` 存在：提高 `team_morale`。

然后为每个角色生成：

- `stress_base_offset`：-10 到 10。
- `energy_base_offset`：-10 到 10。

最后按 `seed_id` 为每个内容分类选 id。

### 偏差与缺口

1. `_select_pool_ids()` 计算了 `filtered = filter_by_conditions(...)`，但随后调用 `pool_select(category, [], count, seed_id)`，没有把 `filtered` 真正用于选择。也就是说条件过滤目前没有实际生效。
2. `seed_id` 每次由 UTC 日期 + 随机 4 位 hex 生成，不是根据 `user_id` 确定性生成。因此同一个用户每次调用都会得到不同 seed。
3. `incident_pool_ids`、`meeting_topic_ids`、`pantry_topic_ids`、`report_template_ids` 没有写入 runtime state，也没有被事件/会议/茶水间/报告引擎消费。
4. `_load_user_profile()` 捕获所有异常并返回 None，避免崩溃，但也会吞掉真实数据库错误。

## API 与前后端契约

### 原文档目标

`frontend-backend-contract.md` 要求后端保持 HTTP API 稳定：

- Cookie 鉴权：`newbear_session`
- 大多数操作返回完整 `state`
- 前端以服务端 state 为权威
- 不随意删除或改名 state 字段

### 实际改动

`backend/server.py` 已实现主要 API：

- `GET /api/auth/me`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/state`
- `POST /api/reset`
- `POST /api/step`
- `POST /api/meeting/enter`
- `POST /api/meeting/start`
- `POST /api/meeting/say`
- `POST /api/meeting/tick`
- `POST /api/meeting/finish`
- `POST /api/meeting/close`
- `POST /api/pantry/say`
- `POST /api/pantry/tick`
- `POST /api/pantry/leave`
- `POST /api/report/close`

`serialize_world_state()` 输出完整前端 state，包括：

- `company`
- `actors`
- `user_inputs`
- `map`
- `encounters`
- `pending_incident`
- `incidents`
- `active_meeting`
- `meetings`
- `active_pantry`
- `active_report`
- `onboarding`

### 怎么改的

服务端采用内存字典：

```text
WORLDS: dict[session_id, WorldRuntimeState]
```

每个请求按 cookie session 查到用户，再取或建对应世界。状态保存到 SQLite 的 `sessions.current_state_json`。

世界推进、会议、茶水间、报告等操作都在修改同一个 `WorldRuntimeState`，然后序列化成完整 state 返回前端。

### 偏差与缺口

1. `get_or_create_world(session_id)` 只接收 session_id，不接收 user_id，因此无法基于用户画像生成参数化世界。
2. `POST /api/reset` 调用 `create_initial_world_state()`，也没有重新生成 seed。
3. `serialize_onboarding()` 内部调用 `load_world_seed()`，所以 onboarding 永远是固定公司和固定角色介绍，不会体现参数化公司画像。
4. `server.py` 没有导入或调用 `user_profile.py`、`session_store.py`。
5. P0-001 文档中的历史 session API 没有实现。
6. `sessions.current_state_json` 只是保存 JSON，服务端启动后没有从数据库恢复 `WORLDS` 内存状态；重启后仍会重新创建世界。

## 当前测试覆盖

### 已有测试

- `backend/test_database.py`
  - 覆盖 user_profiles 和 session_records 的基础 CRUD。
  - 覆盖 JSON 字段解析和 merge。
  - 覆盖 session complete/abandon。
- `backend/test_seed_loader.py`
  - 运行一轮世界创建和 step 推进，打印状态。
- `backend/test_be006.py`
  - 覆盖 BE-006 的局部函数行为。

### 测试覆盖不足

缺少 API 级测试：

- 注册用户后是否初始化 user_profile。
- 登录/注册后是否创建 session_record。
- reset 是否生成新 seed。
- state 是否包含 seed 元信息。
- `/api/report/close` 是否 complete session。
- 内容池 id 是否真的影响 incident/meeting/pantry/report。

缺少确定性测试：

- 给定固定 seed_id 时，内容池选择是否稳定。
- 条件过滤是否真的生效。

缺少兼容性测试：

- 旧 state 字段是否保持不变。
- 前端契约中列出的接口是否都返回完整 state。

## 与原文档相比的完成矩阵

| 模块 | 原文档目标 | 当前状态 | 结论 |
|------|------------|----------|------|
| P0-001 数据库表 | 新增 user_profiles / session_records | 已新增 | 基础完成 |
| P0-001 CRUD | user_profile / session_store | 已实现 | 基础完成 |
| P0-001 主流程接入 | 注册、报告、历史页接入 | 未接入 | 缺主链路 |
| P0-002 SessionSeed | 定义 dataclass | 已实现 | 完成 |
| P0-002 兼容签名 | load_world_seed / create_initial_world_state 可选参数 | 已实现 | 完成 |
| BE-005 公司画像参数化 | 参数映射到文案 | 部分实现 | 中间档文案有偏差 |
| BE-006 seed_loader | user_id 路径接 seed_generator | 已实现 | 局部完成 |
| BE-006 world_factory | seed 改 cash/stress/energy | 已实现 | 局部完成 |
| BE-006 主流程接入 | 用户真实开局由 seed 驱动 | 未实现 | 关键缺口 |
| 内容池 | seed 选择内容池 id | 已生成 id | 未消费 |
| 前后端契约 | API 返回完整 state | 大体保持 | seed/history 字段缺失 |

## 建议的后续改造顺序

### 1. 先统一“本局 seed 的来源”

建议新增一个明确的创建流程：

```text
create_seed_for_user(user_id)
  -> seed_generator.generate(user_id)
  -> seed_summary
  -> session_store.create_session_record(...)
  -> create_initial_world_state(seed)
```

不要让 `load_world_seed(user_id)` 和 `create_initial_world_state(seed)` 各自生成/消费不同 seed。

### 2. 让服务端入口传 user_id

将：

```python
get_or_create_world(session_id)
```

调整为类似：

```python
get_or_create_world(user)
```

内部可以使用：

- `user.user_id`
- `user.session_id`

这样注册、登录、获取状态、重置世界都能接入同一套 seed 创建逻辑。

### 3. 扩展 WorldRuntimeState

建议给 `WorldRuntimeState` 增加：

- `seed_id`
- `seed_summary`
- `incident_pool_ids`
- `meeting_topic_ids`
- `pantry_topic_ids`
- `report_template_ids`

并在 `serialize_world_state()` 输出这些字段。

### 4. 修复内容池过滤

`seed_generator._select_pool_ids()` 应该真正从 `filtered` 中选择，而不是过滤后又丢掉。

可以改成：

```text
filtered -> deterministic shuffle -> take count
```

或者扩展 `select_items()` 支持直接传入候选列表。

### 5. 让事件系统消费 seed pool ids

后续需要改：

- `incident_engine.py`
- `meeting_engine.py`
- `pantry_engine.py`
- `report_engine.py`

让它们优先从 `world` 中保存的本局 pool ids 选择内容。

### 6. 接上 session_records 生命周期

建议：

- 注册/登录/新开局：创建 active session_record。
- reset：abandon 旧记录，创建新记录。
- 报告完成/关闭：complete session_record。
- 历史页：实现 `GET /api/sessions`。

### 7. 把脚本测试升级为 API/集成测试

最少补：

- 注册后 profile 被初始化。
- 注册后 state 有 seed_id。
- reset 后 seed_id 变化。
- 同一 session 多次 `/api/state` seed_id 不变。
- 报告关闭后 session_records 状态变 completed。
- 内容池 id 确实驱动事件选择。

## 一句话复盘

后端已经从“固定世界”向“参数化世界”迈出了第一步：数据库、shared 契约、公司画像、种子生成器、初始 cash/stress/energy modifier 都搭起来了。但这些能力多数还停留在模块内部，真实 API 主流程仍然没有把用户画像、SessionSeed、WorldRuntimeState、内容池和历史记录串成闭环。下一阶段的重点不是继续堆新字段，而是把这条链路打通并用 API 集成测试锁住。
