"""Trang tổng quan. Nằm trên cùng sơ đồ phụ thuộc: được phép đọc mọi module khác."""
from flask import Blueprint, render_template

from tradeflow.core.db import get_db
from tradeflow.core.module import ModuleInfo
from tradeflow.modules.quotations.service import QuotationService
from tradeflow.modules.suppliers.service import SupplierService

bp = Blueprint("dashboard", __name__, template_folder="templates")


@bp.get("/")
def home():
    db = get_db()
    return render_template("dashboard/home.html", suppliers=SupplierService(db).counts(),
                           quotes=QuotationService(db).stats())


module = ModuleInfo(key="dashboard", label="Tổng quan", path="/", blueprint=bp)
