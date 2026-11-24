"""Cấu hình ứng dụng.

Giá trị lấy từ biến môi trường (tiền tố TRADEFLOW_) hoặc file .env ở thư mục gốc.
Khóa bí mật (API key...) CHỈ để trong .env hoặc biến môi trường, không ghi vào code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_dotenv(path: Path | None = None) -> None:
    """Đọc file .env (dạng KEY=VALUE). Biến môi trường có sẵn được ưu tiên."""
    path = path or PROJECT_ROOT / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    database_path: str = str(PROJECT_ROOT / "data" / "tradeflow.db")
    host: str = "127.0.0.1"  # chỉ truy cập được từ chính máy này
    port: int = 8000
    debug: bool = False
    secret_key: str | None = None  # None: tự tạo và lưu trong thư mục data/

    @classmethod
    def from_env(cls) -> "Settings":
        d = cls()
        env = os.environ.get
        return cls(
            database_path=env("TRADEFLOW_DATABASE_PATH", d.database_path),
            host=env("TRADEFLOW_HOST", d.host),
            port=int(env("TRADEFLOW_PORT", str(d.port))),
            debug=env("TRADEFLOW_DEBUG", "") == "1",
            secret_key=env("TRADEFLOW_SECRET_KEY") or None,
        )
