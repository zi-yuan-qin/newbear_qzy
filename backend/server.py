from __future__ import annotations

import json
import threading

from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.core.auth.auth_service import (
    AuthUser,
    create_user,
    get_user_by_session,
    login_user,
    logout_session,
)
from src.core.db.database import (
    init_db,
    save_report,
    save_user_message,
    save_world_state,
)
from src.core.db.session_store import (
    abandon_session,
    complete_session,
    create_session_record,
    get_session_record,
    list_user_sessions,
)
from src.core.db.user_profile import increment_session_count, init_user_profile, update_user_profile
from src.core.config.seed_generator import generate
from src.core.world.meeting_discussion_engine import finish_meeting, run_meeting_tick
from src.core.world.meeting_engine import (
    add_user_meeting_message,
    close_active_meeting,
    enter_active_meeting,
    start_active_meeting,
)
from src.core.world.pantry_discussion_engine import finish_pantry, run_pantry_tick
from src.core.world.pantry_engine import add_user_pantry_message, close_active_pantry
from src.core.world.reflection_engine import schedule_memory_reflections
from src.core.world.report_engine import close_active_report
from src.core.world.runtime_state import WorldRuntimeState
from src.core.world.serializer import serialize_world_state
from src.core.world.step_engine import run_one_step
from src.core.world.world_factory import create_initial_world_state


WORLDS: dict[str, WorldRuntimeState] = {}
WORLD_LOCK = threading.Lock()
ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT_DIR / "frontend" / "web"
APP_DIST_DIR = ROOT_DIR / "frontend" / "app" / "dist"


def write_json(
    handler: BaseHTTPRequestHandler,
    payload: dict[str, Any],
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> None:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", handler.headers.get("Origin", "*"))
    handler.send_header("Access-Control-Allow-Credentials", "true")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(raw)))
    for key, value in (headers or {}).items():
        handler.send_header(key, value)
    handler.end_headers()
    handler.wfile.write(raw)


def create_world_for_user(user: AuthUser) -> WorldRuntimeState:
    init_user_profile(user.user_id)
    seed = generate(user.user_id)
    world = create_initial_world_state(seed)
    world.session_record_id = create_session_record(
        user.user_id,
        seed.seed_id,
        world.seed_summary,
    )
    increment_session_count(user.user_id)
    return world


def get_or_create_world(user: AuthUser) -> WorldRuntimeState:
    world = WORLDS.get(user.session_id)
    if world is None:
        world = create_world_for_user(user)
        WORLDS[user.session_id] = world
    return world


def get_cookie(handler: BaseHTTPRequestHandler, name: str) -> str:
    raw = handler.headers.get("Cookie", "")
    cookie = SimpleCookie()
    cookie.load(raw)

    if name not in cookie:
        return ""

    return cookie[name].value


def get_current_user(handler: BaseHTTPRequestHandler) -> AuthUser | None:
    session_id = get_cookie(handler, "newbear_session")
    return get_user_by_session(session_id)


def require_user(handler: BaseHTTPRequestHandler) -> AuthUser | None:
    user = get_current_user(handler)
    if user is None:
        write_json(handler, {"error": "Unauthorized"}, status=401)
        return None
    return user


def build_session_cookie(session_id: str) -> str:
    return f"newbear_session={session_id}; Path=/; HttpOnly; SameSite=Lax"


def build_clear_cookie() -> str:
    return "newbear_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"


def serialize_user(user: AuthUser) -> dict[str, Any]:
    return {
        "user_id": user.user_id,
        "username": user.username,
        "session_id": user.session_id,
    }


def save_state_for_session(session_id: str, world: WorldRuntimeState) -> dict[str, Any]:
    state = serialize_world_state(world)
    save_world_state(session_id, state)
    return state


def save_active_report_if_needed(user: AuthUser, world: WorldRuntimeState, state: dict[str, Any]) -> None:
    active_report = state.get("active_report")
    if not active_report or not active_report.get("visible"):
        return

    if world.report_saved:
        return

    save_report(
        user_id=user.user_id,
        session_id=user.session_id,
        clock=str(active_report.get("clock", world.company.clock)),
        scores=active_report.get("scores", {}),
        report=active_report,
    )
    world.report_saved = True


def complete_active_session_if_reported(user: AuthUser, world: WorldRuntimeState) -> None:
    report = world.active_report
    if report is None:
        return

    complete_session(
        world.session_record_id or user.session_id,
        report_id=report.report_id,
        scores=report.scores,
        day_completed=world.company.day,
        final_clock=world.company.clock,
    )

    update_user_profile(
        user.user_id,
        {
            "last_report_id": report.report_id,
            "last_report_scores": report.scores,
            "last_trait_summary": report.trait_summary,
            "last_session_seed_id": world.seed_id,
        },
    )


