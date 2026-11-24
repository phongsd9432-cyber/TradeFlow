# TradeFlow

Ứng dụng web giúp doanh nghiệp nhỏ và nhà nhập khẩu tại Việt Nam quản lý nhà cung cấp, lưu báo giá và so sánh báo giá. Dữ liệu nằm hoàn toàn trên máy của bạn.

**Phiên bản hiện tại (0.1.0):** Nhà cung cấp, Báo giá, So sánh báo giá. Chi phí nhập khẩu, tỷ giá tham chiếu và lịch sử thay đổi sẽ có ở các giai đoạn sau (xem `docs/ROADMAP.md`).

## Cách chạy

### Windows (dễ nhất)

1. Cài Python 3.10 trở lên tại https://www.python.org/downloads/ . Khi cài, **nhớ tick ô "Add python.exe to PATH"**.
2. Bấm đúp vào file `start.bat`. Lần đầu sẽ mất vài chục giây để chuẩn bị, trình duyệt sẽ tự mở TradeFlow.
3. Muốn dừng: đóng cửa sổ đen hoặc nhấn Ctrl+C.

### Cách gõ lệnh (Windows, macOS, Linux)

```
python -m venv .venv
.venv\Scripts\activate          (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python run.py
```

Rồi mở http://127.0.0.1:8000 trên trình duyệt.

## Cách dùng nhanh

1. **Nhà cung cấp**: thêm nhà cung cấp bạn đang hỏi giá.
2. **Báo giá**: nhập báo giá nhận được. Càng đủ thông tin (MOQ, Incoterms, thanh toán, thời gian giao, hiệu lực) càng so sánh được chính xác.
3. **So sánh**: chọn một sản phẩm (hoặc tick nhiều báo giá ở trang Báo giá) để đặt các báo giá cạnh nhau. Nhập số lượng dự kiến mua để tính tổng giá trị và kiểm tra MOQ. Nếu các báo giá khác đồng tiền, nhập tỷ giá bạn muốn dùng.

Một số điều nên biết:

- Số thập phân dùng **dấu chấm** (12.5), không dùng dấu phẩy. Ứng dụng từ chối dấu phẩy để tránh nhầm "1,500" là 1.5 hay 1500.
- Số hiển thị dạng `1 234 567.50` (dấu cách ngăn nghìn) để không bị hiểu nhầm giữa kiểu Việt Nam và kiểu quốc tế.
- Tìm kiếm không phân biệt hoa thường và dấu: gõ "cong ty" vẫn ra "Công ty".
- Nhà cung cấp có thể **Lưu trữ** (ẩn nhưng giữ lịch sử). Chỉ xóa được nhà cung cấp chưa có báo giá.
- Trang So sánh **không tự đoán**: thiếu tỷ giá, khác đơn vị tính hoặc khác Incoterms thì sẽ cảnh báo thay vì xếp hạng. Giá thấp nhất chưa chắc là lựa chọn tốt nhất.

## An toàn dữ liệu

- Mặc định chỉ truy cập được từ **chính máy bạn** (127.0.0.1). **Chưa có đăng nhập**, vì vậy đừng mở ứng dụng ra mạng hay Internet khi chưa làm giai đoạn đăng nhập và phân quyền.
- Dữ liệu nằm trong một file duy nhất `data/tradeflow.db`. **Sao lưu bằng cách chép file này** (khi ứng dụng đang tắt). Thư mục `data/` không được đưa vào git.
- Khóa bí mật (API key của dịch vụ AI, tỷ giá sau này) chỉ đặt trong file `.env` hoặc biến môi trường, không bao giờ ghi vào mã nguồn. Xem `.env.example`.
- Ứng dụng hiện không gửi bất kỳ dữ liệu nào ra ngoài.

## Chạy kiểm thử

```
python -m unittest discover -s tests -t .
```

Phải thấy dòng `OK`. Hiện có 74 kiểm thử.

## Cấu trúc thư mục

```
run.py, start.bat      khởi động
tradeflow/
  app.py, registry.py  ghép ứng dụng và danh sách module
  core/                phần dùng chung: cấu hình, CSDL, kiểm tra dữ liệu, giao diện nền
  modules/             mỗi chức năng là một thư mục riêng
    suppliers/  quotations/  comparison/  dashboard/
migrations/            các file SQL đổi cấu trúc CSDL (tự chạy khi khởi động)
tests/                 kiểm thử tự động
docs/                  ARCHITECTURE.md (kiến trúc), ROADMAP.md (kế hoạch, tiến độ)
```

## Gặp sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| `start.bat` báo chưa tìm thấy Python | Cài Python và nhớ tick "Add python.exe to PATH", rồi chạy lại |
| Báo cổng 8000 đang bận | Tạo file `.env` với dòng `TRADEFLOW_PORT=8001` rồi chạy lại |
| Muốn bắt đầu lại từ đầu | Tắt ứng dụng, xóa file `data/tradeflow.db`, mở lại |

Ghi chú: file `start.bat` được viết cho Windows nhưng chưa được chạy thử trên Windows thật (môi trường phát triển là Linux). Nếu gặp lỗi, hãy dùng cách gõ lệnh ở trên và báo lại để sửa.
