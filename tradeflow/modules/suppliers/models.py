from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Supplier:
    id: int
    name: str
    country: str
    address: str | None
    contact_name: str | None
    email: str | None
    phone: str | None
    website: str | None
    products: str | None
    rating: int | None
    notes: str | None
    is_active: bool
    created_at: str
    updated_at: str
