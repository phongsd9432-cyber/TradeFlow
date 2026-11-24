# Lộ trình và tiến độ TradeFlow

Cập nhật lần cuối: 24/11/2026. Phiên bản 0.1.0.

## Tiến độ MVP

| GĐ | Nội dung | Trạng thái | Kết quả kiểm thử |
|---|---|---|---|
| 0 | Nền móng: cấu trúc module, cấu hình, CSDL + migration, giao diện nền, bảo mật cơ bản | Xong | 30 test đạt (cùng GĐ1) |
| 1 | Quản lý nhà cung cấp (thêm, sửa, tìm, lưu trữ, xóa có điều kiện) | Xong | như trên |
| 2 | Quản lý báo giá (đủ trường theo định hướng, kiểm tra dữ liệu, hiệu lực) | Xong | 47 test đạt |
| 3 | So sánh báo giá (xếp hạng, quy đổi tỷ giá nhập tay, MOQ, cảnh báo) + trang tổng quan | Xong | **74 test đạt** |
| 4 | Tính chi phí nhập khẩu cơ bản | Chưa làm | |
| 5 | Tỷ giá tham chiếu từ một nguồn | Chưa làm | |
| 6 | Lịch sử thay đổi dữ liệu | Chưa làm | |

Ngoài kiểm thử tự động, đã chạy thử ứng dụng thật qua `run.py` với dữ liệu mẫu tạm, chụp và xem giao diện bằng Chromium ở màn hình máy tính (1360px) và điện thoại (390px). Hai lỗi giao diện tìm ra qua bước này đã được sửa (thanh lọc bị xếp dọc; trang tràn ngang trên điện thoại).

**Chưa được kiểm tra:** `start.bat` trên Windows thật, trình duyệt Safari/Firefox.

## Các giai đoạn tiếp theo (đề xuất, theo thứ tự)

### GĐ4. Chi phí nhập khẩu cơ bản (Module D)
- Từ một báo giá: giá hàng, cước vận chuyển, bảo hiểm, thuế nhập khẩu, VAT, phí thông quan và phí khác, ra tổng chi phí và chi phí trên mỗi đơn vị.
- **Mọi tỷ lệ thuế và phí do người dùng nhập, không có mặc định**, vì mỗi mặt hàng chịu thuế khác nhau.
- Đưa chi phí nhập khẩu vào trang so sánh để so sánh trên cơ sở "đã về kho", khắc phục hạn chế Incoterms khác nhau.
- Lúc đó mới có thể cân nhắc điểm tổng hợp.

### GĐ5. Tỷ giá tham chiếu (một phần của Module E)
- Adapter lấy tỷ giá từ **một** nguồn miễn phí hoặc chính thống; lưu nguồn và thời điểm; cache; thử lại khi lỗi; cập nhật theo lịch.
- Hiển thị rõ đây là "giá tham chiếu", tự điền sẵn vào ô tỷ giá của trang so sánh (người dùng vẫn sửa được).
- Cần chọn nguồn: sẽ tra cứu và so sánh điều kiện sử dụng trước khi quyết định.

### GĐ6. Lịch sử thay đổi
- Ghi lại trước/sau mỗi lần sửa hoặc xóa nhà cung cấp, báo giá. Hiện sửa báo giá là **ghi đè**, giá cũ mất.
- Biểu đồ biến động giá theo thời gian cho từng sản phẩm.

## Việc nên làm trước khi đưa lên máy chủ
- Đăng nhập và phân quyền người dùng.
- Máy chủ chạy thật (thay máy chủ phát triển của Flask), HTTPS.
- Sao lưu dữ liệu tự động; cân nhắc chuyển sang PostgreSQL.

## Danh sách chờ (chưa xếp lịch)
- Đính kèm tệp báo giá (PDF, Excel) cho từng báo giá.
- Báo giá có bảng giá theo bậc số lượng.
- Quy đổi đơn vị tính (kg ↔ tấn) khi so sánh.
- Xuất báo cáo so sánh ra Excel/PDF.
- Phân trang danh sách; cột tìm kiếm chuẩn hóa sẵn khi dữ liệu lớn.
- Tùy chọn kiểu hiển thị số theo Việt Nam (1.234,5) nếu người dùng muốn.
- Module AI hỗ trợ đọc báo giá từ PDF/Excel/email (cần cơ chế bảo vệ dữ liệu nhạy cảm trước).
- Module F (quy định, chứng từ), Module G (cảnh báo sớm): cần nghiên cứu nguồn dữ liệu và giấy phép riêng, không nằm trong MVP.

## Câu hỏi mở cho chủ dự án
1. Bạn dùng dấu phân cách số kiểu nào quen nhất (1 234.5 hiện tại, hay 1.234,5)?
2. Bạn thường nhập hàng bằng Incoterms nào, đồng tiền nào, để ưu tiên đúng ở GĐ4 và GĐ5?
3. Sau khi dùng thử: trường nào còn thiếu hoặc thừa trong form nhà cung cấp và báo giá?

## Nhật ký
- 24/11/2026: hoàn thành GĐ0 đến GĐ3, phiên bản 0.1.0.
