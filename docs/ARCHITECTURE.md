# Kiến trúc TradeFlow

Tài liệu này mô tả cách ứng dụng được tổ chức, các quy ước bắt buộc và lý do của từng quyết định kỹ thuật. Người (hoặc AI) thêm chức năng mới cần đọc tài liệu này trước.

## 1. Nguyên tắc

- **Modular Monolith**: một ứng dụng duy nhất, chia thành các module có ranh giới rõ. Chưa dùng microservices vì chưa có lý do thực tế.
- **Thêm, thay, mở rộng mà không viết lại**: module mới chỉ cần khai báo một dòng trong `registry.py`.
- **Không đoán, không bịa dữ liệu**: dữ liệu nào chưa so sánh được thì cảnh báo, không âm thầm kết luận.
- **Ít phụ thuộc, miễn phí**: chỉ cần Python và Flask. CSDL là SQLite (một file).

## 2. Các tầng trong một module

```
Trình duyệt
   │
   ▼
routes.py       Giao diện web: đọc yêu cầu, gọi service, trả trang. KHÔNG chứa nghiệp vụ, KHÔNG chứa SQL.
   │
   ▼
service.py      Nghiệp vụ: kiểm tra dữ liệu, quy tắc, tính toán. KHÔNG chứa SQL.
   │
   ▼
repository.py   Truy cập dữ liệu: nơi DUY NHẤT chứa SQL của module.
   │
   ▼
SQLite          models.py chỉ là các lớp dữ liệu thuần (dataclass).
```

Riêng `comparison/service.py` là **hàm thuần** (không đụng CSDL) nên kiểm thử rất nhanh và dễ.

## 3. Quy tắc phụ thuộc giữa các module

```
core  ←  suppliers  ←  quotations  ←  comparison  ←  dashboard
```

Mũi tên nghĩa là "được phép dùng". Module bên trái **không bao giờ** được import module bên phải. Ví dụ `suppliers` không biết `quotations` tồn tại: khi xóa nhà cung cấp, CSDL tự chặn nếu đã có báo giá (khóa ngoại RESTRICT) và `suppliers` chỉ chuyển lỗi đó thành thông báo dễ hiểu.

Quy tắc này **có kiểm thử tự động** (`tests/test_architecture.py`): vi phạm là test đỏ. Test cũng chặn việc viết SQL ngoài `repository.py`.

## 4. Thêm một module mới (danh sách việc cần làm)

1. Tạo `tradeflow/modules/<ten>/` gồm `__init__.py`, `models.py`, `repository.py`, `service.py`, `routes.py`, `templates/<ten>/...`.
2. Trong `__init__.py` khai báo `module = ModuleInfo(key, label, path, blueprint)`.
3. Thêm module vào `load_modules()` trong `tradeflow/registry.py` (thứ tự ở đây là thứ tự trên menu).
4. Khai báo quy tắc phụ thuộc vào `ALLOWED` trong `tests/test_architecture.py`.
5. Nếu cần bảng mới: thêm file `migrations/NNNN_ten.sql` (xem mục 6).
6. Viết kiểm thử, chạy toàn bộ, cập nhật `docs/ROADMAP.md`.

## 5. Quy ước dữ liệu

| Loại | Cách lưu và xử lý | Lý do |
|---|---|---|
| Tiền, đơn giá, số lượng | Python `Decimal`, lưu chuỗi thập phân (`'0.0042'`) | Không sai số làm tròn |
| Ngày | Chuỗi `YYYY-MM-DD` | Sắp xếp đúng, không phụ thuộc múi giờ |
| Thời điểm tạo/sửa | Giờ UTC dạng ISO, hiển thị đổi sang giờ máy | Nhất quán khi chuyển máy chủ |
| Quốc gia | Mã ISO 2 chữ cái (`CN`, `VN`) | Cho các module pháp lý, cảnh báo sau này |
| Đồng tiền | Mã ISO 4217 (`USD`, `CNY`) | Như trên |
| Incoterms | Mã 3 chữ (`FOB`), phiên bản 2020 | Chỉ lưu mã và tên, không chép nội dung quy tắc (bản quyền ICC) |
| Dữ liệu xóa | Nhà cung cấp: lưu trữ thay vì xóa | Giữ lịch sử báo giá |

Nhập số: chỉ nhận dấu chấm thập phân (xem `core/forms.py`). Hiển thị số: dấu cách ngăn nghìn (xem `core/text.py`).

Tìm kiếm so khớp theo `fold()` (chữ thường, bỏ dấu, đ→d) ngay trong Python, vì SQLite chỉ so khớp hoa/thường với ký tự ASCII. Ổn với vài nghìn dòng; khi dữ liệu lớn hơn thì thêm cột chuẩn hóa sẵn.

## 6. Thay đổi cấu trúc cơ sở dữ liệu

- Mọi thay đổi nằm trong `migrations/NNNN_ten.sql`, đánh số tăng dần.
- Khi khởi động, `core/db.py::run_migrations` chạy các file chưa áp dụng theo thứ tự, mỗi file trong một giao dịch (lỗi thì hoàn tác cả file). Bảng `schema_migrations` ghi lại những file đã chạy.
- **Không sửa file migration đã phát hành.** Muốn đổi thì thêm file số mới.

## 7. Bảo mật hiện có

