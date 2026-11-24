-- Giai đoạn 1: bảng nhà cung cấp
CREATE TABLE suppliers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    country      TEXT NOT NULL,          -- mã quốc gia 2 chữ cái (ISO 3166), ví dụ CN, VN
    address      TEXT,
    contact_name TEXT,
    email        TEXT,
    phone        TEXT,
    website      TEXT,
    products     TEXT,                   -- sản phẩm cung cấp (mô tả tự do)
    rating       INTEGER CHECK (rating IS NULL OR rating BETWEEN 1 AND 5),
    notes        TEXT,
    is_active    INTEGER NOT NULL DEFAULT 1,   -- 0 = đã lưu trữ (ẩn, không xóa, giữ lịch sử)
    created_at   TEXT NOT NULL,          -- giờ UTC
    updated_at   TEXT NOT NULL
);
CREATE INDEX ix_suppliers_name ON suppliers (name);
