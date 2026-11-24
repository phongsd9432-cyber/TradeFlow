-- Giai đoạn 2: bảng báo giá
-- Tiền và số lượng lưu dạng CHUỖI thập phân (vd '0.0042') để không bao giờ sai số làm tròn.
CREATE TABLE quotations (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id    INTEGER NOT NULL REFERENCES suppliers (id) ON DELETE RESTRICT,
    reference_no   TEXT,                 -- số báo giá do nhà cung cấp cấp
    product_name   TEXT NOT NULL,
    specifications TEXT,                 -- chất lượng, thông số
    unit           TEXT NOT NULL,        -- đơn vị tính của đơn giá và MOQ (kg, cái, tấn...)
    unit_price     TEXT NOT NULL,
    currency       TEXT NOT NULL,        -- mã ISO 4217: USD, CNY, VND...
    moq            TEXT,
    incoterm       TEXT,                 -- mã Incoterms 2020: FOB, CIF...
    incoterm_place TEXT,                 -- địa điểm đi kèm Incoterms (vd: cảng Thượng Hải)
    payment_terms  TEXT,
    lead_time_days INTEGER,
    quote_date     TEXT NOT NULL,        -- YYYY-MM-DD
    valid_until    TEXT,                 -- YYYY-MM-DD
    notes          TEXT,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    CHECK (CAST(unit_price AS REAL) > 0)
);
CREATE INDEX ix_quotations_supplier ON quotations (supplier_id);
CREATE INDEX ix_quotations_product ON quotations (product_name COLLATE NOCASE);