def guess_content_type(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix == ".png":
        return "image/png"

    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"

    if suffix == ".webp":
        return "image/webp"

    if suffix == ".svg":
        return "image/svg+xml"

    if suffix == ".json":
        return "application/json; charset=utf-8"

    if suffix == ".js":
        return "application/javascript; charset=utf-8"

    if suffix == ".css":
        return "text/css; charset=utf-8"

    return "application/octet-stream"


class NewbearHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin", "*"))
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.serve_frontend_index()
            return

        if parsed.path == "/main.js":
            self.serve_file(WEB_DIR / "main.js", "application/javascript; charset=utf-8")
            return

        if parsed.path == "/styles.css":
            self.serve_file(WEB_DIR / "styles.css", "text/css; charset=utf-8")
            return

        if parsed.path.startswith("/assets/"):
            asset_path = APP_DIST_DIR / parsed.path.lstrip("/")
            if not asset_path.exists():
                asset_path = WEB_DIR / parsed.path.lstrip("/")
            self.serve_file(asset_path, guess_content_type(asset_path))
            return

        app_static_path = APP_DIST_DIR / parsed.path.lstrip("/")
        if APP_DIST_DIR.exists() and app_static_path.exists() and app_static_path.is_file():
            self.serve_file(app_static_path, guess_content_type(app_static_path))
            return

        if parsed.path == "/api/auth/me":
            user = get_current_user(self)
            if user is None:
                write_json(self, {"authenticated": False})
                return

            write_json(
                self,
                {
                    "authenticated": True,
                    "user": serialize_user(user),
                },
            )
            return

        if parsed.path == "/api/state":
            user = require_user(self)
            if user is None:
                return

            with WORLD_LOCK:
                world = get_or_create_world(user)
                state = save_state_for_session(user.session_id, world)

            write_json(self, {"state": state})
            return

        if parsed.path == "/api/sessions":
            user = require_user(self)
            if user is None:
                return

            write_json(self, {"sessions": list_user_sessions(user.user_id)})
            return

        if parsed.path.startswith("/api/sessions/"):
            user = require_user(self)
            if user is None:
                return

            session_id = parsed.path.removeprefix("/api/sessions/").strip("/")
            record = get_session_record(session_id)
            if record is None or record.get("user_id") != user.user_id:
                write_json(self, {"error": "Session not found"}, status=404)
                return

            write_json(self, {"session": record})
            return

        if not parsed.path.startswith("/api/"):
            self.serve_frontend_index()
            return

        write_json(self, {"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/auth/register":
            payload = self.read_json()
            username = str(payload.get("username", "") or "")
            password = str(payload.get("password", "") or "")

            try:
                user = create_user(username, password)
            except ValueError as exc:
                write_json(self, {"error": str(exc)}, status=400)
                return

            with WORLD_LOCK:
                world = get_or_create_world(user)
                state = save_state_for_session(user.session_id, world)

            write_json(
                self,
                {"ok": True, "user": serialize_user(user), "state": state},
                headers={"Set-Cookie": build_session_cookie(user.session_id)},
            )
            return

        if parsed.path == "/api/auth/login":
            payload = self.read_json()
            username = str(payload.get("username", "") or "")
            password = str(payload.get("password", "") or "")

            try:
                user = login_user(username, password)
            except ValueError as exc:
                write_json(self, {"error": str(exc)}, status=400)
                return

            with WORLD_LOCK:
                world = get_or_create_world(user)
                state = save_state_for_session(user.session_id, world)

            write_json(
                self,
                {"ok": True, "user": serialize_user(user), "state": state},
                headers={"Set-Cookie": build_session_cookie(user.session_id)},
            )
            return

        if parsed.path == "/api/auth/logout":
            session_id = get_cookie(self, "newbear_session")
            logout_session(session_id)
            with WORLD_LOCK:
                WORLDS.pop(session_id, None)

            write_json(
                self,
                {"ok": True},
                headers={"Set-Cookie": build_clear_cookie()},
            )
            return

        if parsed.path == "/api/reset":
            user = require_user(self)
            if user is None:
                return

            with WORLD_LOCK:
                old_world = WORLDS.get(user.session_id)
                if old_world is not None:
                    abandon_session(old_world.session_record_id or user.session_id)
                WORLDS[user.session_id] = create_world_for_user(user)
                state = save_state_for_session(user.session_id, WORLDS[user.session_id])

            write_json(self, {"ok": True, "state": state})
            return

        if parsed.path == "/api/step":
            user = require_user(self)
            if user is None:
                return

            payload = self.read_json()
            affair = str(payload.get("affair", "") or "")

            with WORLD_LOCK:
                world = get_or_create_world(user)
                if affair.strip():
                    save_user_message(
                        user_id=user.user_id,
                        session_id=user.session_id,
                        clock=world.company.clock,
                        scene="world",
                        message=affair,
                    )

                run_one_step(world, affair=affair)
                schedule_memory_reflections(world, world_lock=WORLD_LOCK)
                state = save_state_for_session(user.session_id, world)
                save_active_report_if_needed(user, world, state)

            write_json(self, {"ok": True, "state": state})
            return

        if parsed.path == "/api/meeting/enter":
            user = require_user(self)
            if user is None:
                return

            with WORLD_LOCK:
                world = get_or_create_world(user)
                enter_active_meeting(world)
                state = save_state_for_session(user.session_id, world)

            write_json(self, {"ok": True, "state": state})
            return

        if parsed.path == "/api/meeting/start":
            user = require_user(self)
            if user is None:
                return

            with WORLD_LOCK:
                world = get_or_create_world(user)
                start_active_meeting(world)
                state = save_state_for_session(user.session_id, world)

            write_json(self, {"ok": True, "state": state})
            return

        if parsed.path == "/api/meeting/say":
            user = require_user(self)
            if user is None:
                return

            payload = self.read_json()
            message = str(payload.get("message", "") or "")

            with WORLD_LOCK:
                world = get_or_create_world(user)
                save_user_message(
                    user_id=user.user_id,
                    session_id=user.session_id,
                    clock=world.company.clock,
                    scene="meeting",
                    message=message,
                )
                add_user_meeting_message(world, message)
                state = save_state_for_session(user.session_id, world)

            write_json(self, {"ok": True, "state": state})
            return

        if parsed.path == "/api/meeting/tick":
            user = require_user(self)
            if user is None:
                return

            with WORLD_LOCK:
                world = get_or_create_world(user)
                run_meeting_tick(world)
                state = save_state_for_session(user.session_id, world)

            write_json(self, {"ok": True, "state": state})
            return

        if parsed.path == "/api/meeting/finish":
            user = require_user(self)
            if user is None:
                return

            with WORLD_LOCK:
                world = get_or_create_world(user)
                result = finish_meeting(world)
                state = save_state_for_session(user.session_id, world)

            write_json(self, {"ok": True, "result": result, "state": state})
            return

        if parsed.path == "/api/meeting/close":
            user = require_user(self)
            if user is None:
                return

            with WORLD_LOCK:
                world = get_or_create_world(user)
                close_active_meeting(world)
                state = save_state_for_session(user.session_id, world)

            write_json(self, {"ok": True, "state": state})
            return

        if parsed.path == "/api/pantry/say":
            user = require_user(self)
            if user is None:
                return

            payload = self.read_json()
            message = str(payload.get("message", "") or "")

            with WORLD_LOCK:
                world = get_or_create_world(user)
                save_user_message(
                    user_id=user.user_id,
                    session_id=user.session_id,
                    clock=world.company.clock,
                    scene="pantry",
                    message=message,
                )
                add_user_pantry_message(world, message)
                run_pantry_tick(world)
                state = save_state_for_session(user.session_id, world)

            write_json(self, {"ok": True, "state": state})
            return

        if parsed.path == "/api/pantry/tick":
            user = require_user(self)
            if user is None:
                return

            with WORLD_LOCK:
                world = get_or_create_world(user)
                run_pantry_tick(world)
                state = save_state_for_session(user.session_id, world)

            write_json(self, {"ok": True, "state": state})
            return

        if parsed.path == "/api/pantry/leave":
            user = require_user(self)
            if user is None:
                return

            with WORLD_LOCK:
                world = get_or_create_world(user)
                finish_pantry(world)
                close_active_pantry(world)
                state = save_state_for_session(user.session_id, world)

            write_json(self, {"ok": True, "state": state})
            return

        if parsed.path == "/api/report/close":
            user = require_user(self)
            if user is None:
                return

            with WORLD_LOCK:
                world = get_or_create_world(user)
                complete_active_session_if_reported(user, world)
                close_active_report(world)
                state = save_state_for_session(user.session_id, world)

            write_json(self, {"ok": True, "state": state})
            return

        write_json(self, {"error": "Not found"}, status=404)

    def read_json(self) -> dict[str, Any]:
        size = int(self.headers.get("Content-Length", "0") or 0)
        if size <= 0:
            return {}

        raw = self.rfile.read(size)

        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

        return data if isinstance(data, dict) else {}

    def serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists() or not path.is_file():
            write_json(self, {"error": "Not found"}, status=404)
            return

        raw = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def serve_frontend_index(self) -> None:
        react_index = APP_DIST_DIR / "index.html"
        if react_index.exists():
            self.serve_file(react_index, "text/html; charset=utf-8")
            return

        self.serve_file(WEB_DIR / "index.html", "text/html; charset=utf-8")


def main() -> None:
    init_db()

    host = "0.0.0.0"
    port = 8501
    server = ThreadingHTTPServer((host, port), NewbearHandler)

    print(f"newbear backend running: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