- Chỉ nghe ở `127.0.0.1` (không truy cập được từ máy khác).
- Chặn CSRF: yêu cầu ghi (POST) có `Origin` hoặc `Referer` phải trùng địa chỉ đang chạy, nếu không trả 403.
- Header `Content-Security-Policy` chỉ cho phép tài nguyên cùng nguồn: không tải font, script, ảnh từ bên ngoài, nên chạy được khi offline và không rò rỉ dữ liệu.
- Jinja2 tự thoát ký tự đặc biệt (chống XSS); link website chỉ nhận `http`/`https`.
- SQL luôn dùng tham số (`?`), không ghép chuỗi từ dữ liệu người dùng.
- Cookie phiên ký bằng khóa bí mật tự sinh trong `data/secret.key` (hoặc `TRADEFLOW_SECRET_KEY`).

**Chưa có:** đăng nhập, phân quyền, mã hóa file CSDL. Bắt buộc làm đăng nhập và phân quyền trước khi đưa lên máy chủ hoặc cho nhiều người dùng.

## 8. Kế hoạch cho các tích hợp bên ngoài (chưa làm)

Mọi dịch vụ bên ngoài (AI, tỷ giá, tin tức vận tải) đi qua một **adapter** riêng trong `tradeflow/integrations/<dich_vu>/`, để đổi nhà cung cấp mà không đụng nghiệp vụ. Ví dụ dự kiến cho tỷ giá (GĐ5):

```python
class RateProvider(Protocol):
    name: str
    def fetch(self, base: str, quote: str) -> "RateQuote": ...   # RateQuote có: giá trị, nguồn, thời điểm lấy

# Module nghiệp vụ chỉ biết RateProvider, không biết nguồn cụ thể là gì.
```

Nguyên tắc chung: lưu **nguồn và thời điểm** của mọi dữ liệu bên ngoài; có cache, thử lại khi lỗi; phân biệt "giá tham chiếu" với "báo giá thực tế"; khóa API chỉ ở biến môi trường; **không tự gửi** hợp đồng, báo giá mật hay dữ liệu khách hàng lên dịch vụ AI khi chưa có cơ chế bảo vệ và sự đồng ý của người dùng. Tên mô hình AI nằm trong cấu hình (không ghi cứng trong code) để đổi sang mô hình mới nhất chỉ cần sửa một dòng.

## 9. Nhật ký quyết định kỹ thuật

| # | Quyết định | Lý do và đánh đổi |
|---|---|---|
| 1 | Flask + `sqlite3` chuẩn của Python, **không** dùng FastAPI/SQLAlchemy/pytest | Môi trường phát triển không cài được thêm thư viện, nên các lựa chọn này không kiểm thử được. Flask + sqlite3 + unittest kiểm thử được đầy đủ và người dùng chỉ cần cài một thư viện. Đánh đổi: SQL viết tay, nhưng đã gom hết vào `repository.py`; chuyển sang PostgreSQL sau này chỉ cần thay các file đó và viết lại migration cho PostgreSQL |
| 2 | Giao diện HTML dựng ở máy chủ, không dùng framework JavaScript | Không cần Node hay bước build; ít thứ để hỏng; JS chỉ ~15 dòng |
| 3 | Migration bằng file SQL + bộ chạy tự viết (~40 dòng) | Không cần Alembic; người dùng không phải gõ lệnh; có kiểm thử hoàn tác khi lỗi |
| 4 | Tiền lưu dạng chuỗi thập phân | SQLite không có kiểu số thập phân chính xác; chuỗi + `Decimal` tránh sai số |
| 5 | Chỉ chấp nhận dấu chấm khi nhập số, hiển thị bằng dấu cách ngăn nghìn | Tránh nhầm `1,500` / `1.500` giữa kiểu Việt và kiểu quốc tế khi xử lý tiền |
| 6 | Chưa có đăng nhập ở MVP, chỉ nghe `127.0.0.1` | Người dùng đơn lẻ trên máy cá nhân; đăng nhập là điều kiện bắt buộc trước khi lên máy chủ |
| 7 | Trang so sánh không có "điểm tổng hợp" | Một điểm số lúc này sẽ che giấu những thứ chưa tính được (cước, thuế). Chỉ đánh dấu tốt nhất theo từng tiêu chí; điểm tổng hợp làm sau GĐ4 |
| 8 | Nhà cung cấp lưu trữ thay vì xóa; báo giá xóa được | Giữ lịch sử. Lịch sử thay đổi của báo giá (kể cả khi sửa/xóa) sẽ làm ở GĐ6 |
| 9 | Danh sách quốc gia thu gọn (~60) thay vì đủ ~250 | Đủ các đối tác thương mại chính, thêm nước khác chỉ cần thêm một dòng trong `core/reference_data.py` |

## 10. Giả định đã đặt và giới hạn hiện tại

- Mỗi báo giá có **một mức giá** cho một đơn vị tính. Chưa hỗ trợ bảng giá theo bậc số lượng (ghi tạm vào Ghi chú).
- So sánh yêu cầu cùng đơn vị tính; chưa tự quy đổi kg ↔ tấn.
- Tỷ giá trên trang so sánh là **do người dùng nhập tay**, không lưu lại. Tỷ giá tham chiếu tự động ở GĐ5.
- Chưa đính kèm tệp (PDF/Excel báo giá) và chưa xuất báo cáo.
- Chưa phân trang danh sách (ổn cho vài nghìn dòng).
- Đã kiểm tra giao diện trên Chromium (máy tính và điện thoại); chưa thử trên Safari/Firefox.
