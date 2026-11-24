"""Đọc và kiểm tra dữ liệu người dùng nhập (từ biểu mẫu hoặc tham số trên đường dẫn).

Mỗi hàm trả về giá trị đã làm sạch (hoặc None nếu bỏ trống / sai) và ghi lỗi vào self.errors.
Số thập phân CHỈ nhận dấu chấm (12.5), từ chối dấu phẩy: tránh nhầm "1,500" là 1.5 hay 1500 khi nhập tiền.
"""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import Iterable, Mapping

_NUMBER = re.compile(r"^(\d+(\.\d+)?|\.\d+)$")


class FormReader:
    def __init__(self, data: Mapping[str, str]):
        self.data = data
        self.errors: dict[str, str] = {}

    def raw(self, key: str) -> str:
        value = self.data.get(key)
        return value.strip() if isinstance(value, str) else ""

    def fail(self, key: str, message: str) -> None:
        self.errors.setdefault(key, message)
        return None

    def _missing(self, key: str, label: str, required: bool) -> None:
        if required:
            self.fail(key, f"{label} là bắt buộc.")
        return None

    def text(self, key, label, *, required=False, max_len=255, upper=False, collapse=False):
        value = self.raw(key)
        if collapse:
            value = " ".join(value.split())
        if not value:
            return self._missing(key, label, required)
        if len(value) > max_len:
            return self.fail(key, f"{label} tối đa {max_len} ký tự.")
        return value.upper() if upper else value

    def decimal(self, key, label, *, required=False, min_value=None, min_exclusive=None,
                max_value=None, places=6):
        value = self.raw(key)
        if not value:
            return self._missing(key, label, required)
        if not _NUMBER.match(value):
            return self.fail(
                key,
                f"{label} phải là một số, dùng dấu chấm cho số thập phân (ví dụ 12.5), "
                "không dùng dấu phẩy hay dấu cách.",
            )
        number = Decimal(value)
        if min_exclusive is not None and number <= min_exclusive:
            return self.fail(key, f"{label} phải lớn hơn {min_exclusive}.")
        if min_value is not None and number < min_value:
            return self.fail(key, f"{label} không được nhỏ hơn {min_value}.")
        if max_value is not None and number > max_value:
            return self.fail(key, f"{label} quá lớn.")
        if -number.as_tuple().exponent > places:
            return self.fail(key, f"{label} tối đa {places} chữ số thập phân.")
        return number

    def integer(self, key, label, *, required=False, min_value=None, max_value=None):
        value = self.raw(key)
        if not value:
            return self._missing(key, label, required)
        if not re.fullmatch(r"\d{1,12}", value):
            return self.fail(key, f"{label} phải là số nguyên không âm.")
        number = int(value)
        if min_value is not None and number < min_value:
            return self.fail(key, f"{label} không được nhỏ hơn {min_value}.")
        if max_value is not None and number > max_value:
            return self.fail(key, f"{label} không được lớn hơn {max_value}.")
        return number

    def day(self, key, label, *, required=False):
        value = self.raw(key)
        if not value:
            return self._missing(key, label, required)
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            return self.fail(key, f"{label} không hợp lệ (định dạng năm-tháng-ngày).")
        if not 1990 <= parsed.year <= 2100:
            return self.fail(key, f"{label} không hợp lệ: năm phải từ 1990 đến 2100.")
        return parsed

    def choice(self, key, label, allowed: Iterable[str], *, required=False, upper=False):
        value = self.raw(key)
        if upper:
            value = value.upper()
        if not value:
            return self._missing(key, label, required)
        if value not in set(allowed):
            return self.fail(key, f"{label} không hợp lệ.")
        return value
