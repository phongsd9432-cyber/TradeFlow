"""Thời gian. Gom về một chỗ để dễ kiểm thử."""
from __future__ import annotations

from datetime import date, datetime, timezone


def utcnow_iso() -> str:
    """Giờ UTC dạng chuỗi ISO, dùng để lưu vào CSDL."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


def today() -> date:
    return date.today()
