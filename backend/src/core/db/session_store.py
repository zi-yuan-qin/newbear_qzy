from __future__ import annotations

import json
import uuid
from typing import Any

from src.core.db.database import get_connection


def create_session_record(user_id: int, seed_id: str, seed_summary: dict[str, Any]) -> str:
    session_id = uuid.uuid4().hex

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO session_records (session_id, user_id, seed_id, seed_summary)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, user_id, seed_id, json.dumps(seed_summary, ensure_ascii=False)),
        )

    return session_id


def get_session_record(session_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM session_records WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()

    if row is None:
        return None

    return _row_to_session_dict(row)


def list_user_sessions(user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM session_records
            WHERE user_id = ?
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

    return [_row_to_session_dict(row) for row in rows]


def complete_session(session_id: str, report_id: str, scores: dict[str, Any]) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE session_records
            SET status = 'completed',
                ended_at = datetime('now'),
                report_id = ?,
                report_scores = ?
            WHERE session_id = ?
            """,
            (report_id, json.dumps(scores, ensure_ascii=False), session_id),
        )


def abandon_session(session_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE session_records
            SET status = 'abandoned',
                ended_at = datetime('now')
            WHERE session_id = ?
            """,
            (session_id,),
        )


def _row_to_session_dict(row: Any) -> dict[str, Any]:
    seed_summary = row["seed_summary"] or "{}"
    if isinstance(seed_summary, str):
        try:
            seed_summary = json.loads(seed_summary)
        except json.JSONDecodeError:
            seed_summary = {}

    report_scores = row["report_scores"] or "{}"
    if isinstance(report_scores, str):
        try:
            report_scores = json.loads(report_scores)
        except json.JSONDecodeError:
            report_scores = {}

    return {
        "session_id": row["session_id"],
        "user_id": int(row["user_id"]),
        "seed_id": row["seed_id"],
        "seed_summary": seed_summary,
        "day_completed": int(row["day_completed"]),
        "final_clock": row["final_clock"],
        "report_id": row["report_id"],
        "report_scores": report_scores,
        "started_at": row["started_at"],
        "ended_at": row["ended_at"],
        "status": row["status"],
    }
