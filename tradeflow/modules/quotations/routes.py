"""Giao diện web của module báo giá."""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from tradeflow.core import clock
from tradeflow.core.db import get_db
from tradeflow.core.errors import ValidationError

from .service import QuotationService, validity_of

bp = Blueprint("quotations", __name__, url_prefix="/quotations", template_folder="templates")


def _service() -> QuotationService:
    return QuotationService(get_db())


def _int_or_none(value: str | None) -> int | None:
    return int(value) if value and value.isdigit() else None


def _form_page(service: QuotationService, mode: str, values: dict, errors: dict, quote=None, status=200):
    suppliers = service.suppliers.active_options()
    if quote is not None and not any(s.id == quote.supplier_id for s in suppliers):
        suppliers.append(service.suppliers.get(quote.supplier_id))  # giữ nhà cung cấp đã lưu trữ khi sửa
    options = [(str(s.id), f"{s.name} ({s.country})") for s in suppliers]
    return render_template(
        "quotations/form.html", mode=mode, values=values, errors=errors, quote=quote,
        supplier_options=options, product_names=service.product_names(),
    ), status


@bp.get("/")
def index():
    q = request.args.get("q", "").strip()
    supplier_id = _int_or_none(request.args.get("supplier_id"))
    status = request.args.get("status", "")
    service = _service()
    today = clock.today()
    items = service.search(q=q, supplier_id=supplier_id, status=status, today=today)
    return render_template(
        "quotations/list.html", quotes=items, validity={x.id: validity_of(x, today) for x in items},
        q=q, supplier_id=supplier_id, status=status, filtered=bool(q or supplier_id or status),
        suppliers=service.suppliers.search(include_archived=True),
    )


@bp.get("/new")
def new():
    service = _service()
    values = {"quote_date": clock.today().isoformat()}
    supplier_id = _int_or_none(request.args.get("supplier_id"))
    if supplier_id:
        values["supplier_id"] = str(supplier_id)
    return _form_page(service, "new", values, {})


@bp.post("/new")
def create():
    service = _service()
    form = request.form.to_dict()
    try:
        quote = service.create(form)
    except ValidationError as exc:
        return _form_page(service, "new", form, exc.errors, status=422)
    flash("Đã lưu báo giá.", "ok")
    return redirect(url_for("quotations.detail", quotation_id=quote.id))


@bp.get("/<int:quotation_id>")
def detail(quotation_id: int):
    quote = _service().get(quotation_id)
    return render_template("quotations/detail.html", quote=quote, validity=validity_of(quote))


@bp.get("/<int:quotation_id>/edit")
def edit(quotation_id: int):
    service = _service()
    quote = service.get(quotation_id)
    return _form_page(service, "edit", service.form_values(quote), {}, quote)


@bp.post("/<int:quotation_id>/edit")
def update(quotation_id: int):
    service = _service()
    quote = service.get(quotation_id)
    form = request.form.to_dict()
    try:
        service.update(quotation_id, form)
    except ValidationError as exc:
        return _form_page(service, "edit", form, exc.errors, quote, status=422)
    flash("Đã lưu thay đổi.", "ok")
    return redirect(url_for("quotations.detail", quotation_id=quotation_id))


@bp.post("/<int:quotation_id>/delete")
def delete(quotation_id: int):
    _service().delete(quotation_id)
    flash("Đã xóa báo giá.", "ok")
    return redirect(url_for("quotations.index"))
