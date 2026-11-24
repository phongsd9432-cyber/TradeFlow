"""Các loại lỗi nghiệp vụ dùng chung."""
from __future__ import annotations


class TradeFlowError(Exception):
    pass


class NotFoundError(TradeFlowError):
    """Không tìm thấy dữ liệu được yêu cầu (hiển thị trang 404)."""


class ConflictError(TradeFlowError):
    """Thao tác không thực hiện được vì xung đột với dữ liệu hiện có."""


class ValidationError(TradeFlowError):
    """Dữ liệu nhập chưa hợp lệ. errors: {tên_trường: thông_báo}."""

    def __init__(self, errors: dict[str, str]):
        super().__init__("; ".join(errors.values()))
        self.errors = errors
