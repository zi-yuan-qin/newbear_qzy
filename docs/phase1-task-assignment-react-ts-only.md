# newbear Phase 1 任务分配文档：参数化种子系统 + 前端重构

## 1. 项目定位

| Item | Value |
| --- | --- |
| 项目名称 | newbear（熊心壮职） |
| 当前阶段 | v0.1 原型 |
| 目标版本/里程碑 | v0.2 — 参数化种子系统，实现可复玩 |
| 目标用户 | 同一用户可反复游玩，每局体验不同 |
| 成功标准 | 同一用户连续玩 3 局，每局公司初始状态、触发事件、NPC 对话主题存在可感知差异 |

## 2. 当前状态总结

| 领域 | 当前状态 | 差距 | 确认人 |
| --- | --- | --- | --- |
| 代码仓库 | https://github.com/funqueen775/newbear | — | 方坤 |
| 数据库 | SQLite，仅 `world_state` + `users` 表 | 缺 `user_profiles` / `session_records` 表 | 秦梓源 |
| 后端核心 | HTTP server + 14 个 world 模块 | 所有配置写死，无法参数化 | 秦梓源 / 孙迦勒 |
| 后端人格报告 | 报告生成有，但无跨 session 聚合分析 | 无用户画像、无趋势数据 | 陈鸿淼 |
| 前端 | `frontend/app` 已有 React + TypeScript + Vite 工程，`frontend/web` 有旧版原生 JS 实现可供参考 | React 版尚未承接完整游戏流程、历史页和复玩入口 | 方坤 |
| 测试 | 仅有 `test_seed_loader.py` | 核心链路无自动化覆盖 | 孙迦勒 |
| 文档 | 产品说明书 + 公司背景参数化设计文档 + Phase1 设计文档 | — | 秦梓源 |

## 3. 范围与非范围

### 本期范围

- 数据库扩展：新建 `user_profiles` + `session_records` 表，提供 CRUD 封装
- 种子参数化引擎：每局生成不同的公司/角色/事件初始参数
- 内容池系统：事件/会议/茶水间/报告从固定剧本改为多条目池
- 配置层重写：`company_profile` / `incidents` / `meeting` / `pantry` / `report` 参数化
- 跨 session 用户画像存储：存储每局人格数据，影响下局种子
- 人格画像分析引擎：多 session 人格聚合、趋势计算、报告增强
- 新 API 路由：sessions 历史、replay、profile、trend
- 前端历史页 + 复玩流程：React + TS 前端完成 session 历史展示、再来一局、进度感知

### 不在本期范围（P2 / Phase 2）

| 项目 | 原因 |
| --- | --- |
| 角色扩展（产品经理→运营专员→...） | Phase 2 |
| NPC 化机制（前轮用户角色变智能体） | Phase 2 |
| 公司团队规模动态增长 | Phase 2 |
| 移动端适配 | 等核心链路稳定 |
| Qdrant 向量记忆 | 过度设计，SQLite 够用 |
| SSE 推送 | 当前 hashchange+fetch 够用 |

## 4. 旧代码处置

