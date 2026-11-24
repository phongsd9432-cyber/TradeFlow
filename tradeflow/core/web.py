"""Lớp web dùng chung: khóa bí mật, kiểm tra nguồn gửi form, header bảo mật, bộ lọc hiển thị, trang lỗi."""
from __future__ import annotations

import secrets
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, abort, render_template, request
from werkzeug.exceptions import HTTPException

from tradeflow import __version__
from tradeflow.core import reference_data as ref
from tradeflow.core.config import Settings
from tradeflow.core.db import close_db
from tradeflow.core.errors import NotFoundError
from tradeflow.core.module import ModuleInfo
from tradeflow.core.text import format_date, format_datetime, format_number

SECURITY_HEADERS = {
    # Không tải gì từ bên ngoài: ứng dụng chạy được khi offline và không gửi dữ liệu ra ngoài.
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; form-action 'self'; "
    "frame-ancestors 'none'; base-uri 'self'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
}
ERROR_MESSAGES = {
    403: "Yêu cầu bị từ chối vì không xuất phát từ trang của TradeFlow.",
    404: "Không tìm thấy trang hoặc dữ liệu bạn yêu cầu.",
    405: "Thao tác này không được hỗ trợ.",
}


def _secret_key(settings: Settings) -> str:
    """Khóa ký cookie. Lấy từ cấu hình, nếu không có thì tạo một lần và lưu cạnh file CSDL."""
    if settings.secret_key:
        return settings.secret_key
    path = Path(settings.database_path).parent / "secret.key"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    key = secrets.token_hex(32)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(key, encoding="utf-8")
    return key


def install(app: Flask, modules: list[ModuleInfo], settings: Settings) -> None:
    app.secret_key = _secret_key(settings)
    app.config.update(SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_HTTPONLY=True)
    app.teardown_appcontext(close_db)

    app.jinja_env.filters.update(
        num=lambda v, d=6: format_number(v, max_decimals=d),
        money=lambda v, d=6: format_number(v, min_decimals=2, max_decimals=d),
        dmy=format_date,
        dmy_hm=format_datetime,
        country=lambda code: ref.COUNTRIES.get(code, code or "—"),
        stars=lambda n: ("★" * n + "☆" * (5 - n)) if n else "—",
    )
    app.jinja_env.globals.update(
        COUNTRY_OPTIONS=ref.COUNTRY_OPTIONS,
        CURRENCY_OPTIONS=ref.CURRENCY_OPTIONS,
        INCOTERM_OPTIONS=ref.INCOTERM_OPTIONS,
        UNIT_SUGGESTIONS=ref.UNIT_SUGGESTIONS,
    )
    nav = [{"label": m.label, "path": m.path} for m in modules]

    @app.context_processor
    def _inject():
        return {"nav": nav, "app_version": __version__}

    @app.before_request
    def _same_origin_only():
        """Chặn trang web lạ gửi form vào TradeFlow (CSRF): nguồn gửi phải trùng địa chỉ đang chạy."""
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return None
        source = request.headers.get("Origin") or request.headers.get("Referer")
        if source and urlsplit(source).netloc != request.host:
            abort(403)
        return None

    @app.after_request
    def _security_headers(response):
        for key, value in SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        return response

    @app.errorhandler(NotFoundError)
    def _not_found(exc):
        return render_template("error.html", status=404, message=str(exc) or ERROR_MESSAGES[404]), 404

    @app.errorhandler(HTTPException)
    def _http_error(exc):
        message = ERROR_MESSAGES.get(exc.code, "Đã xảy ra lỗi. Vui lòng thử lại.")
        return render_template("error.html", status=exc.code, message=message), exc.code
