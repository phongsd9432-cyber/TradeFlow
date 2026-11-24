from datetime import date, timedelta
from decimal import Decimal

from tradeflow.core.errors import ConflictError, NotFoundError, ValidationError
from tradeflow.modules.quotations.service import QuotationService, validity_of
from tradeflow.modules.suppliers.service import SupplierService

from .base import AppTestCase, supplier_form


def quote_form(supplier_id=1, **overrides) -> dict:
    base = {
        "supplier_id": str(supplier_id), "product_name": "Sợi cotton 40s", "unit": "kg",
        "unit_price": "2.35", "currency": "usd", "quote_date": "2026-11-20",
    }
    return {**base, **overrides}


class QuotationServiceTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.suppliers = SupplierService(self.db)
        self.supplier = self.suppliers.create(supplier_form())
        self.svc = QuotationService(self.db)

    def test_tao_va_luu_chinh_xac_so_thap_phan(self):
        q = self.svc.create(quote_form(unit_price="0.004200", moq="2500.5", incoterm="fob",
                                       lead_time_days="30", valid_until="2026-12-31"))
        self.assertEqual(q.unit_price, Decimal("0.004200"))
        self.assertEqual(q.moq, Decimal("2500.5"))
        self.assertEqual((q.currency, q.incoterm, q.lead_time_days), ("USD", "FOB", 30))
        self.assertEqual(q.valid_until, date(2026, 12, 31))
        self.assertEqual(q.supplier_name, "Công ty Đại Phát")

    def test_cac_truong_bat_buoc(self):
        with self.assertRaises(ValidationError) as ctx:
            self.svc.create({})
        self.assertEqual(set(ctx.exception.errors),
                         {"supplier_id", "product_name", "unit", "unit_price", "currency", "quote_date"})

    def test_gia_phai_duong_va_khong_dung_dau_phay(self):
        for bad in ("0", "-5", "12,5", "abc"):
            with self.assertRaises(ValidationError, msg=bad) as ctx:
                self.svc.create(quote_form(unit_price=bad))
            self.assertIn("unit_price", ctx.exception.errors)

    def test_tien_te_incoterm_khong_hop_le(self):
        with self.assertRaises(ValidationError) as ctx:
            self.svc.create(quote_form(currency="XXX", incoterm="ABC", lead_time_days="-3"))
        self.assertEqual(set(ctx.exception.errors), {"currency", "incoterm", "lead_time_days"})

    def test_hieu_luc_khong_duoc_truoc_ngay_bao_gia(self):
        with self.assertRaises(ValidationError) as ctx:
            self.svc.create(quote_form(valid_until="2026-11-01"))
        self.assertIn("valid_until", ctx.exception.errors)

    def test_nha_cung_cap_khong_ton_tai_hoac_da_luu_tru(self):
        with self.assertRaises(ValidationError) as ctx:
            self.svc.create(quote_form(supplier_id=99))
        self.assertIn("supplier_id", ctx.exception.errors)
        q = self.svc.create(quote_form())
        self.suppliers.set_active(self.supplier.id, False)
        with self.assertRaises(ValidationError):
            self.svc.create(quote_form())  # không thêm báo giá mới cho NCC đã lưu trữ
        self.svc.update(q.id, quote_form(unit_price="3"))  # nhưng vẫn sửa được báo giá cũ
        self.assertEqual(self.svc.get(q.id).unit_price, Decimal("3"))

    def test_sua_va_xoa(self):
        q = self.svc.create(quote_form())
        q2 = self.svc.update(q.id, quote_form(unit_price="2.5", notes="Giá mới"))
        self.assertEqual((q2.unit_price, q2.notes), (Decimal("2.5"), "Giá mới"))
        self.svc.delete(q.id)
        with self.assertRaises(NotFoundError):
            self.svc.get(q.id)

    def test_form_values_de_hien_lai_khi_sua(self):
        q = self.svc.create(quote_form(unit_price="2.350", moq="1000"))
        values = self.svc.form_values(q)
        self.assertEqual((values["unit_price"], values["moq"], values["quote_date"]), ("2.35", "1000", "2026-11-20"))
        self.assertEqual(values["incoterm"], "")

    def test_hieu_luc(self):
        today = date(2026, 11, 24)
        mk = lambda d: self.svc.create(quote_form(valid_until=d.isoformat() if d else "", quote_date="2026-01-01"))
        self.assertEqual(validity_of(mk(None), today).code, "none")
        self.assertEqual(validity_of(mk(today - timedelta(days=1)), today).code, "expired")
        self.assertEqual(validity_of(mk(today), today).code, "expiring")  # hết hạn hôm nay: vẫn còn hiệu lực
        self.assertEqual(validity_of(mk(today + timedelta(days=7)), today).code, "expiring")
        self.assertEqual(validity_of(mk(today + timedelta(days=8)), today).code, "valid")
        self.assertEqual(self.svc.stats(today), {"total": 5, "expired": 1, "expiring": 2})

    def test_tim_kiem_va_loc_trang_thai(self):
        a = self.svc.create(quote_form(valid_until="2026-11-21"))
        self.svc.create(quote_form(product_name="Vải kaki", valid_until="2027-01-01"))
        today = date(2026, 11, 24)
        self.assertEqual([x.product_name for x in self.svc.search(q="soi cotton")], ["Sợi cotton 40s"])
        self.assertEqual([x.id for x in self.svc.search(status="expired", today=today)], [a.id])
        self.assertEqual(len(self.svc.search(status="active", today=today)), 1)
        self.assertEqual(len(self.svc.search(supplier_id=self.supplier.id)), 2)

    def test_gom_san_pham_khong_phan_biet_hoa_thuong_dau(self):
        other = self.suppliers.create(supplier_form(name="Seoul Textile", country="KR"))
        self.svc.create(quote_form())
        self.svc.create(quote_form(supplier_id=other.id, product_name="soi COTTON 40S", currency="CNY"))
        self.svc.create(quote_form(product_name="Vải kaki"))
        summary = self.svc.product_summary()
        self.assertEqual((summary[0].name, summary[0].quote_count, summary[0].supplier_count),
                         ("Sợi cotton 40s", 2, 2))
        self.assertEqual(summary[0].currencies, ["CNY", "USD"])
        self.assertEqual(len(self.svc.by_product("SỢI cotton 40S")), 2)
        self.assertEqual(self.svc.product_names(), ["Sợi cotton 40s", "Vải kaki"])

    def test_khong_xoa_duoc_ncc_da_co_bao_gia(self):
        self.svc.create(quote_form())
        with self.assertRaises(ConflictError):
            self.suppliers.delete(self.supplier.id)
        self.assertIsNotNone(self.suppliers.find(self.supplier.id))


class QuotationWebTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.post("/suppliers/new", supplier_form())

    def test_danh_sach_rong_va_form_goi_y_ncc(self):
        self.assertIn("Chưa có báo giá nào", self.html(self.client.get("/quotations/")))
        form = self.html(self.client.get("/quotations/new?supplier_id=1"))
        self.assertIn('value="1" selected', form)
        self.assertIn('value="' + date.today().isoformat() + '"', form)

    def test_them_xem_sua_xoa_qua_web(self):
        r = self.post("/quotations/new", quote_form(incoterm="FOB", incoterm_place="Thượng Hải"))
        self.assertEqual(r.status_code, 302)
        page = self.html(self.client.get(r.headers["Location"]))
        self.assertIn("Đã lưu báo giá", page)
        self.assertIn("2.35 USD", page)
        self.assertIn("FOB, Thượng Hải", page)
        listing = self.html(self.client.get("/quotations/"))
        self.assertIn('name="ids"', listing)
        self.assertEqual(self.post("/quotations/1/edit", quote_form(unit_price="3")).status_code, 302)
        self.assertEqual(self.post("/quotations/1/delete").status_code, 302)
        self.assertEqual(self.client.get("/quotations/1").status_code, 404)

    def test_loi_nhap_hien_thong_bao_tieng_viet(self):
        r = self.post("/quotations/new", quote_form(unit_price="12,5"))
        body = self.html(r)
        self.assertEqual(r.status_code, 422)
        self.assertIn("dùng dấu chấm", body)
        self.assertIn('value="Sợi cotton 40s"', body)  # giữ lại dữ liệu đã nhập

    def test_xss_trong_ten_san_pham(self):
        self.post("/quotations/new", quote_form(product_name='"><img src=x onerror=alert(1)>'))
        body = self.html(self.client.get("/quotations/"))
        self.assertNotIn("<img src=x", body)

    def test_bo_loc_tren_danh_sach_chap_nhan_o_trong(self):
        self.post("/quotations/new", quote_form())
        r = self.client.get("/quotations/?q=&supplier_id=&status=")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Sợi cotton 40s", self.html(r))
        self.assertIn("Không có báo giá nào khớp", self.html(self.client.get("/quotations/?q=khong-co")))
