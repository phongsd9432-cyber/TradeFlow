"""Chuẩn hóa văn bản và định dạng số, ngày để hiển thị."""
from __future__ import annotations

import unicodedata
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

NBSP = "\u00a0"
DASH = "—"


def fold(text: object) -> str:
    """Chữ thường, bỏ dấu tiếng Việt (đ→d), gọn khoảng trắng. Dùng để tìm kiếm và so khớp tên."""
    if not text:
        return ""
    s = unicodedata.normalize("NFD", str(text).casefold().replace("đ", "d"))
    return " ".join("".join(c for c in s if unicodedata.category(c) != "Mn").split())


def format_number(value, *, min_decimals: int = 0, max_decimals: int = 6) -> str:
    """1234567.5 -> '1 234 567.5' (dấu cách ngăn nghìn, dấu chấm thập phân).

    Dùng dấu cách thay vì dấu phẩy/chấm để người đọc theo kiểu Việt hay quốc tế đều không hiểu nhầm.
    """
    if value is None or value == "":
        return DASH
    number = value if isinstance(value, Decimal) else Decimal(str(value))
    number = number.quantize(Decimal(1).scaleb(-max_decimals), rounding=ROUND_HALF_UP)
    sign = "-" if number < 0 else ""
    whole, _, frac = f"{abs(number):f}".partition(".")
    frac = frac.rstrip("0").ljust(min_decimals, "0")
    grouped = f"{int(whole):,}".replace(",", NBSP)
    return sign + grouped + ("." + frac if frac else "")


def plain_number(value) -> str:
    """Số dạng chuỗi thuần để điền vào ô nhập: Decimal('12.500') -> '12.5'."""
    if value is None:
        return ""
    return format(Decimal(value).normalize(), "f")


def format_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else DASH


def format_datetime(iso_utc: str | None) -> str:
    """Chuỗi ISO giờ UTC (từ CSDL) -> giờ địa phương của máy chạy ứng dụng."""
    if not iso_utc:
        return DASH
    dt = datetime.fromisoformat(iso_utc).replace(tzinfo=timezone.utc).astimezone()
    return dt.strftime("%d/%m/%Y %H:%M")