| 处置 | 文件/目录 | 原因 |
| --- | --- | --- |
| 保留 | `backend/server.py` | 仅增量添加 6 个路由，不重写 |
| 保留 | `backend/src/core/world/step_engine.py` | 时间步核心不变 |
| 保留 | `backend/src/core/world/actor_reactions.py` | LLM 调用逻辑不变 |
| 保留 | `backend/src/core/world/meeting_engine.py` | 会议状态机不变 |
| 保留 | `backend/src/core/world/pantry_engine.py` | 茶水间状态机不变 |
| 保留 | `backend/src/core/world/report_engine.py` | 报告触发不变 |
| 保留 | `backend/src/core/world/incident_engine.py` | 事件触发时间点不变 |
| 保留 | `backend/src/core/world/dialogue_engine.py` | 对话生成不变 |
| 保留 | `backend/src/core/world/encounter_engine.py` | 相遇检测不变 |
| 保留 | `backend/src/core/world/memory_engine.py` | 记忆系统不变 |
| 保留 | `backend/src/core/world/memory_retriever.py` | 记忆检索不变 |
| 保留 | `backend/src/core/world/reflection_engine.py` | 反思调度不变 |
| 保留 | `backend/src/core/world/prompt_context.py` | prompt 上下文不变 |
| 保留 | `backend/src/core/world/meeting_discussion_engine.py` | 会议讨论不变 |
| 保留 | `backend/src/core/world/pantry_discussion_engine.py` | 茶水间讨论不变 |
| 保留 | `backend/src/core/world/runtime_state.py` | 数据类不变 |
| 保留 | `backend/src/core/llm/ark_client.py` | LLM 客户端不变 |
| 保留 | `backend/src/core/map/*` | 地图加载不变 |
| 保留 | `backend/src/core/auth/*` | 认证不变 |
| 保留 | `backend/src/core/config/character_profiles.py` | 基础角色设定保留，仅 world_factory 应用 modifier |
| 保留 | `backend/src/core/config/job_profiles.py` | 岗位设定保留 |
| 保留 | `frontend/web/assets/*` | 美术资产保留，供 React 前端复用 |
| 参考保留 | `frontend/web/main.js` | 旧版原生 JS 流程保留作参考，不再作为本期主开发入口 |
| 参考保留 | `frontend/web/index.html` | 旧版结构保留作参考 |
| 参考保留 | `frontend/web/styles.css` | 旧版样式保留作参考 |
| **重写** | `backend/src/core/config/company_profile.py` | 固定值 → 参数化模板函数（秦梓源） |
| **重写** | `backend/src/core/config/incidents.py` | 固定列表 → 调用 content_pool（孙迦勒） |
| **重写** | `backend/src/core/config/meeting_events.py` | 固定列表 → 调用 content_pool（孙迦勒） |
| **重写** | `backend/src/core/config/pantry_events.py` | 固定列表 → 调用 content_pool（孙迦勒） |
| **重写** | `backend/src/core/config/report_events.py` | 固定列表 → 调用 content_pool（孙迦勒） |
| **重写** | `backend/src/core/world/seed_loader.py` | 读固定文件 → 调用 seed_generator（秦梓源） |
| **重写** | `backend/src/core/world/world_factory.py` | 固定参数 → 接受参数化种子（秦梓源） |
| **重写** | `backend/src/core/db/database.py` | 新增建表（秦梓源） |
| **主力开发** | `frontend/app/src/*` | 本期前端主开发目录，承接 React + TS 版 UI、状态与复玩流程（方坤） |
| **新增** | `backend/src/core/config/seed_generator.py` | 种子生成引擎（孙迦勒） |
| **新增** | `backend/src/core/config/content_pool.py` | 内容池管理器（孙迦勒） |
| **新增** | `backend/src/core/config/content_pool/__init__.py` | —（孙迦勒） |
| **新增** | `backend/src/core/config/content_pool/incidents/*.json` | 事件内容池数据（孙迦勒） |
| **新增** | `backend/src/core/config/content_pool/meetings/*.json` | 会议内容池数据（孙迦勒） |
| **新增** | `backend/src/core/config/content_pool/pantry/*.json` | 茶水间内容池数据（孙迦勒） |
| **新增** | `backend/src/core/config/content_pool/reports/*.json` | 报告内容池数据（孙迦勒） |
| **新增** | `backend/src/core/db/user_profile.py` | 用户画像 DB 操作（秦梓源） |
| **新增** | `backend/src/core/db/session_store.py` | 会话记录 DB 操作（秦梓源） |
| **新增** | `backend/src/core/world/personality_analyzer.py` | 人格分析引擎（陈鸿淼） |
| **新增** | `backend/test_seed_generator.py` | 种子生成器测试（孙迦勒） |
| **新增** | `backend/test_content_pool.py` | 内容池测试（孙迦勒） |
| **新增** | `backend/test_personality_analyzer.py` | 人格分析测试（陈鸿淼） |

## 5. 数据库变更

### 表变更总览

| 表 | 操作 | 备注 |
| --- | --- | --- |
| `user_profiles` | 新建 | 跨 session 用户人格画像 |
| `session_records` | 新建 | 单局 session 元数据 |
| `world_state` | 修改 | 新增 `seed_id` 字段 |
| `users` | 保留 | 不变 |
| `user_messages` | 保留 | 不变 |
| `reports` | 保留 | 不变 |

### 建表 SQL（秦梓源 负责）

```sql
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY,
    personality_data TEXT NOT NULL DEFAULT '{}',
    total_sessions INTEGER NOT NULL DEFAULT 0,
    total_playtime_seconds INTEGER NOT NULL DEFAULT 0,
    preferred_decision_style TEXT,
    preferred_conflict_style TEXT,
    avg_input_length REAL,
    relationship_scores TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS session_records (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    seed_id TEXT NOT NULL,
    seed_summary TEXT NOT NULL DEFAULT '{}',
    day_completed INTEGER NOT NULL DEFAULT 0,
    final_clock TEXT,
    report_id TEXT,
    report_scores TEXT NOT NULL DEFAULT '{}',
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

ALTER TABLE world_state ADD COLUMN seed_id TEXT;
```

