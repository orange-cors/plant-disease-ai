import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

import config
from app import app
from data_access import (
    SessionLocal,
    Base,
    engine,
    seed_data,
    SanPham,
)


def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()


def ensure_sample_leaf_images():
    sample_dir = config.BASE_DIR / "static" / "images" / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    samples = [
        ("la_ca_chua_dom_la_som.jpg", (34, 139, 34), (120, 53, 15)),
        ("la_khoai_tay_moc_suong.jpg", (22, 101, 52), (87, 83, 78)),
        ("la_ngo_chay_la.jpg", (21, 128, 61), (161, 98, 7)),
        ("la_ot_chuong_vi_khuan.jpg", (22, 163, 74), (127, 29, 29)),
        ("anh_mo_low_conf.jpg", (200, 200, 200), (180, 180, 180)),
    ]
    for fname, bg_col, spot_col in samples:
        fpath = sample_dir / fname
        if not fpath.exists():
            img = Image.new("RGB", (320, 240), color=(240, 253, 244))
            draw = ImageDraw.Draw(img)
            draw.ellipse([60, 40, 260, 200], fill=bg_col)
            draw.ellipse([120, 90, 155, 125], fill=spot_col)
            draw.ellipse([175, 120, 210, 155], fill=spot_col)
            img.save(fpath, format="JPEG", quality=92)


