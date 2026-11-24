from flask import Blueprint

from tradeflow.core.module import ModuleInfo

bp = Blueprint("comparison", __name__, url_prefix="/comparison")


@bp.get("")
def index():
    return "Đang xây dựng ở giai đoạn 3."


module = ModuleInfo(key="comparison", label="So sánh", path="/comparison", blueprint=bp)
