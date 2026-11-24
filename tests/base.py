"""Lớp nền cho các test: mỗi test có một ứng dụng và một file CSDL tạm riêng."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tradeflow.app import create_app
from tradeflow.core.config import Settings
from tradeflow.core.db import connect


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str(Path(self._tmp.name) / "test.db")
        self.app = create_app(Settings(database_path=self.db_path, secret_key="test-key"))
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.db = connect(self.db_path)
        self.addCleanup(self.db.close)

    def post(self, url, data=None, **kwargs):
        return self.client.post(url, data=data or {}, **kwargs)

    def html(self, response) -> str:
        return response.get_data(as_text=True)


SUPPLIER_FORM = {"name": "Công ty Đại Phát", "country": "CN"}


def supplier_form(**overrides) -> dict:
    return {**SUPPLIER_FORM, **overrides}
