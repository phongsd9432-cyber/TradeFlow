import unittest
from datetime import date
from decimal import Decimal as D

from tradeflow.modules.comparison.service import build_comparison
from tradeflow.modules.quotations.models import Quotation

from .base import AppTestCase, supplier_form
from .test_quotations import quote_form

TODAY = date(2026, 11, 24)


def mk(id, price="10", currency="USD", unit="kg", supplier="NCC", moq=None, incoterm="FOB", lead=None,
       valid=None, rating=None, product="Cotton", payment="T/T 30 ngày") -> Quotation:
    return Quotation(
        id=id, supplier_id=id, reference_no=None, product_name=product, specifications=None, unit=unit,
        unit_price=D(price), currency=currency, moq=D(moq) if moq else None, incoterm=incoterm,
        incoterm_place=None, payment_terms=payment, lead_time_days=lead, quote_date=date(2026, 11, 1),
        valid_until=valid, notes=None, created_at="", updated_at="", supplier_name=f"{supplier}{id}",
        supplier_country="CN", supplier_rating=rating,
    )


def compare(quotes, **kw):
    return build_comparison(quotes, today=TODAY, **kw)


def texts(c):
    return " | ".join(w.text for w in c.warnings)


class RankingTests(unittest.TestCase):
    def test_cung_dong_tien_xep_hang_va_phan_tram(self):
        c = compare([mk(1, "10"), mk(2, "8"), mk(3, "12")])
        self.assertEqual([r.quote.id for r in c.rows], [2, 1, 3])
        self.assertEqual([r.rank for r in c.rows], [1, 2, 3])
        self.assertEqual([r.premium_pct for r in c.rows], [D("0.0"), D("25.0"), D("50.0")])
        self.assertEqual(c.rows[0].best, {"price"})
        self.assertTrue(c.price_comparable)
        self.assertEqual(c.target, "USD")

    def test_gia_bang_nhau_dong_hang_va_cung_duoc_danh_dau(self):
        c = compare([mk(1, "5"), mk(2, "5"), mk(3, "6")])
        self.assertEqual([r.rank for r in c.rows], [1, 1, 3])
        self.assertEqual([("price" in r.best) for r in c.rows], [True, True, False])

    def test_tat_ca_bang_nhau_khong_danh_dau_va_mot_bao_gia_co_canh_bao(self):
        c = compare([mk(1, "5"), mk(2, "5")])
        self.assertTrue(all(not r.best for r in c.rows))
        c1 = compare([mk(1)])
        self.assertIn("Mới có 1 báo giá", texts(c1))
        self.assertFalse(c1.rows[0].best)

    def test_khac_tien_te_thieu_ty_gia_thi_khong_xep_hang_bua(self):
        c = compare([mk(1, "10", "USD"), mk(2, "70", "CNY")], target_currency="CNY")
        self.assertEqual(c.missing_rates, ["USD"])
        by_id = {r.quote.id: r for r in c.rows}
        self.assertIsNone(by_id[1].converted_price)
        self.assertIsNone(by_id[1].rank)
        self.assertEqual(by_id[2].rank, 1)
        self.assertIn("Chưa có tỷ giá cho USD", texts(c))
        self.assertEqual([r.quote.id for r in c.rows], [2, 1])  # dòng chưa quy đổi xuống cuối

    def test_co_ty_gia_thi_quy_doi_va_xep_hang(self):
        c = compare([mk(1, "10", "USD"), mk(2, "70", "CNY")], target_currency="VND",
                    rates={"USD": D("25000"), "CNY": D("3500")})
        by_id = {r.quote.id: r for r in c.rows}
        self.assertEqual(by_id[1].converted_price, D("250000"))
        self.assertEqual(by_id[2].converted_price, D("245000"))
        self.assertEqual([r.quote.id for r in c.rows], [2, 1])
        self.assertEqual(c.missing_rates, [])
        self.assertEqual(c.rows[1].premium_pct, D("2.0"))

    def test_ty_gia_khong_hop_le_bi_bo_qua(self):
        c = compare([mk(1, "10", "USD"), mk(2, "70", "CNY")], target_currency="CNY", rates={"USD": D("0")})
        self.assertEqual(c.missing_rates, ["USD"])

    def test_dong_tien_so_sanh_mac_dinh_la_dong_tien_pho_bien_nhat(self):
        c = compare([mk(1, currency="USD"), mk(2, currency="CNY"), mk(3, currency="CNY")])
        self.assertEqual(c.target, "CNY")


class ComparabilityTests(unittest.TestCase):
    def test_khac_don_vi_khong_xep_hang_va_canh_bao(self):
        c = compare([mk(1, unit="kg"), mk(2, unit="tấn")], quantity=D("10"))
        self.assertFalse(c.price_comparable)
        self.assertTrue(all(r.rank is None and r.total is None for r in c.rows))
        self.assertIn("Đơn vị tính khác nhau", texts(c))

    def test_don_vi_viet_hoa_thuong_khac_nhau_van_la_mot(self):
        self.assertTrue(compare([mk(1, unit="KG"), mk(2, unit="kg")]).price_comparable)

    def test_khac_incoterms_canh_bao(self):
        self.assertIn("Incoterms", texts(compare([mk(1, incoterm="FOB"), mk(2, incoterm="CIF")])))
        self.assertIn("chưa ghi", texts(compare([mk(1, incoterm="FOB"), mk(2, incoterm=None)])))
        self.assertNotIn("Incoterms", texts(compare([mk(1, incoterm="FOB"), mk(2, incoterm="FOB")])))

    def test_khac_ten_san_pham_canh_bao(self):
        self.assertIn("2 tên sản phẩm khác nhau", texts(compare([mk(1, product="A"), mk(2, product="B")])))
        self.assertNotIn("tên sản phẩm", texts(compare([mk(1, product="Sợi"), mk(2, product="SOI")])))


