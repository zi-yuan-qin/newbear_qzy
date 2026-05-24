"""P0-001 数据库扩展单元测试 — 5 条必需测试"""

from src.core.db.database import get_connection, init_db
from src.core.db.user_profile import (
    get_user_profile,
    increment_session_count,
    init_user_profile,
    update_user_profile,
)
from src.core.db.session_store import (
    abandon_session,
    complete_session,
    create_session_record,
    get_session_record,
    list_user_sessions,
)

PASSED = 0
FAILED = 0


def check(description: str, condition: bool, detail: str = "") -> None:
    global PASSED, FAILED

    if condition:
        PASSED += 1
        print(f"  PASS  {description}")
    else:
        FAILED += 1
        print(f"  FAIL  {description}" + (f"  -> {detail}" if detail else ""))


def setup_user() -> int:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO users (id, username, password_hash)
            VALUES (999, '__test_p0_001', 'test_hash')
            """
        )
        row = connection.execute(
            "SELECT id FROM users WHERE id = 999"
        ).fetchone()

    return int(row["id"])


def cleanup(user_id: int, session_ids: list[str]) -> None:
    with get_connection() as connection:
        for session_id in session_ids:
            connection.execute(
                "DELETE FROM session_records WHERE session_id = ?",
                (session_id,),
            )
        connection.execute(
            "DELETE FROM user_profiles WHERE user_id = ?",
            (user_id,),
        )


def main() -> None:
    init_db()
    user_id = setup_user()

    session_ids: list[str] = []

    try:
        # ── 测试 1 ──
        print("测试 1: 新建用户 → init_user_profile → get_user_profile 返回非空")

        profile = init_user_profile(user_id)
        check("init 返回非空 dict", bool(profile))
        fetched = get_user_profile(user_id)
        check("get 返回非 None", fetched is not None)
        check("user_id 匹配", fetched is not None and fetched["user_id"] == user_id)
        check("total_sessions 初始为 0", fetched is not None and fetched["total_sessions"] == 0)

        # ── 测试 2 ──
        print("测试 2: update_user_profile 写入 → 再读取验证字段一致")

        personality = {
            "openness": 75,
            "conflict_style": "avoid",
            "closest_ally": "xionglaoban",
        }
        updated = update_user_profile(user_id, personality)
        check("更新后 openness=75", updated.get("personality_data", {}).get("openness") == 75)
        check("更新后 conflict_style=avoid", updated.get("personality_data", {}).get("conflict_style") == "avoid")

        refetched = get_user_profile(user_id)
        check("重新读取 openness 一致", refetched is not None and refetched.get("personality_data", {}).get("openness") == 75)

        # merge 测试: 追加新字段，已有字段保留
        merged = update_user_profile(user_id, {"conscientiousness": 60})
        check("merge 后旧字段保留", merged.get("personality_data", {}).get("openness") == 75)
        check("merge 后新字段存在", merged.get("personality_data", {}).get("conscientiousness") == 60)

        # ── 测试 3 ──
        print("测试 3: create → complete → status 变为 completed")

        session_id = create_session_record(
            user_id,
            seed_id="seed-test-001",
            seed_summary={"cash": 5000, "runway_days": 10},
        )
        session_ids.append(session_id)
        check("session_id 非空", bool(session_id))

        record = get_session_record(session_id)
        check("get 返回非 None", record is not None)
        check("status 初始为 active", record is not None and record["status"] == "active")
        check("seed_id 正确", record is not None and record["seed_id"] == "seed-test-001")
        check("seed_summary 正确", record is not None and record.get("seed_summary", {}).get("cash") == 5000)

        complete_session(
            session_id,
            report_id="daily_big_five",
            scores={"O": 75, "C": 60, "E": 80, "A": 55, "S": 65},
        )
        completed = get_session_record(session_id)
        check("status 变为 completed", completed is not None and completed["status"] == "completed")
        check(
            "report_scores 包含 O=75",
            completed is not None and completed.get("report_scores", {}).get("O") == 75,
        )

        # ── 测试 4 ──
        print("测试 4: list_user_sessions 时间倒序 + limit 生效")

        session_id_2 = create_session_record(user_id, "seed-test-002", {"cash": 3000})
        session_id_3 = create_session_record(user_id, "seed-test-003", {"cash": 7000})
        session_ids.extend([session_id_2, session_id_3])

        all_sessions = list_user_sessions(user_id, limit=20)
        check("至少返回 3 条", len(all_sessions) >= 3)

        limited = list_user_sessions(user_id, limit=2)
        check("limit=2 返回 2 条", len(limited) == 2)

        check(
            "时间倒序: 第一条比第二条晚",
            len(all_sessions) >= 2 and all_sessions[0]["started_at"] >= all_sessions[1]["started_at"],
        )

        # ── 测试 5 ──
        print("测试 5: 同一 user 创建 3 session → increment_session_count → total_sessions=3")

        init_user_profile(user_id)
        increment_session_count(user_id)
        increment_session_count(user_id)
        count = increment_session_count(user_id)

        check("increment 返回 >= 3", count >= 3)

        final_profile = get_user_profile(user_id)
        check("total_sessions >= 3", final_profile is not None and final_profile["total_sessions"] >= 3)

        # ── abandon 补充测试 ──
        print("补充: abandon_session 测试")

        abandon_id = create_session_record(user_id, "seed-test-abandon", {"cash": 4000})
        session_ids.append(abandon_id)
        abandon_session(abandon_id)
        abandoned = get_session_record(abandon_id)
        check("status 变为 abandoned", abandoned is not None and abandoned["status"] == "abandoned")

        # ── 空查询测试 ──
        print("补充: 边界条件")

        check("不存在的 user_id 返回 None", get_user_profile(99999) is None)
        check("不存在的 session_id 返回 None", get_session_record("nonexistent") is None)
        check("不存在的 user_id 列表为空", list_user_sessions(99999) == [])
        check("get_user_profile None 不报错", get_user_profile(99999) is None)

    finally:
        cleanup(user_id, session_ids)

    # ── 结果 ──
    total = PASSED + FAILED
    print(f"\n{'=' * 40}")
    print(f"结果: {PASSED}/{total} 通过, {FAILED} 失败")
    if FAILED > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
