"""Truy cập dữ liệu báo giá: nơi DUY NHẤT chứa SQL của module này."""
from __future__ import annotations

import sqlite3
from datetime import date
from decimal import Decimal

from tradeflow.core.clock import utcnow_iso

from .models import Quotation

FIELDS = ("supplier_id", "reference_no", "product_name", "specifications", "unit", "unit_price",
          "currency", "moq", "incoterm", "incoterm_place", "payment_terms", "lead_time_days",
          "quote_date", "valid_until", "notes")

_SELECT = (
    "SELECT q.*, s.name AS supplier_name, s.country AS supplier_country, "
    "s.rating AS supplier_rating, s.is_active AS supplier_active "
    "FROM quotations q JOIN suppliers s ON s.id = q.supplier_id"
)


def _to_quotation(row: sqlite3.Row) -> Quotation:
    d = dict(row)
    d["unit_price"] = Decimal(d["unit_price"])
    d["moq"] = Decimal(d["moq"]) if d["moq"] else None
    d["quote_date"] = date.fromisoformat(d["quote_date"])
    d["valid_until"] = date.fromisoformat(d["valid_until"]) if d["valid_until"] else None
    d["supplier_active"] = bool(d["supplier_active"])
    return Quotation(**d)


def _db_value(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    return value


def get(db: sqlite3.Connection, quotation_id: int) -> Quotation | None:
    row = db.execute(_SELECT + " WHERE q.id = ?", (quotation_id,)).fetchone()
    return _to_quotation(row) if row else None


def list_all(db: sqlite3.Connection, supplier_id: int | None = None) -> list[Quotation]:
    sql, params = _SELECT, []
    if supplier_id is not None:
        sql += " WHERE q.supplier_id = ?"
        params.append(supplier_id)
    sql += " ORDER BY q.quote_date DESC, q.id DESC"
    return [_to_quotation(r) for r in db.execute(sql, params)]


def list_by_ids(db: sqlite3.Connection, ids: list[int]) -> list[Quotation]:
    if not ids:
        return []
    marks = ", ".join("?" for _ in ids)
    rows = db.execute(_SELECT + f" WHERE q.id IN ({marks}) ORDER BY q.id", ids)
    return [_to_quotation(r) for r in rows]


def insert(db: sqlite3.Connection, data: dict) -> int:
    now = utcnow_iso()
    cols = ", ".join(FIELDS)
    marks = ", ".join("?" for _ in FIELDS)
    cur = db.execute(
        f"INSERT INTO quotations ({cols}, created_at, updated_at) VALUES ({marks}, ?, ?)",
        [_db_value(data[f]) for f in FIELDS] + [now, now],
    )
    return cur.lastrowid


def update(db: sqlite3.Connection, quotation_id: int, data: dict) -> None:
    sets = ", ".join(f"{f} = ?" for f in FIELDS)
    db.execute(
        f"UPDATE quotations SET {sets}, updated_at = ? WHERE id = ?",
        [_db_value(data[f]) for f in FIELDS] + [utcnow_iso(), quotation_id],
    )


def delete(db: sqlite3.Connection, quotation_id: int) -> None:
    db.execute("DELETE FROM quotations WHERE id = ?", (quotation_id,))
