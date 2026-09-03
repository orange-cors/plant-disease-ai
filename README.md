# 🌿 Hệ Thống Nhận Diện Bệnh Cây Trồng Bằng Trí Tuệ Nhân Tạo (AI Plant Disease Detection)
> **"Chẩn đoán chính xác - Canh tác an tâm"**

Dự án này là một ứng dụng Web tích hợp Trí tuệ Nhân tạo (AI) giúp nhận diện và chẩn đoán các loại bệnh phổ biến trên lá cây trồng (gia súc, gia cầm có thể mở rộng sau). Bằng cách người dùng tải ảnh lên, hệ thống sẽ phân tích, đưa ra dự đoán top 5 loại bệnh, mức độ tự tin và hiển thị bản đồ nhiệt (Grad-CAM) để giải thích vùng bị tổn thương trên lá.

---

## Công nghệ sử dụng
- **Trí tuệ nhân tạo (AI/Deep Learning):** PyTorch, ResNet18 (Transfer Learning), Grad-CAM (Trực quan hóa).
- **Backend API:** FastAPI, Uvicorn, Python.
- **Frontend:** HTML5, CSS3, Vanilla JavaScript, Fetch API (Triển khai trên GitHub Pages).
- **Công cụ hỗ trợ:** Ngrok (Public Tunneling), Draw.io (Sơ đồ kiến trúc).

---

## Dữ liệu huấn luyện (Dataset)
Hệ thống sử dụng bộ dữ liệu lai (Hybrid Dataset) được gộp từ 2 nguồn:
1. **PlantVillage:** Ảnh chụp lá cây trong điều kiện phòng thí nghiệm (nền trơn, ánh sáng chuẩn).
2. **PlantDoc:** Ảnh chụp lá cây trong điều kiện thực tế ngoài đồng ruộng (bối cảnh phức tạp).

**Quy mô dữ liệu:** Tổng cộng **54.305** bức ảnh.
- Tập huấn luyện (Training): `43.444` ảnh
- Tập xác thực (Validation): `5.430` ảnh
- Tập kiểm thử (Test): `5.431` ảnh

*(Ghi chú: Quá trình trộn dữ liệu được tự động hóa thông qua script `scripts/merge_data.py`)*.

---

## Cấu trúc thư mục

```text
plant-disease-ai/
├── data/                       # Dữ liệu gốc (đã được cấu hình trong .gitignore)
├── docs/                       # Tài liệu báo cáo, sơ đồ kiến trúc
├── frontend/                   # Giao diện người dùng (HTML/CSS/JS)
├── models/                     # Trọng số mô hình đã train (ví dụ: resnet18_phase2_best.pth)
├── notebooks/                  # Các file Jupyter Notebook thử nghiệm & trực quan hóa
├── results/                    # Biểu đồ đánh giá loss, ma trận nhầm lẫn
├── scripts/                    # Các script phụ trợ (merge data, vẽ biểu đồ...)
├── src/                        # Mã nguồn cốt lõi của pipeline AI
│   ├── dataset.py
│   ├── disease_database.py
│   ├── evaluate.py
│   ├── gradcam.py
│   ├── load_model.py
│   ├── model.py
│   ├── train.py
│   └── utils.py
├── app.py                      # Điểm khởi chạy FastAPI Backend
├── diseases.json               # Cơ sở dữ liệu thông tin bệnh học và cách phòng ngừa
├── README.md
└── requirements.txt            # Danh sách thư viện cần thiết

Hướng dẫn cài đặt và chạy thử (Local & Public)

Bước 1: Cài đặt môi trường
Đảm bảo bạn đã cài đặt Python (khuyên dùng bản 3.10+). Mở Terminal tại thư mục gốc của dự án:

# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo (Windows)
.\venv\Scripts\activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt

Bước 2: Khởi động Backend (FastAPI)
Đảm bảo file trọng số mô hình .pth đã có trong thư mục models/. Chạy lệnh sau để bật server API:
uvicorn app:app --reload
API sẽ chạy tại địa chỉ: http://127.0.0.1:8000.

Bước 3: Chạy Frontend
frontend/index.html và chọn Open with Live Server.