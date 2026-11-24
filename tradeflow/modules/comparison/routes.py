"""Giao diện web của module so sánh báo giá."""
from __future__ import annotations

from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for

from tradeflow.core.db import get_db
from tradeflow.core.forms import FormReader
from tradeflow.modules.quotations.service import QuotationService, validity_of

from .service import build_comparison

bp = Blueprint("comparison", __name__, url_prefix="/comparison", template_folder="templates")


@bp.get("")
def index():
    service = QuotationService(get_db())
    args = request.args
    ids = sorted({int(v) for v in args.getlist("ids") if v.isdigit()})
    product = args.get("product", "").strip()

    if not ids and not product:
        return render_template("comparison/pick.html", products=service.product_summary())
    if ids:
        if len(ids) < 2:
            flash("Hãy chọn ít nhất 2 báo giá để so sánh.", "warn")
            return redirect(url_for("quotations.index"))
        quotes, heading = service.by_ids(ids), "Các báo giá đã chọn"
    else:
        quotes = service.by_product(product)
        heading = quotes[0].product_name if quotes else product
    if not quotes:
        flash("Không tìm thấy báo giá nào để so sánh.", "warn")
        return redirect(url_for("comparison.index"))

    hide_expired = args.get("hide_expired") == "1"
    if hide_expired:
        quotes = [q for q in quotes if validity_of(q).code != "expired"]

    reader = FormReader(args)
    quantity = reader.decimal("quantity", "Số lượng dự kiến", min_exclusive=Decimal(0),
                              max_value=Decimal("999999999999"), places=3)
    rates = {}
    for currency in sorted({q.currency for q in quotes}):
        rate = reader.decimal(f"rate_{currency}", f"Tỷ giá {currency}", min_exclusive=Decimal(0),
                              max_value=Decimal("1000000000"), places=6)
        if rate is not None:
            rates[currency] = rate

    comparison = build_comparison(quotes, quantity=quantity, target_currency=args.get("target"), rates=rates)
    values = args.to_dict()
    values["target"] = comparison.target
    return render_template("comparison/result.html", c=comparison, heading=heading, ids=ids,
                           product=None if ids else product, values=values, errors=reader.errors,
                           hide_expired=hide_expired)