class QuantityAndValidityTests(unittest.TestCase):
    def test_tong_gia_tri_va_moq(self):
        c = compare([mk(1, "2", moq="1000"), mk(2, "3", moq="100")], quantity=D("500"))
        by_id = {r.quote.id: r for r in c.rows}
        self.assertEqual(by_id[1].total, D("1000"))
        self.assertTrue(by_id[1].moq_short)
        self.assertFalse(by_id[2].moq_short)
        self.assertIn("MOQ", texts(c))
        self.assertIn("moq", by_id[2].best)

    def test_khong_nhap_so_luong_thi_nhac_nhap(self):
        c = compare([mk(1), mk(2, "9")])
        self.assertIn("Nhập số lượng dự kiến", texts(c))
        self.assertTrue(all(r.total is None for r in c.rows))

    def test_het_han_va_sap_het_han(self):
        c = compare([mk(1, valid=date(2026, 11, 1)), mk(2, valid=date(2026, 11, 26)), mk(3, valid=date(2027, 3, 1))])
        by_id = {r.quote.id: r for r in c.rows}
        self.assertEqual([by_id[i].validity.code for i in (1, 2, 3)], ["expired", "expiring", "valid"])
        self.assertTrue(any(f.level == "warn" for f in by_id[1].flags))
        self.assertIn("1 báo giá đã hết hạn", texts(c))

    def test_tieu_chi_khac_giao_hang_nhanh_danh_gia_cao_thieu_thong_tin(self):
        c = compare([mk(1, lead=10, rating=3), mk(2, lead=20, rating=5), mk(3, incoterm=None, payment=None)])
        by_id = {r.quote.id: r for r in c.rows}
        self.assertIn("lead_time", by_id[1].best)
        self.assertIn("rating", by_id[2].best)
        self.assertEqual(by_id[3].missing, ["Incoterms", "MOQ", "Thanh toán", "Thời gian giao", "Hiệu lực"])
        self.assertEqual(by_id[1].missing, ["MOQ", "Hiệu lực"])

    def test_thoi_gian_giao_bang_khong_van_hop_le(self):
        c = compare([mk(1, lead=0), mk(2, lead=5)])
        self.assertNotIn("Thời gian giao", {m for r in c.rows for m in r.missing})
        self.assertIn("lead_time", {r.quote.id: r for r in c.rows}[1].best)


class ComparisonWebTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.post("/suppliers/new", supplier_form(name="Đại Phát", rating="4"))
        self.post("/suppliers/new", supplier_form(name="Seoul Textile", country="KR"))
        self.post("/quotations/new", quote_form(1, unit_price="2.5", incoterm="FOB", lead_time_days="30"))
        self.post("/quotations/new", quote_form(2, unit_price="2.2", incoterm="FOB", lead_time_days="45",
                                                product_name="SỢI COTTON 40S"))
        self.post("/quotations/new", quote_form(2, unit_price="9", product_name="Vải kaki"))

    def test_trang_chon_san_pham(self):
        body = self.html(self.client.get("/comparison"))
        self.assertIn("Sợi cotton 40s", body)
        self.assertIn("Cần thêm báo giá", body)  # Vải kaki chỉ có 1 báo giá

    def test_so_sanh_theo_san_pham_gom_khong_phan_biet_hoa_thuong(self):
        r = self.client.get("/comparison?product=s%E1%BB%A3i+cotton+40s")
        body = self.html(r)
        self.assertEqual(r.status_code, 200)
        self.assertIn("Đại Phát", body)
        self.assertIn("Seoul Textile", body)
        self.assertIn("Thấp nhất", body)
        self.assertNotIn("Vải kaki", body)

    def test_so_sanh_theo_ids_va_tong_gia_tri(self):
        body = self.html(self.client.get("/comparison?ids=1&ids=2&quantity=1000&target=USD"))
        self.assertIn("2" + "\u00a0" + "200.00 USD", body)  # 1000 x 2.2
        self.assertIn("2" + "\u00a0" + "500.00 USD", body)

    def test_chon_it_hon_2_bao_gia_bi_nhac(self):
        r = self.client.get("/comparison?ids=1", follow_redirects=True)
        self.assertIn("ít nhất 2 báo giá", self.html(r))

    def test_ty_gia_sai_hien_loi_va_ty_gia_dung_duoc_ap_dung(self):
        self.post("/quotations/new", quote_form(1, unit_price="60", currency="CNY"))
        bad = self.html(self.client.get("/comparison?product=Sợi+cotton+40s&target=CNY&rate_USD=25,5"))
        self.assertIn("dùng dấu chấm", bad)
        ok = self.html(self.client.get("/comparison?product=Sợi+cotton+40s&target=CNY&rate_USD=7"))
        self.assertIn("1 USD bằng bao nhiêu CNY", ok)
        self.assertNotIn("Thiếu tỷ giá", ok)

    def test_san_pham_khong_ton_tai_quay_ve_trang_chon(self):
        r = self.client.get("/comparison?product=khong-co", follow_redirects=True)
        self.assertIn("Không tìm thấy báo giá nào", self.html(r))


class DashboardTests(AppTestCase):
    def test_tong_quan_dem_dung(self):
        self.post("/suppliers/new", supplier_form())
        self.post("/quotations/new", quote_form(1, valid_until="2026-11-21"))
        body = self.html(self.client.get("/"))
        self.assertIn("Nhà cung cấp đang hoạt động", body)
        self.assertIn("<b>1</b><span>Nhà cung cấp", body)
        self.assertEqual(self.client.get("/").status_code, 200)
