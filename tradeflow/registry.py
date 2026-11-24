"""Danh sách module của ứng dụng, theo thứ tự hiển thị trên menu.

THÊM MODULE MỚI: tạo thư mục trong tradeflow/modules/, rồi thêm một dòng vào load_modules().
Quy tắc phụ thuộc (có test kiểm tra tự động): core <- suppliers <- quotations <- comparison <- dashboard.
"""
from __future__ import annotations

from tradeflow.core.module import ModuleInfo


def load_modules() -> list[ModuleInfo]:
    from tradeflow.modules import comparison, quotations, suppliers

    return [suppliers.module, quotations.module, comparison.module]
