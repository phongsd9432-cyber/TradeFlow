from tradeflow.core.errors import ConflictError, NotFoundError, ValidationError
from tradeflow.modules.suppliers.service import SupplierService

from .base import AppTestCase, supplier_form


class SupplierServiceTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.svc = SupplierService(self.db)

    def test_tao_voi_thong_tin_toi_thieu(self):
        s = self.svc.create(supplier_form(country="cn"))
        self.assertEqual((s.name, s.country, s.is_active), ("Công ty Đại Phát", "CN", True))
        self.assertIsNone(s.email)

    def test_truong_bat_buoc_va_quoc_gia_la(self):
        with self.assertRaises(ValidationError) as ctx:
            self.svc.create({"name": " ", "country": "XX"})
        self.assertEqual(set(ctx.exception.errors), {"name", "country"})

    def test_email_website_danh_gia(self):
        with self.assertRaises(ValidationError) as ctx:
            self.svc.create(supplier_form(email="khong-hop-le", website="javascript:alert(1)", rating="9"))
        self.assertEqual(set(ctx.exception.errors), {"email", "website", "rating"})

    def test_website_tu_them_https(self):
        s = self.svc.create(supplier_form(website="congty.com/vi"))
        self.assertEqual(s.website, "https://congty.com/vi")

    def test_chong_trung_cung_ten_cung_quoc_gia(self):
        self.svc.create(supplier_form())
        with self.assertRaises(ValidationError) as ctx:
            self.svc.create(supplier_form(name="cong ty  DAI phat"))  # khác hoa/thường, dấu
        self.assertIn("name", ctx.exception.errors)
        self.svc.create(supplier_form(country="VN"))  # cùng tên khác nước: cho phép

    def test_sua_giu_nguyen_ten_khong_bi_coi_la_trung(self):
        s = self.svc.create(supplier_form())
        s2 = self.svc.update(s.id, supplier_form(phone="0123"))
        self.assertEqual(s2.phone, "0123")
        self.assertGreaterEqual(s2.updated_at, s.updated_at)

    def test_luu_tru_va_khoi_phuc(self):
        s = self.svc.create(supplier_form())
        self.svc.set_active(s.id, False)
        self.assertEqual(self.svc.search(), [])
        self.assertEqual(len(self.svc.search(include_archived=True)), 1)
        self.assertEqual(self.svc.counts(), {"active": 0, "archived": 1})
        self.svc.set_active(s.id, True)
        self.assertEqual(len(self.svc.search()), 1)

    def test_tim_kiem_khong_dau_va_loc_quoc_gia(self):
        self.svc.create(supplier_form(products="Sợi cotton 40s"))
        self.svc.create(supplier_form(name="Seoul Textile", country="KR"))
        self.assertEqual([s.name for s in self.svc.search(q="cong ty dai")], ["Công ty Đại Phát"])
        self.assertEqual([s.name for s in self.svc.search(q="soi cotton")], ["Công ty Đại Phát"])
        self.assertEqual([s.name for s in self.svc.search(country="KR")], ["Seoul Textile"])
        self.assertEqual([s.name for s in self.svc.search(q="hàn quốc")], ["Seoul Textile"])

    def test_xoa_va_khong_tim_thay(self):
        s = self.svc.create(supplier_form())
        self.svc.delete(s.id)
        with self.assertRaises(NotFoundError):
            self.svc.get(s.id)
        with self.assertRaises(NotFoundError):
            self.svc.delete(s.id)


class SupplierWebTests(AppTestCase):
    def test_danh_sach_rong_co_loi_moi(self):
        r = self.client.get("/suppliers")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Chưa có nhà cung cấp nào", self.html(r))

    def test_them_moi_chuyen_huong_va_hien_thong_bao(self):
        r = self.post("/suppliers/new", supplier_form())
        self.assertEqual(r.status_code, 302)
        page = self.client.get(r.headers["Location"])
        self.assertIn("Đã thêm nhà cung cấp", self.html(page))
        self.assertIn("Công ty Đại Phát", self.html(page))

    def test_loi_nhap_giu_lai_du_lieu_va_tra_422(self):
        r = self.post("/suppliers/new", supplier_form(email="sai", phone="0909"))
        body = self.html(r)
        self.assertEqual(r.status_code, 422)
        self.assertIn("Email không hợp lệ", body)
        self.assertIn('value="0909"', body)

    def test_ten_chua_ma_doc_duoc_thoat_an_toan(self):
        self.post("/suppliers/new", supplier_form(name="<script>alert(1)</script>"))
        body = self.html(self.client.get("/suppliers"))
        self.assertNotIn("<script>alert(1)</script>", body)
        self.assertIn("&lt;script&gt;", body)

    def test_404_va_duong_dan_sai(self):
        self.assertEqual(self.client.get("/suppliers/999").status_code, 404)
        self.assertEqual(self.client.get("/suppliers/abc").status_code, 404)
        self.assertIn("Không tìm thấy", self.html(self.client.get("/suppliers/999")))

    def test_sua_luu_tru_khoi_phuc_xoa_qua_web(self):
        self.post("/suppliers/new", supplier_form())
        self.assertEqual(self.client.get("/suppliers/1/edit").status_code, 200)
        self.assertEqual(self.post("/suppliers/1/edit", supplier_form(phone="555")).status_code, 302)
        self.post("/suppliers/1/archive")
        self.assertIn("Đã lưu trữ", self.html(self.client.get("/suppliers/1")))
        self.assertNotIn("Công ty Đại Phát", self.html(self.client.get("/suppliers")))
        self.post("/suppliers/1/restore")
        self.assertEqual(self.post("/suppliers/1/delete").status_code, 302)
        self.assertEqual(self.client.get("/suppliers/1").status_code, 404)


class SecurityTests(AppTestCase):
    def test_chan_form_gui_tu_trang_la(self):
        r = self.post("/suppliers/new", supplier_form(), headers={"Origin": "http://trang-la.example"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0], 0)

    def test_cho_phep_form_cung_nguon(self):
        r = self.post("/suppliers/new", supplier_form(), headers={"Origin": "http://localhost"})
        self.assertEqual(r.status_code, 302)

    def test_header_bao_mat(self):
        r = self.client.get("/suppliers")
        self.assertIn("default-src 'self'", r.headers["Content-Security-Policy"])
        self.assertEqual(r.headers["X-Frame-Options"], "DENY")
