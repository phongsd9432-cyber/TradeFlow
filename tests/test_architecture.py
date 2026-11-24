"""Bảo vệ cấu trúc: kiểm tra tự động quy tắc phụ thuộc giữa các module (đọc import trong mã nguồn)."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tradeflow"
# module -> các module được phép dùng. Chiều phụ thuộc: core <- suppliers <- quotations <- comparison <- dashboard
ALLOWED = {
    "suppliers": set(),
    "quotations": {"suppliers"},
    "comparison": {"quotations", "suppliers"},
    "dashboard": {"suppliers", "quotations", "comparison"},
}


def imported_modules(path: Path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.module
            if node.module == "tradeflow.modules":
                for alias in node.names:
                    yield f"tradeflow.modules.{alias.name}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name


class ArchitectureTests(unittest.TestCase):
    def test_moi_module_chi_phu_thuoc_dung_chieu(self):
        for module, allowed in ALLOWED.items():
            for file in (ROOT / "modules" / module).rglob("*.py"):
                for name in imported_modules(file):
                    parts = name.split(".")
                    if parts[:2] == ["tradeflow", "modules"] and len(parts) > 2:
                        target = parts[2]
                        self.assertTrue(target == module or target in allowed,
                                        f"{file.relative_to(ROOT)}: module '{module}' không được phụ thuộc '{target}'")

    def test_moi_module_deu_duoc_khai_bao_trong_bang_kiem_tra(self):
        on_disk = {p.name for p in (ROOT / "modules").iterdir() if p.is_dir() and not p.name.startswith("__")}
        self.assertEqual(on_disk, set(ALLOWED), "Thêm module mới thì phải khai báo quy tắc phụ thuộc ở ALLOWED")

    def test_core_khong_phu_thuoc_module_nao(self):
        for file in (ROOT / "core").rglob("*.py"):
            for name in imported_modules(file):
                self.assertFalse(name.startswith("tradeflow.modules"), f"{file.name} không được import module chức năng")

    def test_sql_chi_nam_trong_repository_va_core(self):
        allowed_names = {"repository.py", "db.py"}
        for file in ROOT.rglob("*.py"):
            if file.name in allowed_names:
                continue
            text = file.read_text(encoding="utf-8")
            self.assertNotIn(".execute(", text, f"{file.relative_to(ROOT)}: SQL phải nằm trong repository.py")


if __name__ == "__main__":
    unittest.main()