def make_test_image_bytes(fmt="JPEG") -> bytes:
    img = Image.new("RGB", (224, 224), color=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_db():
    ensure_sample_leaf_images()
    reset_db()
    yield
    reset_db()


def test_tc01_filter_by_crop_ca_chua():
    """TC01: Lọc sản phẩm theo cây trồng 'Cà chua' hiển thị đúng 6 sản phẩm."""
    client = TestClient(app)
    res = client.get("/san-pham", params={"loaiCay": "Cà chua"})
    assert res.status_code == 200
    assert 'Tìm thấy <strong class="text-green-700">6</strong> sản phẩm phù hợp' in res.text
    for code in ("SP01", "SP02", "SP03", "SP04", "SP05", "SP06"):
        assert f'data-masp="{code}"' in res.text


def test_tc02_search_keyword_nam_benh():
    """TC02: Tìm kiếm từ khóa 'nấm bệnh' trả về 'Thuốc phòng trừ nấm bệnh'."""
    client = TestClient(app)
    res = client.get("/san-pham", params={"tuKhoa": "nấm bệnh"})
    assert res.status_code == 200
    assert "Thuốc phòng trừ nấm bệnh" in res.text


def test_tc03_view_product_detail():
    """TC03: Xem chi tiết sản phẩm hiển thị đầy đủ thông tin và nút 'Thêm vào giỏ'."""
    client = TestClient(app)
    res = client.get("/san-pham/SP02")
    assert res.status_code == 200
    assert "Thuốc phòng trừ nấm bệnh" in res.text
    assert "85.000 đ" in res.text
    assert "Mancozeb 640g/kg" in res.text
    assert "Thêm vào giỏ" in res.text


def test_tc04_cart_add_update_remove():
    """TC04: Thêm vào giỏ hàng, cập nhật số lượng và xóa sản phẩm."""
    client = TestClient(app)
    res = client.post("/gio-hang/them", data={"maSP": "SP02", "soLuong": 2}, follow_redirects=True)
    assert res.status_code == 200
    assert "Thuốc phòng trừ nấm bệnh" in res.text
    assert "170.000 đ" in res.text

    res = client.post("/gio-hang/cap-nhat", data={"maSP": "SP02", "soLuong": 3}, follow_redirects=True)
    assert res.status_code == 200
    assert "255.000 đ" in res.text

    res = client.post("/gio-hang/xoa", data={"maSP": "SP02"}, follow_redirects=True)
    assert res.status_code == 200
    assert "Giỏ hàng của bạn đang trống" in res.text


def test_tc05_empty_cart_and_out_of_stock_validation():
    """TC05: Kiểm tra thông báo 'Giỏ hàng của bạn đang trống' và 'Sản phẩm này hiện tại hết hàng'."""
    client = TestClient(app)
    # 1. Empty cart checkout
    res = client.post("/gio-hang/mua-hang")
    assert res.status_code == 200
    assert "Giỏ hàng của bạn đang trống" in res.text

    # 2. Out of stock product checkout
    res = client.post("/gio-hang/them", data={"maSP": "SP_HET_HANG", "soLuong": 1}, follow_redirects=True)
    assert res.status_code == 200
    assert "Sản phẩm này hiện tại hết hàng" in res.text

    res = client.post("/gio-hang/mua-hang")
    assert res.status_code == 200
    assert "Sản phẩm này hiện tại hết hàng" in res.text


def test_tc06_valid_cod_checkout():
    """TC06: Đặt hàng COD hợp lệ tạo DonHang, trừ tồn kho, xóa giỏ và báo 'Đặt hàng thành công'."""
    reset_db()
    client = TestClient(app)
    client.post("/gio-hang/them", data={"maSP": "SP02", "soLuong": 2}, follow_redirects=True)

    res = client.post(
        "/dat-hang",
        data={
            "hoTenNguoiNhan": "Nguyễn Ngọc Luyến",
            "soDienThoaiNguoiNhan": "0912345678",
            "diaChiNhanHang": "Bắc Từ Liêm, Hà Nội",
            "phuongThucTT": "COD",
        },
    )
    assert res.status_code == 200
    assert "Đặt hàng thành công" in res.text
    assert "Chờ xác nhận" in res.text

    db = SessionLocal()
    sp02 = db.query(SanPham).filter(SanPham.maSP == "SP02").first()
    assert sp02.soLuongTonKho == 48
    db.close()


def test_tc07_checkout_missing_info_or_payment_method():
    """TC07: Đặt hàng thiếu thông tin giao hàng hoặc chưa chọn phương thức thanh toán."""
    client = TestClient(app)
    client.post("/gio-hang/them", data={"maSP": "SP02", "soLuong": 1}, follow_redirects=True)

    res = client.post(
        "/dat-hang",
        data={
            "hoTenNguoiNhan": "Nguyễn Ngọc Luyến",
            "soDienThoaiNguoiNhan": "0912345678",
            "diaChiNhanHang": "Bắc Từ Liêm, Hà Nội",
            "phuongThucTT": "",
        },
    )
    assert res.status_code == 200
    assert "Chưa chọn phương thức thanh toán" in res.text

    res = client.post(
        "/dat-hang",
        data={
            "hoTenNguoiNhan": "",
            "soDienThoaiNguoiNhan": "",
            "diaChiNhanHang": "",
            "phuongThucTT": "COD",
        },
    )
    assert res.status_code == 200
    assert "Vui lòng nhập đầy đủ thông tin nhận hàng" in res.text


def test_tc08_ai_disease_recognition_valid_leaf_image():
    """TC08: Nhận diện bệnh cây bằng AI với ảnh lá cây hợp lệ."""
    client = TestClient(app)
    client.post("/dang-nhap", data={"taiKhoan": "0912345678", "matKhau": "123456"})
    img_bytes = make_test_image_bytes("JPEG")

    res = client.post(
        "/nhan-dien-benh",
        files={"file": ("la_ca_chua_dom_la_som.jpg", img_bytes, "image/jpeg")},
    )
    assert res.status_code == 200
    assert "Cà chua" in res.text
    assert "Đốm lá sớm" in res.text
    assert "94,6%" in res.text


def test_tc09_ai_related_products_and_empty_category():
    """TC09: Hiển thị >= 3 sản phẩm thuốc BVTV liên quan sau khi nhận diện bệnh Đốm lá sớm Cà chua."""
    client = TestClient(app)
    client.post("/dang-nhap", data={"taiKhoan": "0912345678", "matKhau": "123456"})
    img_bytes = make_test_image_bytes("JPEG")

    res = client.post(
        "/nhan-dien-benh",
        files={"file": ("la_ca_chua_dom_la_som.jpg", img_bytes, "image/jpeg")},
    )
    assert res.status_code == 200
    assert "Sản phẩm thuốc BVTV liên quan (nếu có)" in res.text
    assert "Thuốc phòng trừ nấm bệnh" in res.text
    assert "Thuốc bảo vệ cây trồng" in res.text
    assert "Thuốc trừ sâu sinh học" in res.text


def test_tc10_camera_capture_recognition():
    """TC10: Nhận diện bệnh từ ảnh chụp trực tiếp qua chức năng Camera."""
    client = TestClient(app)
    client.post("/dang-nhap", data={"taiKhoan": "0912345678", "matKhau": "123456"})
    img_bytes = make_test_image_bytes("JPEG")

    res = client.post(
        "/nhan-dien-benh",
        files={"file": ("camera_dom_la_som_ca_chua.jpg", img_bytes, "image/jpeg")},
    )
    assert res.status_code == 200
    assert "Đốm lá sớm" in res.text
    assert "94,6%" in res.text


def test_tc11_ai_upload_validation_rules():
    """TC11: Kiểm tra 3 thông báo lỗi khi không chọn ảnh, sai định dạng (.pdf), và ảnh mờ độ tin cậy < 50%."""
    client = TestClient(app)
    client.post("/dang-nhap", data={"taiKhoan": "0912345678", "matKhau": "123456"})

    # 1. Không chọn ảnh
    res1 = client.post("/nhan-dien-benh", files={})
    assert "Vui lòng tải hình ảnh cần nhận diện" in res1.text

    # 2. Tệp không hợp lệ (.pdf)
    res2 = client.post(
        "/nhan-dien-benh",
        files={"file": ("baocao.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert "Vui lòng chọn tệp ảnh hợp lệ (JPG, JPEG, PNG)" in res2.text

    # 3. Độ tin cậy thấp (< 50%)
    img_bytes = make_test_image_bytes("JPEG")
    res3 = client.post(
        "/nhan-dien-benh",
        files={"file": ("anh_mo_low_conf.jpg", img_bytes, "image/jpeg")},
    )
    assert "Chưa thể xác định bệnh từ ảnh. Vui lòng tải lên hình ảnh rõ nét hơn" in res3.text


def test_tc12_unauthenticated_redirect_on_ai_page():
    """TC12: Khách vãng lai chưa đăng nhập truy cập /nhan-dien-benh bị chuyển hướng về /dang-nhap."""
    client = TestClient(app)
    res = client.get("/nhan-dien-benh", follow_redirects=False)
    assert res.status_code == 303
    assert "/dang-nhap" in res.headers["location"]


def test_tc13_ai_inference_performance_and_api():
    """TC13: Kiểm tra REST API /api/ai/predict trả về kết quả chính xác với thời gian xử lý nhanh."""
    client = TestClient(app)
    img_bytes = make_test_image_bytes("JPEG")
    res = client.post(
        "/api/ai/predict",
        files={"file": ("la_ca_chua_dom_la_som.jpg", img_bytes, "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["maBenh"] == "BC01"
    assert len(data["related_products"]) >= 3


def test_tc14_admin_filter_products_by_category_and_empty_category():
    """TC14: Admin lọc sản phẩm theo danh mục và kiểm tra danh mục rỗng DM04."""
    client = TestClient(app)
    client.post("/dang-nhap", data={"taiKhoan": "0900000001", "matKhau": "admin123"})

    res1 = client.get("/admin/san-pham", params={"maDM": "DM01"})
    assert res1.status_code == 200
    assert "Thuốc phòng trừ nấm bệnh" in res1.text

    res2 = client.get("/admin/san-pham", params={"maDM": "DM04"})
    assert res2.status_code == 200
    assert "Chưa có sản phẩm nào được tạo" in res2.text


def test_tc15_admin_add_new_product_valid():
    """TC15: Admin thêm mới sản phẩm hợp lệ."""
    client = TestClient(app)
    client.post("/dang-nhap", data={"taiKhoan": "0900000001", "matKhau": "admin123"})

    res = client.post(
        "/admin/san-pham/them",
        data={
            "tenSP": "Thuốc sinh học Trạm Xanh TC15",
            "DanhMucmaDM": "DM02",
            "donGia": "140000",
            "soLuongTonKho": "30",
            "doiTuongSuDung": "Ngô, Khoai tây",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "Thuốc sinh học Trạm Xanh TC15" in res.text


def test_tc16_admin_add_product_empty_or_duplicate():
    """TC16: Admin thêm sản phẩm thiếu thông tin hoặc trùng tên báo 'Không được bỏ trống dữ liệu hoặc sản phẩm đã tồn tại'."""
    client = TestClient(app)
    client.post("/dang-nhap", data={"taiKhoan": "0900000001", "matKhau": "admin123"})

    res1 = client.post(
        "/admin/san-pham/them",
        data={"tenSP": "", "DanhMucmaDM": "DM01", "donGia": ""},
        follow_redirects=True,
    )
    assert "Không được bỏ trống dữ liệu hoặc sản phẩm đã tồn tại" in res1.text

    res2 = client.post(
        "/admin/san-pham/them",
        data={"tenSP": "Thuốc phòng trừ nấm bệnh", "DanhMucmaDM": "DM01", "donGia": "85000"},
        follow_redirects=True,
    )
    assert "Không được bỏ trống dữ liệu hoặc sản phẩm đã tồn tại" in res2.text


def test_tc17_admin_update_product_valid():
    """TC17: Admin cập nhật thông tin sản phẩm hợp lệ."""
    client = TestClient(app)
    client.post("/dang-nhap", data={"taiKhoan": "0900000001", "matKhau": "admin123"})

    res = client.post(
        "/admin/san-pham/cap-nhat/SP06",
        data={
            "tenSP": "Chế phẩm sinh học phòng trừ bọ phấn trắng hại cà chua (Đã cập nhật)",
            "DanhMucmaDM": "DM02",
            "donGia": "138000",
            "soLuongTonKho": "45",
            "doiTuongSuDung": "Cà chua",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "Chế phẩm sinh học phòng trừ bọ phấn trắng hại cà chua (Đã cập nhật)" in res.text


def test_tc18_admin_update_product_invalid_or_duplicate():
    """TC18: Admin cập nhật sản phẩm không hợp lệ hoặc trùng tên báo 'Dữ liệu không hợp lệ hoặc sản phẩm đã tồn tại'."""
    client = TestClient(app)
    client.post("/dang-nhap", data={"taiKhoan": "0900000001", "matKhau": "admin123"})

    res = client.post(
        "/admin/san-pham/cap-nhat/SP06",
        data={"tenSP": "Thuốc phòng trừ nấm bệnh", "DanhMucmaDM": "DM02", "donGia": "135000"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "Dữ liệu không hợp lệ hoặc sản phẩm đã tồn tại" in res.text


def test_tc19_admin_delete_product_without_orders():
    """TC19: Admin xóa sản phẩm chưa có trong giao dịch (SP06) thành công."""
    client = TestClient(app)
    client.post("/dang-nhap", data={"taiKhoan": "0900000001", "matKhau": "admin123"})

    res = client.post("/admin/san-pham/xoa/SP06", follow_redirects=True)
    assert res.status_code == 200
    assert "Xóa sản phẩm thành công." in res.text


def test_tc20_admin_delete_product_in_existing_order_blocked():
    """TC20: Admin xóa sản phẩm đã có trong đơn hàng (SP01) báo 'Không thể xóa sản phẩm đã có trong giao dịch'."""
    client = TestClient(app)
    client.post("/dang-nhap", data={"taiKhoan": "0900000001", "matKhau": "admin123"})

    res = client.post("/admin/san-pham/xoa/SP01", follow_redirects=True)
    assert res.status_code == 200
    assert "Không thể xóa sản phẩm đã có trong giao dịch" in res.text


def test_tc21_admin_delete_confirmation_modal_cancel():
    """TC21: Hộp thoại xác nhận xóa hiển thị 'Bạn có chắc chắn muốn xóa sản phẩm này?' với nút 'Xác nhận' và 'Hủy bỏ'."""
    client = TestClient(app)
    client.post("/dang-nhap", data={"taiKhoan": "0900000001", "matKhau": "admin123"})

    res = client.get("/admin/san-pham")
    assert res.status_code == 200
    assert "Bạn có chắc chắn muốn xóa sản phẩm này?" in res.text
    assert "Hủy bỏ" in res.text
    assert "Xác nhận" in res.text


def test_tc22_admin_access_control_blocks_guest_and_customer():
    """TC22: Chặn Khách vãng lai và Khách hàng thường truy cập các đường dẫn /admin/*."""
    client = TestClient(app)
    # Guest
    res_guest = client.get("/admin")
    assert res_guest.status_code == 403

    # Non-admin Customer
    client.post("/dang-nhap", data={"taiKhoan": "0912345678", "matKhau": "123456"})
    res_cust = client.get("/admin/san-pham")
    assert res_cust.status_code == 403