## 6. 团队分工总览

| 成员 | 角色 | 技术栈 | 主要职责 | 最终产出 |
| --- | --- | --- | --- | --- |
| 方坤（队长+前端） | 前端 + 验收 | React / TypeScript / Vite / Zustand | React 前端历史页、复玩流程、旧前端资源迁移、全链路联调验收 | React 前端 UI 完成、3 局差异验证通过 |
| 秦梓源 | 后端 | Python | DB 扩展、接口契约、company_profile 参数化、seed_loader/world_factory 重写、API 路由集成 | 数据库就绪、API 全链路打通 |
| 孙迦勒 | 后端 | Python | 种子生成器、内容池及数据、config 层重写(incidents/meetings/pantry/report)、测试 | 种子引擎 + 内容池 + 单元测试 |
| 陈鸿淼 | 后端-人格报告 | Python | 人格分析引擎、profile/trend API 数据层、报告增强 | 人格画像分析模块 + 跨 session 趋势 |

### 模块分工

| 模块 | 目的 | 独立性 | 负责人 |
| --- | --- | --- | --- |
| 数据库扩展 | user_profiles + session_records 表，建表 + CRUD 封装 | 独立，前置依赖 | 秦梓源 |
| 种子参数化引擎 | 每局生成不同的公司/角色/事件初始参数 | 独立模块 | 孙迦勒 |
| 内容池系统 | 事件/会议/茶水间/报告从固定剧本 → 多条目池 | 独立模块 | 孙迦勒 |
| 配置层重写 | company_profile / incidents / meeting / pantry / report 重写 | 依赖种子引擎和内容池接口 | 秦梓源 / 孙迦勒 |
| 跨 session 用户画像存储 | 存储每局人格数据，影响下局种子 | 依赖 DB 扩展 | 秦梓源 |
| 人格画像分析引擎 | 多 session 人格聚合、趋势计算、报告增强 | 独立模块 | 陈鸿淼 |
| 新 API 路由 | sessions 历史、replay、profile、trend | 依赖种子引擎 + 画像引擎 | 秦梓源 |
| 前端历史页 + 复玩流程 | 在 React + TS 前端中完成 session 历史展示、再来一局、进度感知 | 依赖新 API | 方坤 |

### 时间线

| 阶段 | 周次 | 负责人 | 任务 |
| --- | --- | --- | --- |
| Phase 1a: 后端前置 | Week 1 前半 | 秦梓源 | P0-001, P0-002 |
| Phase 1b: 后端并行 | Week 1 后半 ~ Week 2 | 秦梓源, 孙迦勒, 陈鸿淼 | BE-001 ~ BE-009 |
| Phase 1c: 前端 | Week 3 前半 | 方坤 | FE-001, FE-002, FE-003 |
| Phase 1d: 联调验收 | Week 3 后半 | 方坤 + 秦梓源 | INT-001, QA-001 |

## 7. 依赖地图

### Week 1

```
P0-001 [A] 数据库建表 + CRUD 封装
│
├──▶ P0-002 [A] Shared 层接口定义（seed dataclass, content_pool 协议）
│         │
│         ├──▶ BE-001 [C] 种子生成器
│         ├──▶ BE-002 [C] 内容池管理器
│         ├──▶ BE-003 [C] 内容池数据编写
│         └──▶ BE-005 [A] company_profile 参数化模板
│
└──▶ BE-007 [D] 人格分析引擎（需 user_profile CRUD 就绪）
```

### Week 2

```
BE-001 [C] + BE-002 [C] + BE-003 [C] 完成
│
└──▶ BE-004 [C] config 层重写（incidents/meetings/pantry/report）

BE-005 [A] 完成 → BE-006 [A] seed_loader + world_factory 重写
BE-007 [D] 完成 → BE-008 [D] profile/trend API 数据层
后端模块齐备 → BE-009 [A] server.py 新增 6 个 API 路由
```

### Week 3

```
BE-009 [A] API 就绪 → FE-001 [方坤] 前端历史页
BE-009 [A] API 就绪 → FE-002 [方坤] 前端复玩流程
FE-001 + FE-002 → FE-003 [方坤] 报告页底部复玩入口

全部模块就绪 → INT-001 [方坤+A] 全链路联调
                         └──▶ QA-001 [方坤] 3 局差异验收
```

## 8. 时间估算

