"""Truy cập dữ liệu nhà cung cấp: nơi DUY NHẤT chứa SQL của module này."""
from __future__ import annotations

import sqlite3

from tradeflow.core.clock import utcnow_iso

from .models import Supplier

FIELDS = ("name", "country", "address", "contact_name", "email", "phone", "website",
          "products", "rating", "notes")


def _to_supplier(row: sqlite3.Row) -> Supplier:
    data = dict(row)
    data["is_active"] = bool(data["is_active"])
    return Supplier(**data)


def get(db: sqlite3.Connection, supplier_id: int) -> Supplier | None:
    row = db.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
    return _to_supplier(row) if row else None


def list_all(db: sqlite3.Connection, include_archived: bool = False) -> list[Supplier]:
    sql = "SELECT * FROM suppliers"
    if not include_archived:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY name COLLATE NOCASE, id"
    return [_to_supplier(r) for r in db.execute(sql)]


def insert(db: sqlite3.Connection, data: dict) -> int:
    now = utcnow_iso()
    cols = ", ".join(FIELDS)
    marks = ", ".join("?" for _ in FIELDS)
    cur = db.execute(
        f"INSERT INTO suppliers ({cols}, is_active, created_at, updated_at) VALUES ({marks}, 1, ?, ?)",
        [data[f] for f in FIELDS] + [now, now],
    )
    return cur.lastrowid


def update(db: sqlite3.Connection, supplier_id: int, data: dict) -> None:
    sets = ", ".join(f"{f} = ?" for f in FIELDS)
    db.execute(
        f"UPDATE suppliers SET {sets}, updated_at = ? WHERE id = ?",
        [data[f] for f in FIELDS] + [utcnow_iso(), supplier_id],
    )


def set_active(db: sqlite3.Connection, supplier_id: int, active: bool) -> None:
    db.execute("UPDATE suppliers SET is_active = ?, updated_at = ? WHERE id = ?",
               (1 if active else 0, utcnow_iso(), supplier_id))


def delete(db: sqlite3.Connection, supplier_id: int) -> None:
    db.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))


def count(db: sqlite3.Connection, active: bool) -> int:
    return db.execute("SELECT COUNT(*) FROM suppliers WHERE is_active = ?", (1 if active else 0,)).fetchone()[0]
