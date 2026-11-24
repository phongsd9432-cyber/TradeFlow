"""Khung ứng dụng: ghép cấu hình, CSDL, các module và lớp web."""
from __future__ import annotations

from pathlib import Path

from flask import Flask

from tradeflow.core import web
from tradeflow.core.config import Settings
from tradeflow.core.db import connect, run_migrations
from tradeflow.registry import load_modules

CORE_DIR = Path(__file__).resolve().parent / "core"


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or Settings.from_env()
    app = Flask(
        "tradeflow",
        template_folder=str(CORE_DIR / "templates"),
        static_folder=str(CORE_DIR / "static"),
    )
    app.config.update(DATABASE_PATH=settings.database_path)

    conn = connect(settings.database_path)
    try:
        run_migrations(conn)  # tự cập nhật cấu trúc CSDL khi khởi động
    finally:
        conn.close()

    modules = load_modules()
    for module in modules:
        app.register_blueprint(module.blueprint)
    web.install(app, modules, settings)
    return app
