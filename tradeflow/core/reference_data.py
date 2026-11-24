"""Danh mục tham chiếu dùng chung. Muốn thêm một mục: thêm một dòng vào danh sách tương ứng.

Về Incoterms: chỉ dùng mã viết tắt và tên gọi. Nội dung đầy đủ của các quy tắc thuộc bản quyền của
ICC và KHÔNG được chép vào ứng dụng; cần kiểm tra giấy phép trước khi làm Module F (kiến thức thương mại).
"""
from __future__ import annotations

from tradeflow.core.text import fold

COUNTRIES: dict[str, str] = {
    "AE": "Các Tiểu vương quốc Ả Rập Thống nhất (UAE)", "AR": "Argentina", "AT": "Áo", "AU": "Úc",
    "BD": "Bangladesh", "BE": "Bỉ", "BR": "Brazil", "CA": "Canada", "CH": "Thụy Sĩ",
    "CI": "Bờ Biển Ngà", "CL": "Chile", "CN": "Trung Quốc", "CO": "Colombia", "CZ": "Cộng hòa Séc",
    "DE": "Đức", "DK": "Đan Mạch", "EG": "Ai Cập", "ES": "Tây Ban Nha", "FI": "Phần Lan",
    "FR": "Pháp", "GB": "Vương quốc Anh", "GH": "Ghana", "GR": "Hy Lạp", "HK": "Hồng Kông",
    "ID": "Indonesia", "IE": "Ireland", "IL": "Israel", "IN": "Ấn Độ", "IT": "Ý", "JP": "Nhật Bản",
    "KE": "Kenya", "KH": "Campuchia", "KR": "Hàn Quốc", "LA": "Lào", "LK": "Sri Lanka",
    "MA": "Ma-rốc", "MM": "Myanmar", "MX": "Mexico", "MY": "Malaysia", "NG": "Nigeria",
    "NL": "Hà Lan", "NO": "Na Uy", "NZ": "New Zealand", "PE": "Peru", "PH": "Philippines",
    "PK": "Pakistan", "PL": "Ba Lan", "PT": "Bồ Đào Nha", "QA": "Qatar", "RU": "Nga",
    "SA": "Ả Rập Xê Út", "SE": "Thụy Điển", "SG": "Singapore", "TH": "Thái Lan", "TR": "Thổ Nhĩ Kỳ",
    "TW": "Đài Loan", "TZ": "Tanzania", "UA": "Ukraine", "US": "Hoa Kỳ", "VN": "Việt Nam",
    "ZA": "Nam Phi", "ZZ": "Khác (ghi rõ trong địa chỉ)",
}

# Thứ tự hiển thị: đồng tiền hay dùng trước.
CURRENCIES: dict[str, str] = {
    "USD": "Đô la Mỹ", "EUR": "Euro", "CNY": "Nhân dân tệ", "VND": "Đồng Việt Nam",
    "JPY": "Yên Nhật", "KRW": "Won Hàn Quốc", "THB": "Baht Thái", "SGD": "Đô la Singapore",
    "MYR": "Ringgit Malaysia", "IDR": "Rupiah Indonesia", "INR": "Rupee Ấn Độ",
    "TWD": "Đô la Đài Loan", "HKD": "Đô la Hồng Kông", "GBP": "Bảng Anh", "AUD": "Đô la Úc",
    "CAD": "Đô la Canada", "CHF": "Franc Thụy Sĩ", "AED": "Dirham UAE",
}

# Incoterms 2020 (đúng thứ tự thường gặp: mọi phương thức vận tải, rồi đường biển/thủy nội địa).
INCOTERMS: dict[str, str] = {
    "EXW": "Ex Works - Giao tại xưởng",
    "FCA": "Free Carrier - Giao cho người chuyên chở",
    "CPT": "Carriage Paid To - Cước phí trả tới",
    "CIP": "Carriage and Insurance Paid To - Cước phí và bảo hiểm trả tới",
    "DAP": "Delivered at Place - Giao tại nơi đến",
    "DPU": "Delivered at Place Unloaded - Giao tại nơi đến, đã dỡ hàng",
    "DDP": "Delivered Duty Paid - Giao đã nộp thuế",
    "FAS": "Free Alongside Ship - Giao dọc mạn tàu",
    "FOB": "Free on Board - Giao lên tàu",
    "CFR": "Cost and Freight - Tiền hàng và cước phí",
    "CIF": "Cost, Insurance and Freight - Tiền hàng, bảo hiểm và cước phí",
}

UNIT_SUGGESTIONS = ["kg", "tấn", "g", "cái", "bộ", "m", "m²", "m³", "lít", "thùng", "kiện", "cuộn", "pallet"]

COUNTRY_OPTIONS = sorted(
    COUNTRIES.items(), key=lambda kv: (kv[0] == "ZZ", fold(kv[1]))
)
CURRENCY_OPTIONS = [(code, f"{code} - {name}") for code, name in CURRENCIES.items()]
INCOTERM_OPTIONS = [(code, f"{code} - {name.split(' - ')[1]}") for code, name in INCOTERMS.items()]
