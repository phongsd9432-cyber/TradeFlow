"""Module A - Quản lý nhà cung cấp. Không phụ thuộc module nào khác (chỉ phụ thuộc core)."""
from tradeflow.core.module import ModuleInfo

from .routes import bp

module = ModuleInfo(key="suppliers", label="Nhà cung cấp", path="/suppliers", blueprint=bp)
