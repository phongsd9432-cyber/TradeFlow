"""Module B - Quản lý báo giá. Phụ thuộc: suppliers."""
from tradeflow.core.module import ModuleInfo

from .routes import bp

module = ModuleInfo(key="quotations", label="Báo giá", path="/quotations", blueprint=bp)
