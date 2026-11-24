"""Nghiệp vụ nhà cung cấp: kiểm tra dữ liệu, chống trùng, lưu trữ."""
from __future__ import annotations

import re
import sqlite3
from urllib.parse import urlsplit

from tradeflow.core.errors import ConflictError, NotFoundError, ValidationError
from tradeflow.core.forms import FormReader
from tradeflow.core.reference_data import COUNTRIES
from tradeflow.core.text import fold

from . import repository as repo
from .models import Supplier

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_website(value: str) -> str | None:
    """Thêm https:// nếu thiếu; chỉ chấp nhận http/https (chặn javascript: và các dạng nguy hiểm)."""
    candidate = value if "://" in value else "https://" + value
    try:
        parts = urlsplit(candidate)
        parts.port  # noqa: B018 - kiểm tra cổng hợp lệ
    except ValueError:
        return None
    if parts.scheme not in ("http", "https") or not parts.hostname or " " in candidate:
        return None
    return candidate


class SupplierService:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    # ---- đọc ----
    def find(self, supplier_id: int) -> Supplier | None:
        return repo.get(self.db, supplier_id)

    def get(self, supplier_id: int) -> Supplier:
        supplier = repo.get(self.db, supplier_id)
        if supplier is None:
            raise NotFoundError("Không tìm thấy nhà cung cấp này.")
        return supplier

    def active_options(self) -> list[Supplier]:
        return repo.list_all(self.db, include_archived=False)

    def search(self, *, q: str = "", country: str = "", include_archived: bool = False) -> list[Supplier]:
        items = repo.list_all(self.db, include_archived)
        if country:
            items = [s for s in items if s.country == country]
        needle = fold(q)
        if needle:
            def haystack(s: Supplier) -> str:
                parts = [s.name, s.products, s.contact_name, s.email, COUNTRIES.get(s.country, "")]
                return fold(" ".join(p for p in parts if p))
            items = [s for s in items if needle in haystack(s)]
        return items

    def counts(self) -> dict[str, int]:
        return {"active": repo.count(self.db, True), "archived": repo.count(self.db, False)}

    @staticmethod
    def form_values(s: Supplier) -> dict[str, str]:
        return {f: ("" if getattr(s, f) is None else str(getattr(s, f))) for f in repo.FIELDS}

    # ---- kiểm tra dữ liệu ----
    def clean(self, form, exclude_id: int | None = None) -> dict:
        f = FormReader(form)
        data = {
            "name": f.text("name", "Tên nhà cung cấp", required=True, max_len=200, collapse=True),
            "country": f.choice("country", "Quốc gia", COUNTRIES, required=True, upper=True),
            "address": f.text("address", "Địa chỉ", max_len=500),
            "contact_name": f.text("contact_name", "Người liên hệ", max_len=120),
            "email": f.text("email", "Email", max_len=200),
            "phone": f.text("phone", "Điện thoại", max_len=50),
            "website": f.text("website", "Website", max_len=300),
            "products": f.text("products", "Sản phẩm cung cấp", max_len=2000),
            "rating": f.integer("rating", "Đánh giá nội bộ", min_value=1, max_value=5),
            "notes": f.text("notes", "Ghi chú", max_len=2000),
        }
        if data["email"] and not _EMAIL.match(data["email"]):
            f.fail("email", "Email không hợp lệ (ví dụ: ten@congty.com).")
        if data["website"]:
            site = _normalize_website(data["website"])
            if site is None:
                f.fail("website", "Website không hợp lệ (ví dụ: https://congty.com).")
            data["website"] = site
        if data["name"] and data["country"] and not f.errors:
            key = fold(data["name"])
            for other in repo.list_all(self.db, include_archived=True):
                if other.id != exclude_id and other.country == data["country"] and fold(other.name) == key:
                    f.fail("name", "Nhà cung cấp này (cùng tên, cùng quốc gia) đã có trong danh sách.")
                    break
        if f.errors:
            raise ValidationError(f.errors)
        return data

    # ---- ghi ----
    def create(self, form) -> Supplier:
        data = self.clean(form)
        with self.db:
            supplier_id = repo.insert(self.db, data)
        return self.get(supplier_id)

    def update(self, supplier_id: int, form) -> Supplier:
        self.get(supplier_id)
        data = self.clean(form, exclude_id=supplier_id)
        with self.db:
            repo.update(self.db, supplier_id, data)
        return self.get(supplier_id)

    def set_active(self, supplier_id: int, active: bool) -> Supplier:
        self.get(supplier_id)
        with self.db:
            repo.set_active(self.db, supplier_id, active)
        return self.get(supplier_id)

    def delete(self, supplier_id: int) -> None:
        """Chỉ xóa được nhà cung cấp chưa có báo giá; CSDL tự chặn nếu đã có (khóa ngoại RESTRICT)."""
        self.get(supplier_id)
        try:
            with self.db:
                repo.delete(self.db, supplier_id)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(
                "Nhà cung cấp này đã có báo giá nên không thể xóa. "
                "Hãy dùng “Lưu trữ” để ẩn khỏi danh sách và vẫn giữ lịch sử."
            ) from exc
