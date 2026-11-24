"""Giao diện web của module nhà cung cấp."""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from tradeflow.core.db import get_db
from tradeflow.core.errors import ConflictError, ValidationError

from .service import SupplierService

bp = Blueprint("suppliers", __name__, url_prefix="/suppliers", template_folder="templates")


def _service() -> SupplierService:
    return SupplierService(get_db())


def _form_page(mode: str, values: dict, errors: dict, supplier=None, status: int = 200):
    return render_template("suppliers/form.html", mode=mode, values=values, errors=errors,
                           supplier=supplier), status


@bp.get("")
def index():
    q = request.args.get("q", "").strip()
    country = request.args.get("country", "").strip().upper()
    archived = request.args.get("archived") == "1"
    service = _service()
    return render_template(
        "suppliers/list.html",
        suppliers=service.search(q=q, country=country, include_archived=archived),
        q=q, country=country, include_archived=archived,
        filtered=bool(q or country or archived),
    )


@bp.get("/new")
def new():
    return _form_page("new", {}, {})


@bp.post("/new")
def create():
    form = request.form.to_dict()
    try:
        supplier = _service().create(form)
    except ValidationError as exc:
        return _form_page("new", form, exc.errors, status=422)
    flash(f"Đã thêm nhà cung cấp “{supplier.name}”.", "ok")
    return redirect(url_for("suppliers.detail", supplier_id=supplier.id))


@bp.get("/<int:supplier_id>")
def detail(supplier_id: int):
    return render_template("suppliers/detail.html", supplier=_service().get(supplier_id))


@bp.get("/<int:supplier_id>/edit")
def edit(supplier_id: int):
    service = _service()
    supplier = service.get(supplier_id)
    return _form_page("edit", service.form_values(supplier), {}, supplier)


@bp.post("/<int:supplier_id>/edit")
def update(supplier_id: int):
    service = _service()
    supplier = service.get(supplier_id)
    form = request.form.to_dict()
    try:
        supplier = service.update(supplier_id, form)
    except ValidationError as exc:
        return _form_page("edit", form, exc.errors, supplier, status=422)
    flash("Đã lưu thay đổi.", "ok")
    return redirect(url_for("suppliers.detail", supplier_id=supplier.id))


@bp.post("/<int:supplier_id>/archive")
def archive(supplier_id: int):
    supplier = _service().set_active(supplier_id, False)
    flash(f"Đã lưu trữ “{supplier.name}”. Báo giá cũ vẫn được giữ nguyên.", "ok")
    return redirect(url_for("suppliers.detail", supplier_id=supplier_id))


@bp.post("/<int:supplier_id>/restore")
def restore(supplier_id: int):
    supplier = _service().set_active(supplier_id, True)
    flash(f"Đã khôi phục “{supplier.name}”.", "ok")
    return redirect(url_for("suppliers.detail", supplier_id=supplier_id))


@bp.post("/<int:supplier_id>/delete")
def delete(supplier_id: int):
    try:
        _service().delete(supplier_id)
    except ConflictError as exc:
        flash(str(exc), "error")
        return redirect(url_for("suppliers.detail", supplier_id=supplier_id))
    flash("Đã xóa nhà cung cấp.", "ok")
    return redirect(url_for("suppliers.index"))
