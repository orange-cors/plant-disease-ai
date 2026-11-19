# TramXanh — Website Phân Phối Thuốc BVTV & AI Nhận Diện Bệnh Cây

## 1. Giới thiệu nhanh

**TramXanh** là ứng dụng web phân phối thuốc bảo vệ thực vật tích hợp mô hình AI (**PyTorch ResNet18**) giúp nhận diện bệnh trên lá 4 loại cây hoa màu phổ biến ở Đồng bằng sông Hồng (**Cà chua, Khoai tây, Ớt chuông, Ngô**) và gợi ý thuốc đặc trị liên quan.

- **Kiến trúc:** 3 tầng — Giao diện (`templates/`), Xử lý nghiệp vụ (`controllers/`), Truy cập dữ liệu (`data_access/`) + mô-đun suy luận AI cục bộ (`ai_service.py`, dùng trọng số `models/resnet18_phase2_best.pth`).
- **Cơ sở dữ liệu:** Hỗ trợ **Microsoft SQL Server** (file khởi tạo `database_setup.sql`) và tự động chuyển sang **SQLite** (`tramxanh.db`) kèm dữ liệu mẫu nếu SQL Server chưa chạy.
- **Chức năng chính:** Tra cứu & lọc sản phẩm, Giỏ hàng & Đặt hàng COD, Nhận diện bệnh lá cây qua ảnh/camera, Trang quản trị (Danh mục, Sản phẩm, Đơn hàng, Khách hàng).

---

## 2. Hướng dẫn cài đặt & chạy Backend (Local)

### Bước 1: Cài đặt thư viện cần thiết
Mở terminal (PowerShell / CMD) tại thư mục gốc dự án (`plant-disease-ai`) và chạy:

```powershell
pip install -r requirements.txt
```

Nếu muốn cài bản **PyTorch CPU** gọn nhẹ (chạy nhanh ~25ms/ảnh, tải ~130MB):

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Bước 2: Cấu hình cơ sở dữ liệu (tùy chọn)
- **Mặc định (nhanh nhất):** Không cần làm gì thêm. File `.env` đang để `DB_MODE=auto`, khi chạy backend sẽ tự thử kết nối SQL Server, nếu chưa bật thì tự tạo `tramxanh.db` và nạp sẵn dữ liệu mẫu.
- **Dùng Microsoft SQL Server:** Chạy file `database_setup.sql` trong SSMS, sau đó chỉnh thông tin kết nối trong file `.env` (`MSSQL_SERVER`, `MSSQL_DATABASE`, `MSSQL_DRIVER`).

### Bước 3: Khởi chạy Backend
Mở **Terminal 1** tại thư mục dự án và chạy một trong hai lệnh sau:

```powershell
python app.py
```

Hoặc chạy trực tiếp bằng Uvicorn:

```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Khi thấy dòng sau là backend đã sẵn sàng:

```text
[AIService] Loaded PyTorch ResNet18 model from resnet18_phase2_best.pth on cpu
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Truy cập web trên máy cá nhân tại: **http://127.0.0.1:8000**

---

## 3. Hướng dẫn mở Tunnel Link (Cho người khác truy cập từ xa)

Giữ nguyên **Terminal 1** đang chạy backend ở cổng `8000`, sau đó chọn **1 trong 3 cách** dưới đây để tạo link public `https://...` (có sẵn HTTPS nên điện thoại mở được cả tính năng **Chụp bằng camera**).

### Cách 1: Dùng `localhost.run` qua SSH (Nhanh nhất — không cần cài thêm phần mềm)
Mở **Terminal 2** và chạy:

```powershell
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:127.0.0.1:8000 nokey@localhost.run
```

- Đợi khoảng 3–5 giây, màn hình sẽ hiện dòng tương tự:
  ```text
  xxxxxxxxxxxx.app.lhr.life tunneled with tls termination, https://xxxxxxxxxxxx.app.lhr.life
  ```
- Copy link `https://xxxxxxxxxxxx.app.lhr.life` gửi cho người khác truy cập.
- **Lưu ý:** Giữ cả 2 cửa sổ terminal mở trong suốt lúc sử dụng. Nhấn `Ctrl + C` để tắt.

## 4. Tài khoản thử nghiệm & Kiểm thử nhanh

| Vai trò | Số điện thoại / Tài khoản | Mật khẩu |
|---|---|---|
| **Khách hàng** | `0912345678` (hoặc `khachhang`) | `123456` |
| **Quản trị viên** | `0900000001` (hoặc `admin`) | `admin123` |

Chạy bộ kiểm thử tự động (22 Test Cases `TC01`–`TC22`):

```powershell
pytest tests/test_tramxanh_tc01_tc22.py -v
```
