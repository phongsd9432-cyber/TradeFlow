import os
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from tradeflow.core.config import Settings, load_dotenv
from tradeflow.core.db import connect, run_migrations
from tradeflow.core.forms import FormReader
from tradeflow.core.text import fold, format_number, plain_number


class TextTests(unittest.TestCase):
    def test_fold_bo_dau_va_chu_hoa(self):
        self.assertEqual(fold("Công ty ĐẠI  Phát"), "cong ty dai phat")
        self.assertEqual(fold(None), "")

    def test_format_number(self):
        nbsp = "\u00a0"
        self.assertEqual(format_number(Decimal("1234567.5")), f"1{nbsp}234{nbsp}567.5")
        self.assertEqual(format_number(Decimal("12.5"), min_decimals=2), "12.50")
        self.assertEqual(format_number(Decimal("0.004200"), min_decimals=2), "0.0042")
        self.assertEqual(format_number(Decimal("5000.000")), f"5{nbsp}000")
        self.assertEqual(format_number(Decimal("2.345"), min_decimals=2, max_decimals=2), "2.35")
        self.assertEqual(format_number(None), "—")

    def test_plain_number(self):
        self.assertEqual(plain_number(Decimal("12.500")), "12.5")
        self.assertEqual(plain_number(Decimal("100")), "100")
        self.assertEqual(plain_number(None), "")


class FormReaderTests(unittest.TestCase):
    def read(self, **data):
        return FormReader(data)

    def test_decimal_hop_le(self):
        f = self.read(price="12.5", tiny=".5")
        self.assertEqual(f.decimal("price", "Đơn giá"), Decimal("12.5"))
        self.assertEqual(f.decimal("tiny", "X"), Decimal("0.5"))
        self.assertFalse(f.errors)

    def test_decimal_tu_choi_dau_phay_va_so_am(self):
        f = self.read(a="12,5", b="-3", c="abc", d="1e5")
        for key in "abcd":
            self.assertIsNone(f.decimal(key, "Giá trị"))
        self.assertEqual(set(f.errors), set("abcd"))

    def test_decimal_gioi_han(self):
        f = self.read(a="0", b="1.1234567", c="5")
        f.decimal("a", "A", min_exclusive=Decimal(0))
        f.decimal("b", "B", places=6)
        f.decimal("c", "C", max_value=Decimal(4))
        self.assertEqual(set(f.errors), {"a", "b", "c"})

    def test_bat_buoc_va_do_dai(self):
        f = self.read(name="  ", long="x" * 11)
        f.text("name", "Tên", required=True)
        f.text("long", "Mô tả", max_len=10)
        self.assertEqual(f.errors["name"], "Tên là bắt buộc.")
        self.assertIn("tối đa 10", f.errors["long"])

    def test_ngay_va_so_nguyen_va_lua_chon(self):
        f = self.read(d="2026-11-24", bad="24/11/2026", old="0202-01-01", n="12", neg="-1", c="usd")
        self.assertEqual(f.day("d", "Ngày").isoformat(), "2026-11-24")
        self.assertIsNone(f.day("bad", "Ngày"))
        self.assertIsNone(f.day("old", "Ngày"))
        self.assertEqual(f.integer("n", "N"), 12)
        self.assertIsNone(f.integer("neg", "N"))
        self.assertEqual(f.choice("c", "Tiền", ["USD"], upper=True), "USD")
        self.assertEqual(set(f.errors), {"bad", "old", "neg"})


class ConfigTests(unittest.TestCase):
    def test_settings_tu_bien_moi_truong(self):
        old = dict(os.environ)
        try:
            os.environ.update(TRADEFLOW_PORT="9100", TRADEFLOW_DEBUG="1", TRADEFLOW_DATABASE_PATH="x/y.db")
            s = Settings.from_env()
            self.assertEqual((s.port, s.debug, s.database_path), (9100, True, "x/y.db"))
            self.assertEqual(s.host, "127.0.0.1")  # mặc định chỉ chạy trên máy này
        finally:
            os.environ.clear()
            os.environ.update(old)

    def test_load_dotenv_khong_de_len_bien_co_san(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text('# ghi chú\nTF_TEST_A=1\nTF_TEST_B="hai"\nTF_TEST_C=3\n', encoding="utf-8")
            os.environ["TF_TEST_C"] = "co-san"
            try:
                load_dotenv(env_file)
                self.assertEqual(os.environ["TF_TEST_A"], "1")
                self.assertEqual(os.environ["TF_TEST_B"], "hai")
                self.assertEqual(os.environ["TF_TEST_C"], "co-san")
            finally:
                for k in ("TF_TEST_A", "TF_TEST_B", "TF_TEST_C"):
                    os.environ.pop(k, None)


class MigrationTests(unittest.TestCase):
    def test_chay_lai_khong_loi_va_khong_lap(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = connect(str(Path(tmp) / "m.db"))
            first = run_migrations(conn)
            self.assertIn("0001_suppliers", first)
            self.assertEqual(run_migrations(conn), [])
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertIn("suppliers", tables)
            conn.close()

    def test_migration_loi_duoc_hoan_tac(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "mig"
            d.mkdir()
            (d / "0001_ok.sql").write_text("CREATE TABLE a (id INTEGER);", encoding="utf-8")
            (d / "0002_hong.sql").write_text("CREATE TABLE b (id INTEGER); CREATE TABLE b (id INTEGER);", encoding="utf-8")
            conn = connect(str(Path(tmp) / "m.db"))
            with self.assertRaises(Exception):
                run_migrations(conn, d)
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertIn("a", tables)
            self.assertNotIn("b", tables)  # file hỏng bị hoàn tác hoàn toàn
            self.assertEqual([r[0] for r in conn.execute("SELECT version FROM schema_migrations")], ["0001_ok"])
            conn.close()


if __name__ == "__main__":
    unittest.main()
