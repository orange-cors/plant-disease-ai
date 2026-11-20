# TramXanh — Phân Phối Thuốc BVTV & AI Nhận Diện Bệnh Cây

Website phân phối thuốc bảo vệ thực vật tích hợp mô hình AI (**PyTorch ResNet18**) nhận diện bệnh lá trên 4 loại cây hoa màu phổ biến ở Đồng bằng sông Hồng (**Cà chua, Khoai tây, Ớt chuông, Ngô**).

- **Kiến trúc 3 tầng:** Giao diện (`templates/`) → Nghiệp vụ (`controllers/`) → Truy cập dữ liệu (`data_access/`) + AI (`ai_service.py`, model `models/resnet18_phase2_best.pth`).
- **Cơ sở dữ liệu:** **Microsoft SQL Server** (`TramXanhDB`, 9 bảng theo ERD trong `database_setup.sql`).

---

## 1. Cài đặt Microsoft SQL Server & Tạo Database

1. **Cài SQL Server Express & SSMS:**
   - Tải **SQL Server Express** (miễn phí, chọn chế độ **Basic**): https://www.microsoft.com/en-us/sql-server/sql-server-downloads
   - Bấm **Install SSMS** ở cuối bước cài để cài SQL Server Management Studio.
2. **Cài ODBC Driver 17 for SQL Server** *(nếu chưa có)*:
   ```powershell
   winget install Microsoft.msodbcsql.17
   ```
3. **Khởi tạo CSDL `TramXanhDB`:**
   - Mở **SSMS** → kết nối vào `.\SQLEXPRESS` (chọn **Windows Authentication**).
   - Mở file `database_setup.sql` trong thư mục dự án → bấm **Execute (F5)** để tạo 9 bảng, 1 view và dữ liệu mẫu.
4. **Kiểm tra file `.env`:**
   ```env
   MSSQL_SERVER=.\SQLEXPRESS
   MSSQL_DATABASE=TramXanhDB
   MSSQL_DRIVER=ODBC Driver 17 for SQL Server
   ```
   *(Đổi `MSSQL_SERVER` nếu máy bạn dùng tên instance khác, ví dụ `localhost` hoặc `TÊN_MÁY\SQLEXPRESS`.)*

---

## 2. Cài đặt thư viện Python

Mở PowerShell tại thư mục gốc dự án (`plant-disease-ai`) và chạy:

```powershell
pip install -r requirements.txt
```

Nếu muốn cài bản **PyTorch CPU** gọn nhẹ (~130MB, chạy ~25ms/ảnh):

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

---

## 3. Chạy Backend (Local)

Mở **Terminal 1** tại thư mục dự án và chạy:

```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

*(Hoặc chạy nhanh bằng `python app.py`)*

Truy cập ứng dụng trên máy cá nhân tại: **http://127.0.0.1:8000**

---

## 4. Mở Tunnel Link (Chia sẻ truy cập từ xa qua HTTPS)

Giữ nguyên **Terminal 1** đang chạy backend ở cổng `8000`, mở thêm **Terminal 2** và chạy:

```powershell
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:127.0.0.1:8000 nokey@localhost.run
```

Đợi 3–5 giây, copy đường link `https://xxxxxxxxxxxx.app.lhr.life` in trên màn hình gửi cho người khác truy cập *(hỗ trợ sẵn HTTPS để điện thoại mở được tính năng **Chụp bằng camera**)*.

---

## 5. Tài khoản thử nghiệm & Kiểm thử

| Vai trò | Số điện thoại / Tài khoản | Mật khẩu |
|---|---|---|
| **Khách hàng** | `0912345678` (hoặc `khachhang`) | `123456` |
| **Quản trị viên** | `0900000001` (hoặc `admin`) | `admin123` |

Chạy kiểm thử tự động 22 Test Cases (`TC01`–`TC22`):

```powershell
pytest tests/test_tramxanh_tc01_tc22.py -v
```
*(Lưu ý: `pytest` sẽ reset lại dữ liệu mẫu trong `TramXanhDB` sau khi chạy xong.)*
