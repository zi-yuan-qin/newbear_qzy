from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path(__file__).resolve().parents[3] / "data" / "newbear.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                ended_at TEXT,
                current_state_json TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                clock TEXT NOT NULL,
                scene TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                clock TEXT NOT NULL,
                scores_json TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )

        connection.execute(
            """
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
            )
            """
        )

        connection.execute(
            """
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
            )
            """
        )


def save_world_state(session_id: str, state: dict[str, Any]) -> None:
    raw = json.dumps(state, ensure_ascii=False)

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE sessions
            SET current_state_json = ?
            WHERE id = ?
            """,
            (raw, session_id),
        )


def save_user_message(
    *,
    user_id: int,
    session_id: str,
    clock: str,
    scene: str,
    message: str,
) -> None:
    clean_message = str(message or "").strip()
    if not clean_message:
        return

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO user_messages (user_id, session_id, clock, scene, message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, session_id, clock, scene, clean_message),
        )


def save_report(
    *,
    user_id: int,
    session_id: str,
    clock: str,
    scores: dict[str, Any],
    report: dict[str, Any],
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO reports (user_id, session_id, clock, scores_json, report_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                session_id,
                clock,
                json.dumps(scores, ensure_ascii=False),
                json.dumps(report, ensure_ascii=False),
            ),
        )


def report_exists(session_id: str) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id FROM reports
            WHERE session_id = ?
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()

    return row is not None
