"""Kết nối cơ sở dữ liệu SQLite và bộ chạy migration (đổi cấu trúc CSDL có kiểm soát)."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from flask import current_app, g

from tradeflow.core.config import PROJECT_ROOT

MIGRATIONS_DIR = PROJECT_ROOT / "migrations"
_VERSION_RE = re.compile(r"^\d{4}_[a-z0-9_]+$")


def connect(path: str) -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # bắt buộc để ràng buộc khóa ngoại có hiệu lực
    return conn


def get_db() -> sqlite3.Connection:
    """Kết nối dùng chung trong một request, tự đóng khi request kết thúc."""
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_PATH"])
    return g.db


def close_db(_exc: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def run_migrations(conn: sqlite3.Connection, directory: Path = MIGRATIONS_DIR) -> list[str]:
    """Chạy các file migrations/NNNN_ten.sql chưa áp dụng, theo thứ tự. Trả về danh sách đã chạy.

    Mỗi file chạy trong một giao dịch: lỗi giữa chừng thì hoàn tác toàn bộ file đó.
    QUY TẮC: không sửa file migration đã phát hành; muốn đổi cấu trúc thì thêm file số mới.
    """
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    conn.commit()
    done = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    applied: list[str] = []
    for path in sorted(directory.glob("[0-9][0-9][0-9][0-9]_*.sql")):
        version = path.stem
        if version in done:
            continue
        if not _VERSION_RE.match(version):
            raise ValueError(f"Tên file migration không hợp lệ: {path.name}")
        script = (
            "BEGIN;\n"
            + path.read_text(encoding="utf-8")
            + f"\nINSERT INTO schema_migrations (version, applied_at) VALUES ('{version}', datetime('now'));\n"
            + "COMMIT;"
        )
        try:
            conn.executescript(script)
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        applied.append(version)
    return applied
