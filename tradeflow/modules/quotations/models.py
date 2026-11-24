from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class Quotation:
    id: int
    supplier_id: int
    reference_no: str | None
    product_name: str
    specifications: str | None
    unit: str
    unit_price: Decimal
    currency: str
    moq: Decimal | None
    incoterm: str | None
    incoterm_place: str | None
    payment_terms: str | None
    lead_time_days: int | None
    quote_date: date
    valid_until: date | None
    notes: str | None
    created_at: str
    updated_at: str
    # Thông tin nhà cung cấp đi kèm (đọc từ bảng suppliers)
    supplier_name: str = ""
    supplier_country: str = ""
    supplier_rating: int | None = None
    supplier_active: bool = True