各任务的时间估算已标注在下方任务卡片中，总览见 [第 6 节 - 时间线](#6-团队分工总览)。

## 9. 后端前置任务（A）

### P0-001: 数据库扩展

**目标**: 新建 `user_profiles` 和 `session_records` 表，提供 CRUD 封装
**负责人**: 秦梓源
**状态**: Not Started
**前置依赖**: 无
**时间**: Week 1 前半

**允许编辑路径**:
- `backend/src/core/db/database.py`
- `backend/src/core/db/user_profile.py`（新增）
- `backend/src/core/db/session_store.py`（新增）

**API/数据契约**:

`user_profile.py` 对外暴露：
```python
def init_user_profile(user_id: str) -> dict
def get_user_profile(user_id: str) -> dict | None
def update_user_profile(user_id: str, personality_data: dict) -> dict
def increment_session_count(user_id: str) -> int
```

`session_store.py` 对外暴露：
```python
def create_session_record(user_id: str, seed_id: str, seed_summary: dict) -> str
def get_session_record(session_id: str) -> dict | None
def list_user_sessions(user_id: str, limit: int = 20) -> list[dict]
def complete_session(session_id: str, report_id: str, scores: dict) -> None
def abandon_session(session_id: str) -> None
```

**验收标准**:
- [ ] `init_db()` 执行后两张新表自动创建
- [ ] user_profile CRUD 四个函数均可调用，返回预期结构
- [ ] session_store 六个函数均可调用，返回预期结构
- [ ] 现有 `world_state` / `users` 表不受影响

**必需测试**:
- [ ] 新建用户 → `init_user_profile` → `get_user_profile` 返回非空
- [ ] `update_user_profile` 写入人格数据 → 再次读取验证字段一致
- [ ] `create_session_record` → `complete_session` → status 变为 completed
- [ ] `list_user_sessions` 按时间倒序返回，limit 生效
- [ ] 同一 user 创建 3 个 session → `increment_session_count` → `total_sessions=3`

**队长验收**: 需要方坤验收
**交付物**: `user_profile.py`, `session_store.py`, 修改后的 `database.py`
**移交备注**: C、D 可以通过 import 直接使用，D 的 BE-007 依赖 P0-001 完成

---

### P0-002: Shared 层接口定义

**目标**: 定义种子数据结构、内容池协议、参数化模板接口，作为 A/C/D 三方并行开发的契约
**负责人**: 秦梓源
**状态**: Not Started
**前置依赖**: 无（可与 P0-001 并行）
**时间**: Week 1 前半

**允许编辑路径**:
- `backend/src/core/world/seed_loader.py`

**API/数据契约**:

在 `seed_loader.py` 中定义 `SessionSeed` dataclass：
```python
@dataclass
class SessionSeed:
    seed_id: str
    company_params: dict
    character_modifiers: dict[str, dict]
    incident_pool_ids: list[str]
    meeting_topic_ids: list[str]
    pantry_topic_ids: list[str]
    report_template_ids: list[str]
```

定义接口签名（具体实现在后续任务）：
```python
def load_world_seed(user_id: str | None = None) -> dict
def build_company_profile(params: dict) -> dict
def create_initial_world_state(seed: SessionSeed | None = None) -> WorldRuntimeState
```

**验收标准**:
- [ ] `SessionSeed` dataclass 定义完成，A/C/D 可 import
- [ ] 接口签名清晰，输入输出类型明确
- [ ] 现有 `python backend/server.py` 仍可启动

**必需测试**:
- [ ] `from src.core.world.seed_loader import SessionSeed` 可正常 import
- [ ] `SessionSeed(...)` 可正常实例化

**队长验收**: 需要方坤验收
**交付物**: 修改后的 `seed_loader.py`（仅 dataclass + 接口签名）
**移交备注**: 孙迦勒依赖 SessionSeed 写 seed_generator，秦梓源自己后续在 BE-005/006 中实现

---

## 10. 并行成员任务

### 秦梓源（后端）—— 参数化配置层 + 世界工厂 + API 集成

#### BE-005: company_profile 参数化模板

**目标**: 将固定 `COMPANY_PROFILE` dict 改为参数化函数
**负责人**: 秦梓源
**状态**: Not Started
**前置依赖**: P0-002（SessionSeed dataclass + `build_company_profile` 接口签名就绪）
**时间**: Week 1 后半

**允许编辑路径**:
- `backend/src/core/config/company_profile.py`

**API/数据契约**:
```python
def build_company_profile(params: dict) -> dict
```

**参数化规则**:

| 参数 | 效果 |
| --- | --- |
| `cash` / `runway_days` | 现金流天数描述文案 |
| `strategy_consensus` | "团队方向一致/存在分歧" 文案 |
| `team_morale` | "士气不错/有些低落" 文案 |
| `resource_scarcity` | 资源紧张度描述 |

无参数时 fallback 默认值（与当前版本一致）。

**验收标准**:
- [ ] 不同参数生成的公司描述文案有明显差异
- [ ] 关键数字和状态词随参数变化
- [ ] 无参数时与当前版本默认描述一致

---

#### BE-006: seed_loader + world_factory 重写

**目标**: 实现 `load_world_seed` 和 `create_initial_world_state` 的完整逻辑
**负责人**: 秦梓源
**状态**: Not Started
**前置依赖**: BE-005, BE-001
**时间**: Week 2 前半

**允许编辑路径**:
- `backend/src/core/world/seed_loader.py`
- `backend/src/core/world/world_factory.py`

**验收标准**:
- [ ] `load_world_seed(user_id)` 返回完整的 seed dict
- [ ] `create_initial_world_state(seed)` 角色初始属性反映 modifier
- [ ] 公司初始状态反映 `company_params`
- [ ] 向后兼容：不传 seed 时行为与当前版本一致
- [ ] 现有 `python backend/server.py` 可启动运行

---

#### BE-009: server.py 新增 API 路由

**目标**: 在 `server.py` 中新增 6 个 API 路由，集成种子引擎、画像引擎
**负责人**: 秦梓源
**状态**: Not Started
**前置依赖**: BE-001~BE-008 全部完成
**时间**: Week 2 后半

**允许编辑路径**:
- `backend/server.py`

**新增路由**:
| Method | Path | 处理逻辑 |
| --- | --- | --- |
| GET | `/api/sessions` | `session_store.list_user_sessions` |
| GET | `/api/sessions/<id>` | `session_store.get_session_record` |
| POST | `/api/sessions/replay` | `seed_generator.generate` → `world_factory.create` → 返回新 state |
| GET | `/api/profile` | `personality_analyzer.get_profile_response` |
| GET | `/api/profile/trend` | `personality_analyzer.get_trend_response` |
| POST | `/api/seed/preview` | `seed_generator.preview`（调试用） |

**现有路由修改**:
- `POST /api/reset` → 改用 `load_world_seed(user.user_id)`
- `POST /api/report/close` → 增加 user_profile 更新 + session_record 写入

**验收标准**:
- [ ] 6 个新路由正常响应
- [ ] `POST /api/sessions/replay` 返回完整 state
- [ ] `POST /api/reset` 每次生成不同初始状态
- [ ] `POST /api/report/close` 正确写入 user_profile 和 session_record
- [ ] 所有路由未登录时返回 401

**前后端集成检查**: 前端方坤依赖这些 API（FE-001/002/003 的前置条件）

---

### 孙迦勒（后端）—— 种子引擎 + 内容池

#### BE-001: 种子生成器

**目标**: 实现 `SessionSeed` 生成逻辑——随机采样参数、内容池选择、用户画像加权
**负责人**: 孙迦勒
**状态**: Not Started
**前置依赖**: P0-002
**时间**: Week 1 后半 ~ Week 2 前半

**允许编辑路径**:
- `backend/src/core/config/seed_generator.py`（新增）

**API/数据契约**:
```python
def generate(user_id: str | None = None) -> SessionSeed
def preview(user_id: str | None = None) -> dict
```

**参数采样范围**:

| 参数 | 范围 |
| --- | --- |
| `cash` | [2000, 8000]，步长 500 |
| `runway_days` | [5, 15] |
| `strategy_consensus` | [20, 80] |
| `team_morale` | [30, 90] |
| character `stress_base` 偏移 | ±10 |
| character `energy_base` 偏移 | ±10 |

**用户画像加权**（初版）:

| 条件 | 效果 |
| --- | --- |
| `openness` > 70 | 高变体事件权重 +30% |
| `conflict_style` = "avoid" | 团队冲突事件概率 -50% |
| `closest_ally` | 该角色初始好感度 +10 |

**验收标准**:
- [ ] `generate()` 返回完整的 `SessionSeed`，所有字段非空
- [ ] 连续 10 次 generate 至少 8 种不同 seed
- [ ] user_profile 影响种子参数
- [ ] seed_id 格式 `seed-{YYYYMMDD}-{4位随机hex}`

---

#### BE-002: 内容池管理器

**目标**: 实现内容池加载、条件筛选、条目选取
**负责人**: 孙迦勒
**状态**: Not Started
**前置依赖**: P0-002
**时间**: Week 1 后半 ~ Week 2 前半（与 BE-001 并行）

**允许编辑路径**:
- `backend/src/core/config/content_pool.py`（新增）

**API/数据契约**:
```python
def load_pool(category: str) -> list[dict]
def select_items(category: str, pool_ids: list[str], count: int, seed_id: str) -> list[dict]
def filter_by_conditions(items: list[dict], conditions: dict) -> list[dict]
```

**验收标准**:
- [ ] 4 个 category 均可正确加载
- [ ] `select_items` 相同 seed_id 返回相同结果
- [ ] `filter_by_conditions` 正确过滤
- [ ] 空池子返回空列表不报错

---

#### BE-003: 内容池数据编写

**目标**: 为 4 个类别编写至少 6 条变体/类，确保多局体验差异
**负责人**: 孙迦勒
**状态**: Not Started
**前置依赖**: 无（可与 BE-001/BE-002 并行）
**时间**: Week 1 后半 ~ Week 2 前半

**允许编辑路径**:
- `backend/src/core/config/content_pool/`（新增）

**新增文件**:
```
backend/src/core/config/content_pool/__init__.py
backend/src/core/config/content_pool/incidents/market_pressure.json
backend/src/core/config/content_pool/incidents/funding_crisis.json
backend/src/core/config/content_pool/incidents/team_friction.json
backend/src/core/config/content_pool/incidents/user_growth.json
backend/src/core/config/content_pool/incidents/competitor_move.json
backend/src/core/config/content_pool/meetings/morning_standup.json
backend/src/core/config/content_pool/meetings/afternoon_review.json
backend/src/core/config/content_pool/pantry/afterwork_chat.json
backend/src/core/config/content_pool/reports/daily_letter.json
```

**验收标准**:
- [ ] incidents ≥ 8 变体，meetings ≥ 6 变体，pantry ≥ 6 变体，reports ≥ 4 变体
- [ ] 每条填写 `tags` 和 `param_conditions`
- [ ] JSON 格式合法，`content_pool.py` 可加载

---

#### BE-004: config 层重写（incidents / meetings / pantry / report）

**目标**: 将 4 个配置模块从固定列表改为调用 content_pool
**负责人**: 孙迦勒
**状态**: Not Started
**前置依赖**: BE-002, BE-003
**时间**: Week 2 前半

**允许编辑路径**:
- `backend/src/core/config/incidents.py`
- `backend/src/core/config/meeting_events.py`
- `backend/src/core/config/pantry_events.py`
- `backend/src/core/config/report_events.py`

**验收标准**:
- [ ] 函数签名与旧版兼容，现有 engine 调用不报错
- [ ] 不同种子 → 不同事件/会议/茶水间/报告列表

---

### 陈鸿淼（后端-人格报告）—— 画像分析引擎

#### BE-007: 人格分析引擎

**目标**: 实现跨 session 用户人格画像计算——行为数据→人格维度→趋势追踪
**负责人**: 陈鸿淼
**状态**: Not Started
**前置依赖**: P0-001
**时间**: Week 1 后半 ~ Week 2

**允许编辑路径**:
- `backend/src/core/world/personality_analyzer.py`（新增）

**API/数据契约**:
```python
def analyze_session(session_id: str, report: dict, user_inputs: list[dict]) -> SessionBehaviorData
def update_user_profile(user_id: str, behavior: SessionBehaviorData) -> dict
def get_trend(user_id: str) -> dict
```

**验收标准**:
- [ ] `analyze_session` 正确提取所有行为特征
- [ ] `update_user_profile` 首次创建、再次加权更新
- [ ] `get_trend` 返回正确趋势数据
- [ ] 人格维度值 0-100 范围

---

#### BE-008: profile / trend API 数据层

**目标**: 封装 profile 和 trend 响应结构，供秦梓源在 `server.py` 中调用
**负责人**: 陈鸿淼
**状态**: Not Started
**前置依赖**: BE-007
**时间**: Week 2 后半

**允许编辑路径**:
- `backend/src/core/world/personality_analyzer.py`

**API/数据契约**:
```python
def get_profile_response(user_id: str) -> dict
def get_trend_response(user_id: str) -> dict
```

**验收标准**:
- [ ] 返回结构符合前端 FE-001 数据需求
- [ ] 无历史数据时返回合理空结构

---

### 方坤（队长+前端）—— 前端 + 联调验收

#### FE-001: Session 历史页

**目标**: 在 React + TS 前端中新增 `#/history` 路由，展示历次游玩记录 + 人格趋势
**负责人**: 方坤
**状态**: Not Started
**前置依赖**: BE-009
**时间**: Week 3 前半

**允许编辑路径**:
- `frontend/app/src/App.tsx`
- `frontend/app/src/pages/*`
- `frontend/app/src/components/*`
- `frontend/app/src/store/*`
- `frontend/app/src/styles/*`
- `frontend/app/src/types/*`
- `frontend/app/src/api/*`

**UI 设计要点**:
- 页面路由 `#/history`，顶部导航可切换回游戏
- 每局一张卡片：日期、人格标签、关键事件数
- SVG 折线图展示人格维度变化趋势（横轴=session 序号，纵轴=分数）
- 空状态引导文案"还没有职场记录，开始你的第一天吧"

**验收标准**:
- [ ] 从 `#/` 可导航到 `#/history`
- [ ] 历史列表按时间倒序展示
- [ ] 人格趋势折线图正确（至少 openness / extraversion 两条线）
- [ ] 空状态/单局/多局三种展示正确

**必需测试**:
- [ ] 0 条历史 → 空状态引导
- [ ] 1 条历史 → 1 张卡片 + 趋势图提示"需 2 局以上"
- [ ] 3 条历史 → 3 张卡片 + 3 点连线
- [ ] 10+ 条历史 → 展示最近 10 条

**队长验收**: 自验
**交付物**: `frontend/app` 下对应页面、组件、store、样式与类型文件

---

#### FE-002: 复玩流程

**目标**: 在 React + TS 前端中实现"再来一局"完整流程
**负责人**: 方坤
**状态**: Not Started
**前置依赖**: FE-001, BE-009
**时间**: Week 3 前半

**允许编辑路径**: 同 FE-001

**UI 设计要点**:
- 三个触发入口：报告页底部 / 历史页顶部 / 登录后主页
- 点击后展示种子预览提示（1-2 句中文描述）
- 确认后 `POST /api/sessions/replay` → `renderState`

**验收标准**:
- [ ] 三个入口均可触发复玩
- [ ] 种子预览文案与后端一致
- [ ] 新游戏初始状态与上局不同

**必需测试**:
- [ ] 报告页点[再来一局]→新游戏启动
- [ ] 历史页点[开始新的一局]→同上
- [ ] 连续复玩 3 次 → 3 次预览文案各不相同

**队长验收**: 自验
**交付物**: `frontend/app` 下对应页面、组件、store、样式与 API 接线

---

#### FE-003: 报告页底部复玩入口

**目标**: 在 React + TS 报告页底部增加内容进度提示和复玩引导
**负责人**: 方坤
**状态**: Not Started
**前置依赖**: FE-002
**时间**: Week 3 前半（与 FE-002 并行或略后）

**允许编辑路径**:
- `frontend/app/src/pages/*`
- `frontend/app/src/components/*`
- `frontend/app/src/styles/*`
- `frontend/app/src/store/*`

**验收标准**:
- [ ] 事件进度正确展示
- [ ] [再来一局] 按钮可用

**队长验收**: 自验
**交付物**: `frontend/app` 下报告页相关文件

---

## 11. 联调与验收

### INT-001: 全链路联调

**目标**: 端到端验证 注册→游戏→报告→复玩→历史 完整链路
**负责人**: 方坤 + 秦梓源
**状态**: Not Started
**前置依赖**: BE-009, FE-001, FE-002, FE-003 全部完成
**时间**: Week 3 后半

**验收标准**:
- [ ] 完整链路无报错
- [ ] 第二局初始状态与第一局不同
- [ ] 第三局事件与第一局至少 2 条不同
- [ ] `GET /api/profile/trend` 返回 3 个数据点

**必需测试**:
- [ ] 方坤 + 秦梓源一起跑通 3 局完整链路
- [ ] 孙迦勒确认种子参数变化符合预期
- [ ] 陈鸿淼确认人格数据跨 session 正确累积

**队长验收**: 方坤最终签字
**交付物**: 联调通过确认 + bug 列表（如有）

---

### QA-001: 3 局差异验收

**目标**: 定量验证 3 局体验存在可感知差异
**负责人**: 方坤
**状态**: Not Started
**前置依赖**: INT-001
**时间**: Week 3 后半

**验收标准**（必须全部通过）:
- [ ] 3 局的 `company_params.cash` 不全相同
- [ ] 3 局的 `company_params.runway_days` 不全相同
- [ ] 3 局的 incident 至少 1/3 不同
- [ ] 3 局的 meeting 主题至少 1/3 不同
- [ ] 3 局的 pantry 主题至少 1/3 不同
- [ ] 3 局的 `seed_summary` 文案各不相同
- [ ] 用户人格趋势至少 1 个维度变化 > 5 分

**队长验收**: 方坤最终签字
**交付物**: 验收报告 + 差异对比截图

## 12. API 端点总览

### 新增路由

| Method | Path | 处理逻辑 |
| --- | --- | --- |
| GET | `/api/sessions` | `session_store.list_user_sessions` |
| GET | `/api/sessions/<id>` | `session_store.get_session_record` |
| POST | `/api/sessions/replay` | `seed_generator.generate` → `world_factory.create` → 返回新 state |
| GET | `/api/profile` | `personality_analyzer.get_profile_response` |
| GET | `/api/profile/trend` | `personality_analyzer.get_trend_response` |
| POST | `/api/seed/preview` | `seed_generator.preview`（调试用） |

### 全量路由

| 模块 | Method | Path | 负责人 | 新增/修改 |
| --- | --- | --- | --- | --- |
| Auth | POST | `/api/auth/register` | 秦梓源 | 修改（新增 user_profile 初始化） |
| Auth | POST | `/api/auth/login` | 秦梓源 | 保留 |
| Auth | POST | `/api/auth/logout` | 秦梓源 | 保留 |
| Auth | GET | `/api/auth/me` | 秦梓源 | 保留 |
| State | GET | `/api/state` | 秦梓源 | 修改（响应新增 seed_id） |
| World | POST | `/api/step` | 秦梓源 | 保留 |
| World | POST | `/api/reset` | 秦梓源 | 修改（使用新种子） |
| Meeting | POST | `/api/meeting/*` | 秦梓源 | 保留 |
| Pantry | POST | `/api/pantry/*` | 秦梓源 | 保留 |
| Report | POST | `/api/report/close` | 秦梓源 | 修改（写入 user_profile + session_record） |
| Session | GET | `/api/sessions` | 秦梓源 | **新增** |
| Session | GET | `/api/sessions/{id}` | 秦梓源 | **新增** |
| Session | POST | `/api/sessions/replay` | 秦梓源 | **新增** |
| Profile | GET | `/api/profile` | 秦梓源（调用陈鸿淼） | **新增** |
| Profile | GET | `/api/profile/trend` | 秦梓源（调用陈鸿淼） | **新增** |
| Debug | POST | `/api/seed/preview` | 秦梓源（调用孙迦勒） | **新增** |

## 13. 测试与验收计划

| 层级 | 负责人 | 测试场景数 | 命令 | 通过标准 |
| --- | --- | --- | --- | --- |
| 单元测试-种子引擎 | 孙迦勒 | 5 | `python backend/test_seed_generator.py` | 全部通过 |
| 单元测试-内容池 | 孙迦勒 | 5 | `python backend/test_content_pool.py` | 全部通过 |
| 单元测试-人格分析 | 陈鸿淼 | 5 | `python backend/test_personality_analyzer.py` | 全部通过 |
| 单元测试-DB 层 | 秦梓源 | 5 | 集成在 P0-001 | 全部通过 |
| 集成测试 | 秦梓源 | 4 | `python backend/test_seed_loader.py`（重写） | 全部通过 |
| 前端验收 | 方坤 | 见 FE-001/002/003 | `cd frontend/app && npm run build`、`npm run lint`、浏览器手动验证 | 无 TS/JS 报错、UI 正确 |
| 最终验收 | 方坤 | 7 | 手动全链路 + 3 局差异 | 全部通过 |

## 14. 进度管理

### 状态词汇

| 状态 | 含义 |
| --- | --- |
| Not Started | 未开始 |
| In Progress | 进行中 |
| Blocked | 阻塞 |
| Done | 完成 |

### 阻塞定义

任务在以下情况标记 **Blocked**：
- 前置任务未完成
- 外部依赖（API/人/决策）超过 24 小时不可用

阻塞时负责人必须立即通知方坤：阻塞原因、需要什么来解除、可以并行做什么。

### 每日更新格式

```
- 昨日完成：
- 今日计划：
- 阻塞项（如有）：
- 分支/PR 链接：
- 测试结果：
```

### 完成定义

1. 代码完成
2. 测试通过
3. 文档/移交备注已更新
4. 审查者无需猜测即可验证

## 15. PR 与合入规则

- **分支命名**: `feature/{task-id}-{简短描述}`
- **PR 标题**: 包含任务 ID 和模块名
- **PR 描述**: 列出变更范围、测试结果、截图（如有 UI 变更）
- **不得编辑其他成员的所属路径**
- **共享文件**（`server.py`, `database.py`, `runtime_state.py`）只有方坤有编辑权限
- 前端相关改动以 `frontend/app` 为主，`frontend/web` 不再承载本期新增功能
- **合入顺序**遵循依赖地图：P0 → BE → FE → INT → QA
