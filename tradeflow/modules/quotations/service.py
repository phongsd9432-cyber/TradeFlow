"""Nghiệp vụ báo giá: kiểm tra dữ liệu, hiệu lực, tìm kiếm, gom theo sản phẩm."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from tradeflow.core import clock
from tradeflow.core.errors import NotFoundError, ValidationError
from tradeflow.core.forms import FormReader
from tradeflow.core.reference_data import CURRENCIES, INCOTERMS
from tradeflow.core.text import fold, plain_number
from tradeflow.modules.suppliers.service import SupplierService

from . import repository as repo
from .models import Quotation

EXPIRING_SOON_DAYS = 7
MAX_NUMBER = Decimal("999999999999")


@dataclass(frozen=True)
class Validity:
    code: str  # "none" | "valid" | "expiring" | "expired"
    label: str
    days_left: int | None


def validity_of(quote: Quotation, today: date | None = None) -> Validity:
    """Báo giá còn hiệu lực không? Hạn cuối tính là hết ngày valid_until."""
    today = today or clock.today()
    if quote.valid_until is None:
        return Validity("none", "Không ghi hạn", None)
    days = (quote.valid_until - today).days
    if days < 0:
        return Validity("expired", "Đã hết hạn", days)
    if days <= EXPIRING_SOON_DAYS:
        return Validity("expiring", f"Còn {days} ngày", days)
    return Validity("valid", "Còn hiệu lực", days)


@dataclass(frozen=True)
class ProductSummary:
    name: str
    quote_count: int
    supplier_count: int
    currencies: list[str]


class QuotationService:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.suppliers = SupplierService(db)

    # ---- đọc ----
    def get(self, quotation_id: int) -> Quotation:
        quote = repo.get(self.db, quotation_id)
        if quote is None:
            raise NotFoundError("Không tìm thấy báo giá này.")
        return quote

    def search(self, *, q: str = "", supplier_id: int | None = None, status: str = "",
               today: date | None = None) -> list[Quotation]:
        items = repo.list_all(self.db, supplier_id)
        needle = fold(q)
        if needle:
            items = [x for x in items if needle in fold(
                f"{x.product_name} {x.supplier_name} {x.reference_no or ''} {x.specifications or ''}")]
        if status == "expired":
            items = [x for x in items if validity_of(x, today).code == "expired"]
        elif status == "active":
            items = [x for x in items if validity_of(x, today).code != "expired"]
        return items

    def by_ids(self, ids: list[int]) -> list[Quotation]:
        return repo.list_by_ids(self.db, ids)

    def by_product(self, product_name: str) -> list[Quotation]:
        key = fold(product_name)
        return [x for x in repo.list_all(self.db) if fold(x.product_name) == key]

    def product_names(self) -> list[str]:
        """Tên sản phẩm đã dùng (mỗi tên một lần, không phân biệt hoa/thường/dấu) để gợi ý khi nhập."""
        seen: dict[str, str] = {}
        for x in sorted(repo.list_all(self.db), key=lambda i: i.id):  # giữ cách viết nhập đầu tiên
            seen.setdefault(fold(x.product_name), x.product_name)
        return sorted(seen.values(), key=fold)

    def product_summary(self) -> list[ProductSummary]:
        groups: dict[str, list[Quotation]] = {}
        for x in sorted(repo.list_all(self.db), key=lambda i: i.id):  # tên hiển thị = cách viết nhập đầu tiên
            groups.setdefault(fold(x.product_name), []).append(x)
        result = [
            ProductSummary(
                name=items[0].product_name,
                quote_count=len(items),
                supplier_count=len({i.supplier_id for i in items}),
                currencies=sorted({i.currency for i in items}),
            )
            for items in groups.values()
        ]
        return sorted(result, key=lambda p: (-p.quote_count, fold(p.name)))

    def stats(self, today: date | None = None) -> dict[str, int]:
        items = repo.list_all(self.db)
        codes = [validity_of(x, today).code for x in items]
        return {"total": len(items), "expired": codes.count("expired"), "expiring": codes.count("expiring")}

    @staticmethod
    def form_values(q: Quotation) -> dict[str, str]:
        values = {}
        for f in repo.FIELDS:
            v = getattr(q, f)
            if v is None:
                values[f] = ""
            elif isinstance(v, Decimal):
                values[f] = plain_number(v)
            elif isinstance(v, date):
                values[f] = v.isoformat()
            else:
                values[f] = str(v)
        return values

    # ---- kiểm tra dữ liệu ----
    def clean(self, form, existing: Quotation | None = None) -> dict:
        f = FormReader(form)
        data = {
            "supplier_id": f.integer("supplier_id", "Nhà cung cấp", required=True, min_value=1),
            "reference_no": f.text("reference_no", "Số báo giá", max_len=100),
            "product_name": f.text("product_name", "Tên sản phẩm", required=True, max_len=200, collapse=True),
            "specifications": f.text("specifications", "Thông số, chất lượng", max_len=2000),
            "unit": f.text("unit", "Đơn vị tính", required=True, max_len=30, collapse=True),
            "unit_price": f.decimal("unit_price", "Đơn giá", required=True, min_exclusive=Decimal(0),
                                    max_value=MAX_NUMBER, places=6),
            "currency": f.choice("currency", "Đồng tiền", CURRENCIES, required=True, upper=True),
            "moq": f.decimal("moq", "MOQ", min_exclusive=Decimal(0), max_value=MAX_NUMBER, places=3),
            "incoterm": f.choice("incoterm", "Incoterms", INCOTERMS, upper=True),
            "incoterm_place": f.text("incoterm_place", "Địa điểm giao hàng", max_len=100),
            "payment_terms": f.text("payment_terms", "Điều kiện thanh toán", max_len=300),
            "lead_time_days": f.integer("lead_time_days", "Thời gian giao hàng", min_value=0, max_value=1000),
            "quote_date": f.day("quote_date", "Ngày báo giá", required=True),
            "valid_until": f.day("valid_until", "Hiệu lực đến"),
            "notes": f.text("notes", "Ghi chú", max_len=2000),
        }
        if data["supplier_id"] and "supplier_id" not in f.errors:
            supplier = self.suppliers.find(data["supplier_id"])
            if supplier is None:
                f.fail("supplier_id", "Nhà cung cấp không tồn tại.")
            elif not supplier.is_active and (existing is None or existing.supplier_id != supplier.id):
                f.fail("supplier_id", "Nhà cung cấp này đã được lưu trữ. Hãy khôi phục trước khi thêm báo giá mới.")
        if data["quote_date"] and data["valid_until"] and data["valid_until"] < data["quote_date"]:
            f.fail("valid_until", "Hiệu lực đến phải cùng ngày hoặc sau ngày báo giá.")
        if f.errors:
            raise ValidationError(f.errors)
        return data

    # ---- ghi ----
    def create(self, form) -> Quotation:
        data = self.clean(form)
        with self.db:
            quotation_id = repo.insert(self.db, data)
        return self.get(quotation_id)

    def update(self, quotation_id: int, form) -> Quotation:
        existing = self.get(quotation_id)
        data = self.clean(form, existing)
        with self.db:
            repo.update(self.db, quotation_id, data)
        return self.get(quotation_id)

    def delete(self, quotation_id: int) -> None:
        self.get(quotation_id)
        with self.db:
            repo.delete(self.db, quotation_id)
