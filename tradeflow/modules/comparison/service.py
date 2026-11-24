"""So sánh báo giá. Toàn bộ là hàm thuần (không đụng CSDL) nên kiểm thử rất dễ.

Nguyên tắc: không đưa ra kết luận khi dữ liệu chưa so sánh được với nhau. Thiếu tỷ giá, khác đơn vị tính,
khác Incoterms... đều được cảnh báo rõ ràng thay vì âm thầm xếp hạng sai. Giá thấp nhất chưa chắc là
lựa chọn tốt nhất: ở bản này chỉ đánh dấu "tốt nhất theo từng tiêu chí", chưa có điểm tổng hợp
(sẽ làm sau khi có tính toán chi phí nhập khẩu thực tế).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Callable, Iterable, Mapping, Sequence

from tradeflow.core import clock
from tradeflow.core.reference_data import CURRENCIES
from tradeflow.core.text import fold, format_date, format_number
from tradeflow.modules.quotations.models import Quotation
from tradeflow.modules.quotations.service import Validity, validity_of


@dataclass
class Flag:
    level: str  # "warn" | "info"
    text: str


@dataclass
class Row:
    quote: Quotation
    validity: Validity
    converted_price: Decimal | None  # đơn giá đã quy đổi sang đồng tiền so sánh
    total: Decimal | None = None  # số lượng dự kiến x đơn giá quy đổi
    rank: int | None = None
    premium_pct: Decimal | None = None  # % cao hơn mức giá thấp nhất
    moq_short: bool = False
    missing: list[str] = field(default_factory=list)
    flags: list[Flag] = field(default_factory=list)
    best: set[str] = field(default_factory=set)  # tiêu chí mà dòng này tốt nhất: price, lead_time, moq, rating


@dataclass
class Comparison:
    rows: list[Row]
    target: str
    quantity: Decimal | None
    units: list[str]
    products: list[str]
    currencies: list[str]
    foreign_currencies: list[str]  # đồng tiền khác đồng tiền so sánh: cần tỷ giá
    missing_rates: list[str]
    price_comparable: bool
    warnings: list[Flag]


def _distinct(values: Iterable[str]) -> list[str]:
    seen: dict[str, str] = {}
    for v in values:
        seen.setdefault(fold(v), v)
    return list(seen.values())


def _pick_target(quotes: Sequence[Quotation], wanted: str | None) -> str:
    if wanted in CURRENCIES:
        return wanted
    counts = Counter(q.currency for q in quotes)
    if not counts:
        return "USD"
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def _mark_best(rows: list[Row], criterion: str, value_of: Callable[[Row], object], *, lowest: bool) -> None:
    """Đánh dấu dòng tốt nhất. Cần ít nhất 2 giá trị và có sự khác biệt, nếu không thì không đánh dấu."""
    scored = [(r, value_of(r)) for r in rows if value_of(r) is not None]
    values = [v for _, v in scored]
    if len(values) < 2 or min(values) == max(values):
        return
    best = min(values) if lowest else max(values)
    for r, v in scored:
        if v == best:
            r.best.add(criterion)


def build_comparison(
    quotes: Iterable[Quotation],
    *,
    quantity: Decimal | None = None,
    target_currency: str | None = None,
    rates: Mapping[str, Decimal] | None = None,
    today: date | None = None,
) -> Comparison:
    """rates: {"USD": 25400} nghĩa là 1 USD = 25400 đồng tiền so sánh. Tỷ giá do người dùng cung cấp."""
    today = today or clock.today()
    rates = {c: r for c, r in (rates or {}).items() if r is not None and r > 0}
    quotes = list(quotes)
    target = _pick_target(quotes, target_currency)
    currencies = sorted({q.currency for q in quotes})
    foreign = [c for c in currencies if c != target]
    missing_rates = [c for c in foreign if c not in rates]
    units = _distinct(q.unit for q in quotes)
    products = _distinct(q.product_name for q in quotes)
    comparable = len(units) == 1

    rows: list[Row] = []
    for q in quotes:
        if q.currency == target:
            converted = q.unit_price
        elif q.currency in rates:
            converted = q.unit_price * rates[q.currency]
        else:
            converted = None
        row = Row(quote=q, validity=validity_of(q, today), converted_price=converted)
        if quantity and converted is not None and comparable:
            row.total = quantity * converted
        row.moq_short = bool(quantity and q.moq and comparable and quantity < q.moq)
        row.missing = [label for label, value in (
            ("Incoterms", q.incoterm), ("MOQ", q.moq), ("Thanh toán", q.payment_terms),
            ("Thời gian giao", q.lead_time_days), ("Hiệu lực", q.valid_until),
        ) if value in (None, "")]
        if row.validity.code == "expired":
            row.flags.append(Flag("warn", f"Đã hết hạn từ {format_date(q.valid_until)}, giá có thể không còn áp dụng."))
        elif row.validity.code == "expiring":
            row.flags.append(Flag("info", f"Sắp hết hạn ({row.validity.label.lower()})."))
        if row.moq_short:
            row.flags.append(Flag("warn", f"Số lượng dự kiến ({format_number(quantity, max_decimals=3)}) "
                                          f"thấp hơn MOQ ({format_number(q.moq, max_decimals=3)})."))
        if converted is None:
            row.flags.append(Flag("info", f"Chưa quy đổi được vì thiếu tỷ giá {q.currency}."))
        rows.append(row)

    ranked = [r for r in rows if comparable and r.converted_price is not None]
    for r in ranked:
        r.rank = 1 + sum(1 for o in ranked if o.converted_price < r.converted_price)
    if ranked:
        lowest = min(r.converted_price for r in ranked)
        for r in ranked:
            r.premium_pct = ((r.converted_price / lowest - 1) * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    _mark_best(ranked, "price", lambda r: r.converted_price, lowest=True)
    _mark_best(rows, "lead_time", lambda r: r.quote.lead_time_days, lowest=True)
    if comparable:
        _mark_best(rows, "moq", lambda r: r.quote.moq, lowest=True)
    _mark_best(rows, "rating", lambda r: r.quote.supplier_rating, lowest=False)

    warnings: list[Flag] = []
    if len(quotes) == 1:
        warnings.append(Flag("info", "Mới có 1 báo giá nên chưa có gì để so sánh. Hãy thêm báo giá của nhà cung cấp khác."))
    if len(products) > 1:
        warnings.append(Flag("warn", f"Danh sách có {len(products)} tên sản phẩm khác nhau ({'; '.join(products)}). "
                                     "Hãy chắc chắn các báo giá này cùng quy cách trước khi so giá."))
    if not comparable:
        warnings.append(Flag("warn", f"Đơn vị tính khác nhau ({', '.join(units)}), nên chưa xếp hạng giá và chưa tính tổng giá trị. "
                                     "Hãy nhập lại báo giá theo cùng một đơn vị."))
    if missing_rates:
        warnings.append(Flag("warn", f"Chưa có tỷ giá cho {', '.join(missing_rates)} sang {target}, nên các báo giá này "
                                     f"chưa được quy đổi và xếp hạng. Nhập tỷ giá ở ô bên dưới."))
    incoterms = {q.incoterm for q in quotes}
    if len(incoterms - {None}) > 1 or (None in incoterms and len(incoterms) > 1):
        listed = ", ".join(sorted(i for i in incoterms if i)) or "chưa rõ"
        warnings.append(Flag("warn", f"Điều kiện giao hàng (Incoterms) không đồng nhất ({listed}"
                                     f"{', có báo giá chưa ghi' if None in incoterms else ''}). Giá chưa cùng cơ sở: "
                                     "cước vận chuyển, bảo hiểm, thuế có thể chưa được tính vào một số báo giá. "
                                     "Phần tính chi phí nhập khẩu (giai đoạn sau) sẽ giúp so sánh công bằng hơn."))
    expired = sum(1 for r in rows if r.validity.code == "expired")
    if expired:
        warnings.append(Flag("warn", f"{expired} báo giá đã hết hạn, giá có thể không còn áp dụng."))
    if quantity is None and len(quotes) > 1:
        warnings.append(Flag("info", "Nhập số lượng dự kiến mua để tính tổng giá trị và kiểm tra MOQ."))
    if any(r.moq_short for r in rows):
        warnings.append(Flag("warn", "Có nhà cung cấp yêu cầu MOQ cao hơn số lượng dự kiến."))

    rows.sort(key=lambda r: (r.rank is None, r.converted_price if r.rank is not None else Decimal(0),
                             fold(r.quote.supplier_name), r.quote.id))
    return Comparison(rows=rows, target=target, quantity=quantity, units=units, products=products,
                      currencies=currencies, foreign_currencies=foreign, missing_rates=missing_rates,
                      price_comparable=comparable, warnings=warnings)
