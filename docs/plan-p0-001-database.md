# P0-001 数据库扩展 — 规划文档

## 模块概述

在现有 SQLite 数据库（`backend/data/newbear.db`）中新增 `user_profiles` 和 `session_records` 两张表，提供 CRUD 封装函数，为跨 session 用户画像存储、种子参数化和前端历史页打基础。

## 架构设计

### 数据流

```
server.py (秦梓源 BE-009)
  │
  ├── POST /api/auth/register  →  user_profile.init_user_profile(user_id)
  ├── POST /api/report/close    →  user_profile.update_user_profile(user_id, data)
  │                              →  session_store.complete_session(session_id, ...)
  ├── GET  /api/sessions        →  session_store.list_user_sessions(user_id)
  ├── GET  /api/sessions/<id>   →  session_store.get_session_record(session_id)
  ├── POST /api/sessions/replay →  读 session_store + 创建新 session
  │
  └── BE-007 人格引擎(陈鸿淼)   →  user_profile.get_user_profile(user_id)
                                 →  user_profile.update_user_profile(user_id, data)
```

### 模块划分

| 文件 | 职责 | 操作类型 |
|------|------|----------|
| `database.py` | `init_db()` 加建表 SQL、`get_connection()` 不变 | 修改 |
| `user_profile.py` | user_profiles 表 CRUD（4 个函数） | **新增** |
| `session_store.py` | session_records 表 CRUD（6 个函数） | **新增** |

## 文件清单

### 1. 修改：`backend/src/core/db/database.py`

在 `init_db()` 末尾新增两段 `CREATE TABLE IF NOT EXISTS`：

```sql
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INTEGER PRIMARY KEY,
    personality_data TEXT NOT NULL DEFAULT '{}',
    total_sessions INTEGER NOT NULL DEFAULT 0,
    total_playtime_seconds INTEGER NOT NULL DEFAULT 0,
    preferred_decision_style TEXT,
    preferred_conflict_style TEXT,
    avg_input_length REAL,
    relationship_scores TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS session_records (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    seed_id TEXT NOT NULL,
    seed_summary TEXT NOT NULL DEFAULT '{}',
    day_completed INTEGER NOT NULL DEFAULT 0,
    final_clock TEXT,
    report_id TEXT,
    report_scores TEXT NOT NULL DEFAULT '{}',
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

（注意：不包含 `ALTER TABLE world_state ADD seed_id` — world_state 表当前不在 database.py 里定义，而是存为 JSON blob，lives in `sessions.current_state_json` 列，所以 seed_id 加在 state JSON 里由序列化层处理即可，无需 DDL。）

### 2. 新增：`backend/src/core/db/user_profile.py`

```python
from src.core.db.database import get_connection

def init_user_profile(user_id: int) -> dict
def get_user_profile(user_id: int) -> dict | None
def update_user_profile(user_id: int, personality_data: dict) -> dict
def increment_session_count(user_id: int) -> int
```

**实现要点**：
- `init_user_profile`: INSERT OR IGNORE → SELECT 返回
- `get_user_profile`: SELECT，解析 JSON 字段后返回
- `update_user_profile`: UPDATE，同时更新 `updated_at`
- `increment_session_count`: UPDATE total_sessions = total_sessions + 1，返回新值

### 3. 新增：`backend/src/core/db/session_store.py`

```python
import uuid
from src.core.db.database import get_connection

def create_session_record(user_id: int, seed_id: str, seed_summary: dict) -> str
def get_session_record(session_id: str) -> dict | None
def list_user_sessions(user_id: int, limit: int = 20) -> list[dict]
def complete_session(session_id: str, report_id: str, scores: dict) -> None
def abandon_session(session_id: str) -> None
```

**实现要点**：
- `create_session_record`: 生成 `uuid.uuid4().hex` 作为 session_id，INSERT → 返回 session_id
- `get_session_record`: SELECT，解析 JSON 字段后返回
- `list_user_sessions`: SELECT WHERE user_id ORDER BY started_at DESC LIMIT
- `complete_session`: UPDATE status='completed', ended_at, report_id, report_scores
- `abandon_session`: UPDATE status='abandoned', ended_at

### 4. 新增：`backend/test_database.py`

按文档 5 条必需测试编写：

| # | 测试场景 | 预期 |
|---|---------|------|
| 1 | 新建用户 → init → get | 返回非空 |
| 2 | update 写入人格数据 → 再读取 | 字段一致 |
| 3 | create → complete → 查 status | completed |
| 4 | list_user_sessions 时间倒序 + limit | 返回正确 |
| 5 | 同一 user 创建 3 session → increment ×3 | total_sessions=3 |

## 接口定义

### user_profile.py

```python
def init_user_profile(user_id: int) -> dict
    """为新用户创建 profile 记录，幂等。返回完整 profile dict。"""

def get_user_profile(user_id: int) -> dict | None
    """获取用户画像，不存在返回 None。"""

def update_user_profile(user_id: int, personality_data: dict) -> dict
    """合并更新人格数据（JSON merge），返回更新后的完整 profile。"""

def increment_session_count(user_id: int) -> int
    """会话计数 +1，返回新的 total_sessions 值。"""
```

### session_store.py

```python
def create_session_record(user_id: int, seed_id: str, seed_summary: dict) -> str
    """创建新 session 记录，返回 session_id。"""

def get_session_record(session_id: str) -> dict | None
    """获取单条 session 记录，不存在返回 None。"""

def list_user_sessions(user_id: int, limit: int = 20) -> list[dict]
    """按 started_at 倒序返回该用户的 session 列表。"""

def complete_session(session_id: str, report_id: str, scores: dict) -> None
    """标记 session 为 completed，写入报告 ID 和分数。"""

def abandon_session(session_id: str) -> None
    """标记 session 为 abandoned。"""
```

## 假设清单

1. `user_profiles.user_id` 与 `users.id` 一一对应，每个用户只有一条 profile 记录
2. `session_records.session_id` 与游戏运行时 session 是不同概念——前者是数据库持久化记录，后者是 Cookie 中的会话标识，两者暂不强制关联
3. JSON 字段（`personality_data`、`seed_summary`、`report_scores`、`relationship_scores`）用 `json.dumps` 写入、`json.loads` 读出
4. `init_user_profile` 由调用方在注册时调用，不在 `create_user` 内部自动触发（保持 auth 模块不变）
5. `world_state` 表本身不存在（世界状态序列化在 `sessions.current_state_json` 中），seed_id 后续通过 serializer 加入 state JSON，不需要 DDL
6. `increment_session_count` 幂等——每次 new game / replay 时调用

## 风险点

| 风险 | 等级 | 预案 |
|------|------|------|
| JSON 字段读取时解析失败 | 低 | 所有 JSON 读取用 try/except，fallback 返回空 dict |
| 并发写入冲突 | 低 | SQLite 单写锁，当前 ThreadingHTTPServer 已串行化 WORLD_LOCK，外加 WAL 模式足够 |
| 旧数据迁移 | 无 | 两张新表，无需迁移 |
