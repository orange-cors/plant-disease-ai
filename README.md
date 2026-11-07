# TramXanh - Website Phân Phối Thuốc Bảo Vệ Thực Vật Tích Hợp AI Nhận Diện Bệnh Cây Hoa Màu Ở Đồng Bằng Sông Hồng

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Architecture](https://img.shields.io/badge/Architecture-3--Tier-15803d)
![Database](https://img.shields.io/badge/Database-SQL%20Server%20%7C%20SQLite-0f766e)
![AI](https://img.shields.io/badge/AI-ResNet18%20Local%20Inference-ee4c2c)

**TramXanh** là hệ thống website thương mại điện tử chuyên phân phối thuốc bảo vệ thực vật (BVTV) kết hợp mô hình Học sâu (Deep Learning) nhận diện bệnh trên lá 4 loại cây hoa màu phổ biến tại vùng Đồng bằng sông Hồng: **Cà chua, Khoai tây, Ớt chuông, Ngô**.

---

## 1. Kiến trúc hệ thống (3-Tier Architecture + AI Service)

Dự án tuân thủ nghiêm ngặt kiến trúc **3 tầng (3-Tier Architecture)** tách biệt rõ ràng:

```text
plant-disease-ai/
├── templates/                      # [Tầng 1: Presentation / UI Layer] Giao diện HTML5 + TailwindCSS (Jinja2)
│   ├── base.html                   # Layout chung, Header, Thanh tìm kiếm, Giỏ hàng, Flash Alert
│   ├── index.html                  # Trang chủ (/): Banner, 4 thẻ cây trồng, Sản phẩm nổi bật
│   ├── san_pham.html               # Trang danh sách & Bộ lọc sản phẩm (/san-pham)
│   ├── chi_tiet_san_pham.html      # Trang chi tiết sản phẩm (/san-pham/<maSP>)
│   ├── gio_hang.html               # Trang giỏ hàng (/gio-hang)
│   ├── dat_hang.html               # Trang đặt hàng COD (/dat-hang)
│   ├── nhan_dien_benh.html         # Trang nhận diện bệnh cây bằng AI + Camera (/nhan-dien-benh)
│   ├── dang_nhap.html              # Trang đăng nhập (/dang-nhap)
│   ├── dang_ky.html                # Trang đăng ký (/dang-ky)
│   ├── tai_khoan.html              # Trang thông tin cá nhân & Lịch sử đơn hàng (/tai-khoan)
│   ├── 403.html                    # Trang cảnh báo phân quyền (403 Forbidden)
│   └── admin/                      # Giao diện Quản trị viên (/admin/*)
│       ├── dashboard.html          # 4 thẻ quản trị chính (/admin)
│       ├── san_pham.html           # CRUD Sản phẩm + Lọc danh mục (/admin/san-pham)
│       ├── danh_muc.html           # Quản lý danh mục (/admin/danh-muc)
│       ├── don_hang.html           # Quản lý đơn hàng COD (/admin/don-hang)
│       └── khach_hang.html         # Tra cứu khách hàng (/admin/khach-hang)
├── controllers/                    # [Tầng 2: Business Logic / Controller Layer]
│   ├── __init__.py
│   └── tramxanh_controllers.py     # TaiKhoanController, SanPhamController, GioHangController, DonHangController, NhanDienBenhController
├── data_access/                    # [Tầng 3: Data Access / Repository Layer]
│   ├── __init__.py
│   ├── models_db.py                # 9 bảng ORM chuẩn ERD: NguoiDung, DanhMuc, SanPham, GioHang, ChiTietGioHang, DonHang, ChiTietDonHang (DonHang_SanPham), BenhCay, BenhCay_SanPham
│   ├── database.py                 # Kết nối SQL Server (pyodbc/SQLAlchemy) + Tự động khởi tạo & Seed dữ liệu (kèm SQLite fallback)
│   └── repositories.py             # Các lớp Repository truy vấn CSDL
├── ai_service.py                   # [AI Module] AIService tải mô hình AI cục bộ (.pth/.pt, .h5, .onnx) & ánh xạ CLASS_MAPPING -> maBenh
├── database_setup.sql              # Script T-SQL khởi tạo CSDL TramXanhDB và dữ liệu mẫu trên Microsoft SQL Server
├── models/                         # Chứa trọng số mô hình AI đã huấn luyện
│   └── resnet18_phase2_best.pth    # Mô hình ResNet18 phân loại bệnh lá cây
├── static/                         # Tài nguyên tĩnh (Ảnh sản phẩm SVG, ảnh lá cây người dùng tải lên)
├── tests/                          # Kiểm thử tự động toàn bộ 22 Test Cases
│   └── test_tramxanh_tc01_tc22.py  # Script kiểm thử tự động TC01 -> TC22
├── config.py                       # Cấu hình tập trung đọc từ .env
├── .env                            # Biến môi trường (Kết nối SQL Server, đường dẫn MODEL_PATH)
├── app.py                          # Điểm khởi chạy Web Server (FastAPI + Uvicorn)
└── requirements.txt                # Danh sách thư viện Python
```

---

## 2. Hướng dẫn cài đặt và chạy chương trình

### Bước 1: Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### Bước 2: Cấu hình Cơ sở dữ liệu (SQL Server hoặc Tự động)
Hệ thống hỗ trợ 2 chế độ cơ sở dữ liệu thông qua tệp `.env`:
1. **Kết nối Microsoft SQL Server**:
   - Mở **SQL Server Management Studio (SSMS)** và chạy tệp `database_setup.sql` để tạo CSDL `TramXanhDB`, 9 bảng vật lý và toàn bộ dữ liệu mẫu.
   - Trong tệp `.env`, cấu hình:
     ```env
     DB_MODE=auto
     MSSQL_SERVER=localhost
     MSSQL_DATABASE=TramXanhDB
     MSSQL_DRIVER=SQL Server
     ```
2. **Tự động khởi tạo (Auto Fallback)**:
   - Khi `DB_MODE=auto` (mặc định), ứng dụng tự động thử kết nối tới SQL Server trước. Nếu dịch vụ SQL Server chưa bật trên máy, hệ thống tự động chuyển sang cơ sở dữ liệu cục bộ `tramxanh.db` và **tự động tạo bảng + nạp toàn bộ dữ liệu mẫu (Seed Data)** ngay khi khởi động.

### Bước 3: Cấu hình Mô hình AI cục bộ (`ai_service.py`)
Trong tệp `.env` và `ai_service.py`:
- `MODEL_PATH=models/resnet18_phase2_best.pth`: Đường dẫn tới tệp trọng số mô hình học sâu trên máy cục bộ (hỗ trợ PyTorch `.pth`/`.pt`, TensorFlow/Keras `.h5`/`.keras`, hoặc `.onnx`).
- `IMAGE_SIZE=224`: Kích thước ảnh đầu vào `(224, 224)`.
- `CONFIDENCE_THRESHOLD=0.50`: Ngưỡng độ tin cậy tối thiểu (`50%`). Nếu độ tin cậy dự đoán `< 50%`, hệ thống trả về thông báo: *"Chưa thể xác định bệnh từ ảnh. Vui lòng tải lên hình ảnh rõ nét hơn"*.
- `CLASS_MAPPING`: Từ điển ánh xạ nhãn lớp dự đoán của mô hình sang mã bệnh `maBenh` (`BC01` đến `BC14`) trong bảng `BenhCay`.

### Bước 4: Khởi chạy Web Server
```bash
python app.py
```
Truy cập ứng dụng trên trình duyệt tại địa chỉ: **`http://127.0.0.1:8000`**

---

## 3. Tài khoản thử nghiệm (Seed Data)

| Vai trò | Số điện thoại / Tài khoản | Mật khẩu | Họ và tên | Ghi chú |
|---|---|---|---|---|
| **Quản trị viên (`QuanTriVien`)** | `0900000001` (hoặc `admin`) | `admin123` | Quản Trị Viên Trạm Xanh | Toàn quyền truy cập `/admin` và CRUD sản phẩm |
| **Khách hàng (`KhachHang`)** | `0912345678` (hoặc `khachhang`) | `123456` | Nguyễn Ngọc Luyến | Sử dụng AI nhận diện bệnh (`/nhan-dien-benh`), mua hàng COD |

---

## 4. Kiểm thử nghiệm thu (Test Cases TC01 – TC22)

Chạy kiểm thử tự động toàn bộ 22 kịch bản kiểm thử bằng lệnh:
```bash
pytest tests/test_tramxanh_tc01_tc22.py -v
```

| Mã TC | Nội dung kiểm thử | Kết quả đạt được trên hệ thống |
|---|---|---|
| **TC01** | Lọc sản phẩm theo cây trồng `"Cà chua"` | Hiển thị đúng **6 sản phẩm** (`SP01` đến `SP06`) dành cho cây Cà chua |
| **TC02** | Tìm kiếm từ khóa `"nấm bệnh"` | Hiển thị `"Thuốc phòng trừ nấm bệnh"` và các sản phẩm trừ nấm liên quan |
| **TC03** | Xem chi tiết sản phẩm (`/san-pham/SP02`) | Hiển thị đầy đủ tên, giá `85.000 đ`, tồn kho, thành phần, công dụng, HDSD |
| **TC04** | Thêm vào giỏ hàng, tăng/giảm số lượng, xóa sản phẩm | Cập nhật chính xác số lượng và tổng tiền trong giỏ hàng |
| **TC05** | Mua hàng khi giỏ trống hoặc có sản phẩm hết hàng (`SP_HET_HANG`) | Báo đúng thông báo: **"Giỏ hàng của bạn đang trống"** hoặc **"Sản phẩm này hiện tại hết hàng"** |
| **TC06** | Đặt hàng COD hợp lệ (`/dat-hang`) | Tạo đơn hàng trạng thái `Chờ xác nhận`, trừ tồn kho, xóa giỏ, báo **"Đặt hàng thành công"** |
| **TC07** | Đặt hàng thiếu thông tin nhận hàng hoặc chưa chọn PTTT | Báo lỗi thông tin giao hàng hoặc **"Chưa chọn phương thức thanh toán"** |
| **TC08** | Nhận diện bệnh từ ảnh lá cây hợp lệ (`/nhan-dien-benh`) | Hiển thị `Cà chua` - `Đốm lá sớm` (`94,6%`), triệu chứng và biện pháp điều trị |
| **TC09** | Gợi ý thuốc BVTV liên quan sau khi nhận diện AI / Danh mục trống | Hiển thị `>= 3` sản phẩm thuốc liên kết (`SP02`, `SP03`, `SP04`, `SP01`); danh mục `DM04` báo **"Chưa có sản phẩm nào được tạo"** |
| **TC10** | Chụp ảnh lá cây trực tiếp bằng Camera | Mở modal Camera trực tiếp, chụp ảnh, xem trước và gửi nhận diện thành công |
| **TC11** | Kiểm tra lỗi tải ảnh AI (Không chọn ảnh / File `.pdf` / Ảnh mờ `<50%`) | Hiển thị chính xác: **"Vui lòng tải hình ảnh cần nhận diện"**, **"Vui lòng chọn tệp ảnh hợp lệ (JPG, JPEG, PNG)"**, **"Chưa thể xác định bệnh từ ảnh. Vui lòng tải lên hình ảnh rõ nét hơn"** |
| **TC12** | Khách vãng lai chưa đăng nhập truy cập `/nhan-dien-benh` | Chuyển hướng ngay lập tức về trang `/dang-nhap` |
| **TC13** | Tốc độ phản hồi nhận diện AI (NFR02) | Thời gian xử lý `< 1 giây` |
| **TC14** | Admin lọc danh sách sản phẩm theo danh mục (`/admin/san-pham`) | Hiển thị đúng các sản phẩm thuộc danh mục được chọn |
| **TC15** | Admin thêm mới sản phẩm hợp lệ | Lưu sản phẩm mới vào CSDL và hiển thị trong danh sách |
| **TC16** | Admin thêm sản phẩm bỏ trống hoặc trùng tên | Hiển thị chính xác: **"Không được bỏ trống dữ liệu hoặc sản phẩm đã tồn tại"** |
| **TC17** | Admin chỉnh sửa cập nhật sản phẩm hợp lệ | Cập nhật thông tin sản phẩm thành công |
| **TC18** | Admin cập nhật sản phẩm dữ liệu rỗng/sai hoặc trùng tên | Hiển thị chính xác: **"Dữ liệu không hợp lệ hoặc sản phẩm đã tồn tại"** |
| **TC19** | Admin xóa sản phẩm chưa phát sinh giao dịch (`SP06`) | Xóa thành công khỏi `BenhCay_SanPham`, `ChiTietGioHang`, `SanPham` |
| **TC20** | Admin xóa sản phẩm đã có trong đơn hàng (`SP01` trong `DH01`) | Chặn xóa và hiển thị chính xác: **"Không thể xóa sản phẩm đã có trong giao dịch"** |
| **TC21** | Admin nhấn nút xóa nhưng chọn `"Hủy bỏ"` trên hộp thoại xác nhận | Hộp thoại hiển thị **"Bạn có chắc chắn muốn xóa sản phẩm này?"**, nhấn `"Hủy bỏ"` đóng hộp thoại và giữ nguyên sản phẩm |
| **TC22** | Khách vãng lai hoặc Khách hàng thường truy cập `/admin/*` | Chặn truy cập (HTTP 403 Forbidden) |
