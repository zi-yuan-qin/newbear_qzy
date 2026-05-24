from __future__ import annotations

import json
from typing import Any

from src.core.db.database import get_connection


def init_user_profile(user_id: int) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO user_profiles (user_id)
            VALUES (?)
            """,
            (user_id,),
        )

        row = connection.execute(
            """
            SELECT * FROM user_profiles WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    return _row_to_profile_dict(row)


def get_user_profile(user_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM user_profiles WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    if row is None:
        return None

    return _row_to_profile_dict(row)


def update_user_profile(user_id: int, personality_data: dict[str, Any]) -> dict[str, Any]:
    existing = get_user_profile(user_id)
    if existing is None:
        existing_raw = {}
    else:
        existing_raw = existing.get("personality_data", {})
        if isinstance(existing_raw, str):
            try:
                existing_raw = json.loads(existing_raw)
            except json.JSONDecodeError:
                existing_raw = {}

    merged = {**existing_raw, **personality_data}

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE user_profiles
            SET personality_data = ?,
                updated_at = datetime('now')
            WHERE user_id = ?
            """,
            (json.dumps(merged, ensure_ascii=False), user_id),
        )

    return get_user_profile(user_id) or {}


def increment_session_count(user_id: int) -> int:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE user_profiles
            SET total_sessions = total_sessions + 1,
                updated_at = datetime('now')
            WHERE user_id = ?
            """,
            (user_id,),
        )

        row = connection.execute(
            """
            SELECT total_sessions FROM user_profiles WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    if row is None:
        return 0

    return int(row["total_sessions"])


def _row_to_profile_dict(row: Any) -> dict[str, Any]:
    if row is None:
        return {}

    personality_data = row["personality_data"] or "{}"
    if isinstance(personality_data, str):
        try:
            personality_data = json.loads(personality_data)
        except json.JSONDecodeError:
            personality_data = {}

    relationship_scores = row["relationship_scores"] or "{}"
    if isinstance(relationship_scores, str):
        try:
            relationship_scores = json.loads(relationship_scores)
        except json.JSONDecodeError:
            relationship_scores = {}

    return {
        "user_id": int(row["user_id"]),
        "personality_data": personality_data,
        "total_sessions": int(row["total_sessions"]),
        "total_playtime_seconds": int(row["total_playtime_seconds"]),
        "preferred_decision_style": row["preferred_decision_style"],
        "preferred_conflict_style": row["preferred_conflict_style"],
        "avg_input_length": float(row["avg_input_length"]) if row["avg_input_length"] is not None else None,
        "relationship_scores": relationship_scores,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
