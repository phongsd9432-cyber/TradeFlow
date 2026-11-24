"""Module C - So sánh báo giá. Phụ thuộc: quotations (và qua đó là suppliers)."""
from tradeflow.core.module import ModuleInfo

from .routes import bp

module = ModuleInfo(key="comparison", label="So sánh", path="/comparison", blueprint=bp)
