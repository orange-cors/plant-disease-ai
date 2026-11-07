from datetime import date
from urllib.parse import quote_plus
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import config
from .models_db import (
    Base,
    NguoiDung,
    DanhMuc,
    SanPham,
    GioHang,
    ChiTietGioHang,
    DonHang,
    ChiTietDonHang,
    BenhCay,
    BenhCay_SanPham,
)


def hash_password(raw_password: str) -> str:
    """Hash password using bcrypt (NFR05)."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(raw_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(raw_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash, werkzeug hash, or SQL script placeholder."""
    if not raw_password or not hashed_password:
        return False
    # Handle SQL script seeded placeholder hashes if SQL script was run directly
    if hashed_password == "$2b$12$KIX/hashed_by_app_init_admin123":
        return raw_password == "admin123"
    if hashed_password == "$2b$12$KIX/hashed_by_app_init_123456":
        return raw_password == "123456"
    try:
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
            return bcrypt.checkpw(raw_password.encode("utf-8"), hashed_password.encode("utf-8"))
        return check_password_hash(hashed_password, raw_password)
    except Exception:
        return raw_password == hashed_password


def _build_engine():
    """Build SQLAlchemy engine for SQL Server with automatic fallback to SQLite."""
    if config.DATABASE_URL_ENV:
        try:
            eng = create_engine(config.DATABASE_URL_ENV, pool_pre_ping=True)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            return eng, "SQL Server (DATABASE_URL)"
        except Exception as e:
            if config.DB_MODE == "mssql":
                raise RuntimeError(f"Không thể kết nối SQL Server qua DATABASE_URL: {e}")

    if config.DB_MODE in ("mssql", "auto"):
        odbc_str = (
            f"DRIVER={{{config.MSSQL_DRIVER}}};"
            f"SERVER={config.MSSQL_SERVER};"
            f"DATABASE={config.MSSQL_DATABASE};"
            f"Trusted_Connection=yes;"
        )
        mssql_url = f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_str)}"
        try:
            eng = create_engine(mssql_url, pool_pre_ping=True, connect_args={"timeout": 2})
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            return eng, f"SQL Server ({config.MSSQL_SERVER}/{config.MSSQL_DATABASE})"
        except Exception as e:
            if config.DB_MODE == "mssql":
                raise RuntimeError(f"Không thể kết nối SQL Server: {e}")

    sqlite_url = f"sqlite:///{config.SQLITE_PATH}"
    eng = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    return eng, f"SQLite Fallback ({config.SQLITE_PATH.name})"


engine, ACTIVE_DB_BACKEND = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_data(session):
    """Idempotently seed all required accounts, categories, products, diseases, and sample orders."""
    # 1. Seed NguoiDung
    if session.query(NguoiDung).count() == 0:
        users = [
            NguoiDung(
                maND="ND01",
                hoTen="Quản Trị Viên Trạm Xanh",
                matKhau=hash_password("admin123"),
                soDienThoai="0900000001",
                gioiTinh="Nam",
                ngaySinh=date(1990, 1, 1),
                diaChiNhanHang="Số 1 Đại Cồ Việt, Hai Bà Trưng, Hà Nội",
                vaiTro="QuanTriVien",
            ),
            NguoiDung(
                maND="ND02",
                hoTen="Nguyễn Ngọc Luyến",
                matKhau=hash_password("123456"),
                soDienThoai="0912345678",
                gioiTinh="Nữ",
                ngaySinh=date(2003, 5, 15),
                diaChiNhanHang="Bắc Từ Liêm, Hà Nội",
                vaiTro="KhachHang",
            ),
            NguoiDung(
                maND="ND03",
                hoTen="Trần Văn Nông",
                matKhau=hash_password("123456"),
                soDienThoai="0987654321",
                gioiTinh="Nam",
                ngaySinh=date(1985, 8, 20),
                diaChiNhanHang="Gia Lâm, Hà Nội",
                vaiTro="KhachHang",
            ),
        ]
        session.add_all(users)
        session.flush()

    # 2. Seed DanhMuc (DM04 kept empty with 0 products for TC09 / Branch 4.1)
    if session.query(DanhMuc).count() == 0:
        categories = [
            DanhMuc(
                maDM="DM01",
                tenDM="Thuốc trừ nấm bệnh",
                moTa="Các dòng thuốc đặc trị nấm bệnh, mốc sương, đốm lá, gỉ sắt trên cây hoa màu.",
            ),
            DanhMuc(
                maDM="DM02",
                tenDM="Thuốc trừ sâu sinh học",
                moTa="Chế phẩm sinh học an toàn giúp tiêu diệt sâu tơ, sâu xanh, bọ phấn trắng, nhện đỏ.",
            ),
            DanhMuc(
                maDM="DM03",
                tenDM="Thuốc đặc trị vi khuẩn & bảo vệ cây trồng",
                moTa="Thuốc phòng trị bệnh héo xanh vi khuẩn, đốm vi khuẩn và tăng sức đề kháng cây trồng.",
            ),
            DanhMuc(
                maDM="DM04",
                tenDM="Chế phẩm vi sinh mới",
                moTa="Danh mục các dòng chế phẩm vi sinh thế hệ mới (Chưa có sản phẩm).",
            ),
        ]
        session.add_all(categories)
        session.flush()

    # 3. Seed SanPham (Exact 6 products for 'Cà chua' -> SP01..SP06 for TC01; SP_HET_HANG with stock 0 for TC05)
    if session.query(SanPham).count() == 0:
        products = [
            SanPham(
                maSP="SP01",
                tenSP="Thuốc trừ sâu sinh học",
                hinhAnh="/static/images/sp01.svg",
                donGia=120000,
                soLuongTonKho=50,
                congDung="Đặc trị sâu xanh, sâu tơ, bọ trĩ, nhện đỏ và côn trùng chích hút truyền bệnh virus trên cây hoa màu.",
                doiTuongSuDung="Cà chua, Ngô, Ớt chuông",
                huongDanSuDung="Pha 20ml cho bình 16-20 lít nước. Phun ướt đều hai mặt lá vào sáng sớm hoặc chiều mát.",
                thuongHieu="BioAgri Việt Nam",
                thanhPhan="Abamectin 1.8% w/w + Phụ gia sinh học 98.2%",
                hanSuDung=date(2028, 12, 31),
                DanhMucmaDM="DM02",
            ),
            SanPham(
                maSP="SP02",
                tenSP="Thuốc phòng trừ nấm bệnh",
                hinhAnh="/static/images/sp02.svg",
                donGia=85000,
                soLuongTonKho=50,
                congDung="Phòng và đặc trị hiệu quả bệnh đốm lá sớm, mốc sương, thán thư, nấm bệnh gây hại lá và thân.",
                doiTuongSuDung="Cà chua, Khoai tây",
                huongDanSuDung="Pha 40g cho bình 16 lít nước. Phun định kỳ 7-10 ngày/lần khi bệnh mới xuất hiện.",
                thuongHieu="Trạm Xanh CropCare",
                thanhPhan="Mancozeb 640g/kg + Metalaxyl 80g/kg",
                hanSuDung=date(2028, 6, 30),
                DanhMucmaDM="DM01",
            ),
            SanPham(
                maSP="SP03",
                tenSP="Thuốc bảo vệ cây trồng",
                hinhAnh="/static/images/sp03.svg",
                donGia=150000,
                soLuongTonKho=50,
                congDung="Bảo vệ toàn diện cây trồng trước nấm và vi khuẩn gây bệnh đốm lá, cháy lá, tăng cường đề kháng.",
                doiTuongSuDung="Cà chua, Khoai tây, Ớt chuông, Ngô",
                huongDanSuDung="Pha 25ml cho bình 20 lít nước. Phun phòng ngừa hoặc ngay khi phát hiện vết bệnh đầu tiên.",
                thuongHieu="Syngenta Việt Nam",
                thanhPhan="Azoxystrobin 200g/L + Difenoconazole 125g/L",
                hanSuDung=date(2028, 10, 15),
                DanhMucmaDM="DM03",
            ),
            SanPham(
                maSP="SP04",
                tenSP="Thuốc đặc trị mốc sương và đốm lá cà chua",
                hinhAnh="/static/images/sp04.svg",
                donGia=95000,
                soLuongTonKho=40,
                congDung="Đặc trị nấm bệnh gây đốm lá sớm (Alternaria solani) và mốc sương (Phytophthora infestans) trên cà chua và khoai tây.",
                doiTuongSuDung="Cà chua, Khoai tây",
                huongDanSuDung="Pha 30g cho bình 16 lít nước. Phun kỹ mặt dưới lá nơi bào tử nấm trú ngụ.",
                thuongHieu="VFC Nông Dược",
                thanhPhan="Chlorothalonil 75% WP",
                hanSuDung=date(2028, 9, 1),
                DanhMucmaDM="DM01",
            ),
            SanPham(
                maSP="SP05",
                tenSP="Thuốc trừ bệnh héo xanh và đốm vi khuẩn cà chua",
                hinhAnh="/static/images/sp05.svg",
                donGia=110000,
                soLuongTonKho=35,
                congDung="Tiêu diệt nhanh vi khuẩn gây bệnh đốm vi khuẩn, loét vi khuẩn và héo xanh trên cà chua, ớt chuông.",
                doiTuongSuDung="Cà chua, Ớt chuông",
                huongDanSuDung="Pha 18g cho bình 16 lít nước. Phun 2 lần cách nhau 5-7 ngày khi trời ráo.",
                thuongHieu="Lộc Trời Group",
                thanhPhan="Kasugamycin 2% + Copper Oxychloride 45%",
                hanSuDung=date(2028, 11, 20),
                DanhMucmaDM="DM03",
            ),
            SanPham(
                maSP="SP06",
                tenSP="Chế phẩm sinh học phòng trừ bọ phấn trắng hại cà chua",
                hinhAnh="/static/images/sp06.svg",
                donGia=135000,
                soLuongTonKho=45,
                congDung="Kiểm soát bọ phấn trắng môi giới truyền bệnh virus vàng xoăn lá cà chua, an toàn cho thiên địch.",
                doiTuongSuDung="Cà chua",
                huongDanSuDung="Pha 25ml cho bình 20 lít nước. Phun đều lên tán lá định kỳ 7 ngày/lần.",
                thuongHieu="EcoGreen Đồng Bằng",
                thanhPhan="Matrine 1.2% + Tinh dầu Neem tự nhiên",
                hanSuDung=date(2028, 8, 15),
                DanhMucmaDM="DM02",
            ),
            SanPham(
                maSP="SP07",
                tenSP="Thuốc đặc trị nấm mốc sương khoai tây",
                hinhAnh="/static/images/sp07.svg",
                donGia=90000,
                soLuongTonKho=60,
                congDung="Chuyên dùng phòng trừ nấm bệnh mốc sương và đốm vòng cháy lá sớm trên cây khoai tây vụ Đông.",
                doiTuongSuDung="Khoai tây",
                huongDanSuDung="Pha 35g cho bình 16 lít nước. Phun sớm khi thời tiết ẩm ướt, sương muối.",
                thuongHieu="Trạm Xanh CropCare",
                thanhPhan="Cymoxanil 8% + Mancozeb 64%",
                hanSuDung=date(2028, 5, 30),
                DanhMucmaDM="DM01",
            ),
            SanPham(
                maSP="SP08",
                tenSP="Thuốc trừ bệnh thán thư và đốm lá ớt chuông",
                hinhAnh="/static/images/sp08.svg",
                donGia=105000,
                soLuongTonKho=40,
                congDung="Đặc trị đốm vi khuẩn và nấm thán thư trên lá và quả ớt chuông.",
                doiTuongSuDung="Ớt chuông",
                huongDanSuDung="Pha 20ml cho bình 16 lít nước. Ngừng phun trước khi thu hoạch 7 ngày.",
                thuongHieu="BioAgri Việt Nam",
                thanhPhan="Copper Hydroxide 77% WP",
                hanSuDung=date(2028, 7, 20),
                DanhMucmaDM="DM03",
            ),
            SanPham(
                maSP="SP09",
                tenSP="Thuốc đặc trị cháy lá và gỉ sắt hại ngô",
                hinhAnh="/static/images/sp09.svg",
                donGia=88000,
                soLuongTonKho=70,
                congDung="Đặc trị nấm bệnh cháy lá lớn, đốm lá xám và gỉ sắt trên cây ngô vùng bãi sông Hồng.",
                doiTuongSuDung="Ngô",
                huongDanSuDung="Pha 20ml cho bình 16 lít nước. Phun khi ngô giai đoạn xoáy nõn đến trỗ cờ.",
                thuongHieu="VFC Nông Dược",
                thanhPhan="Propiconazole 250g/L EC",
                hanSuDung=date(2028, 12, 1),
                DanhMucmaDM="DM01",
            ),
            SanPham(
                maSP="SP10",
                tenSP="Thuốc trừ sâu keo mùa thu hại ngô sinh học",
                hinhAnh="/static/images/sp10.svg",
                donGia=125000,
                soLuongTonKho=55,
                congDung="Diệt trừ sâu keo mùa thu, sâu đục thân hại ngô bằng vi khuẩn sinh học Bt.",
                doiTuongSuDung="Ngô",
                huongDanSuDung="Pha 25g cho bình 16 lít nước, phun trực tiếp vào nõn ngô.",
                thuongHieu="EcoGreen Đồng Bằng",
                thanhPhan="Bacillus thuringiensis var. kurstaki 32.000 IU/mg",
                hanSuDung=date(2028, 10, 1),
                DanhMucmaDM="DM02",
            ),
            SanPham(
                maSP="SP_HET_HANG",
                tenSP="Thuốc đặc trị nấm bệnh phổ rộng (Tạm hết hàng)",
                hinhAnh="/static/images/sp_hethang.svg",
                donGia=99000,
                soLuongTonKho=0,
                congDung="Thuốc trừ nấm bệnh phổ rộng trên khoai tây, ngô và ớt chuông (Sản phẩm đang tạm hết hàng trong kho).",
                doiTuongSuDung="Khoai tây, Ngô, Ớt chuông",
                huongDanSuDung="Pha 30ml cho bình 16 lít nước.",
                thuongHieu="Trạm Xanh CropCare",
                thanhPhan="Hexaconazole 50g/L",
                hanSuDung=date(2028, 4, 1),
                DanhMucmaDM="DM01",
            ),
        ]
        session.add_all(products)
        session.flush()

    # 4. Seed BenhCay
    if session.query(BenhCay).count() == 0:
        diseases = [
            BenhCay(
                maBenh="BC01",
                tenBenh="Đốm lá sớm",
                loaiCay="Cà chua",
                trieuChung="Xuất hiện các đốm nâu sẫm có vòng đồng tâm như bia bắn trên lá già phía dưới trước, sau đó lan dần lên trên làm vàng lá và rụng sớm.",
                bienPhapDieuTri="Tỉa bỏ lá bệnh già ở gốc, luân canh cây trồng, giữ ruộng thông thoáng và phun thuốc trừ nấm hoạt chất Mancozeb, Azoxystrobin hoặc Chlorothalonil.",
            ),
            BenhCay(
                maBenh="BC02",
                tenBenh="Mốc sương",
                loaiCay="Cà chua",
                trieuChung="Vết bệnh ban đầu là các đốm xanh tái ngập nước ở mép lá, sau chuyển nâu đen. Mặt dưới lá có lớp mốc trắng mịn khi trời ẩm ướt, bệnh lan rất nhanh.",
                bienPhapDieuTri="Thoát nước tốt, không tưới phun mưa vào chiều tối, thu gom tiêu hủy cây bệnh nặng và phun ngay thuốc đặc trị Metalaxyl + Mancozeb.",
            ),
            BenhCay(
                maBenh="BC03",
                tenBenh="Đốm vi khuẩn",
                loaiCay="Cà chua",
                trieuChung="Các đốm nhỏ sũng nước màu nâu đen xuất hiện rải rác trên lá, xung quanh có quầng vàng hẹp; các đốm có thể liên kết làm cháy rách phiến lá.",
                bienPhapDieuTri="Sử dụng hạt giống sạch bệnh, hạn chế làm xây xát lá khi chăm sóc và phun thuốc gốc Đồng hoặc kháng sinh Kasugamycin.",
            ),
            BenhCay(
                maBenh="BC04",
                tenBenh="Vàng xoăn lá",
                loaiCay="Cà chua",
                trieuChung="Lá ngọn nhỏ lại, xoăn cong lên phía trên, phiến lá dày giòn và chuyển màu vàng giữa các gân lá; cây còi cọc, đốt ngắn, hoa dễ rụng.",
                bienPhapDieuTri="Nhổ bỏ cây nhiễm bệnh sớm, quây lưới chắn côn trùng và phun chế phẩm sinh học tiêu diệt bọ phấn trắng truyền virus.",
            ),
            BenhCay(
                maBenh="BC05",
                tenBenh="Lá khỏe mạnh",
                loaiCay="Cà chua",
                trieuChung="Phiến lá cà chua có màu xanh tươi đồng đều, bề mặt lá phẳng, không có vết đốm nấm, vi khuẩn hay biến dạng do virus.",
                bienPhapDieuTri="Duy trì chế độ bón phân cân đối NPK, tưới nước hợp lý và thăm đồng định kỳ để phòng ngừa sâu bệnh.",
            ),
            BenhCay(
                maBenh="BC06",
                tenBenh="Đốm vòng / Cháy lá sớm",
                loaiCay="Khoai tây",
                trieuChung="Trên lá xuất hiện những đốm tròn hoặc góc cạnh màu nâu sẫm có các vòng đồng tâm rõ rệt, mô lá xung quanh vết bệnh chuyển màu vàng.",
                bienPhapDieuTri="Bón đủ phân kali tăng sức chống chịu, vệ sinh tàn dư cây trồng và phun thuốc trừ nấm Mancozeb hoặc Chlorothalonil.",
            ),
            BenhCay(
                maBenh="BC07",
                tenBenh="Mốc sương khoai tây",
                loaiCay="Khoai tây",
                trieuChung="Mép lá và chóp lá có vết bệnh màu nâu xám như bị dội nước sôi, mặt dưới lá có lớp tơ nấm trắng xốp khi trời lạnh và sương mù.",
                bienPhapDieuTri="Lên luống cao thoát nước tốt, vun gốc kỹ và phun phòng trừ kịp thời bằng thuốc đặc trị Cymoxanil + Mancozeb.",
            ),
            BenhCay(
                maBenh="BC08",
                tenBenh="Lá khỏe mạnh",
                loaiCay="Khoai tây",
                trieuChung="Lá khoai tây xanh đậm, dày khỏe, phát triển bình thường, không có dấu hiệu đốm lá hay mốc sương.",
                bienPhapDieuTri="Tiếp tục chăm sóc, vun xới và theo dõi thời tiết sương muối để chủ động bảo vệ cây.",
            ),
            BenhCay(
                maBenh="BC09",
                tenBenh="Đốm vi khuẩn ớt chuông",
                loaiCay="Ớt chuông",
                trieuChung="Trên lá xuất hiện các đốm nhỏ màu xanh sẫm ướt, sau chuyển sang màu nâu đen, viền sẫm, lá bị bệnh nặng chuyển vàng và rụng hàng loạt.",
                bienPhapDieuTri="Tránh tưới nước lên tán lá, cắt tỉa cành lá thông thoáng và phun thuốc gốc Đồng hoặc Kasugamycin.",
            ),
            BenhCay(
                maBenh="BC10",
                tenBenh="Lá khỏe mạnh",
                loaiCay="Ớt chuông",
                trieuChung="Lá ớt chuông bóng mượt, xanh tốt, không có vết đốm hay biến dạng.",
                bienPhapDieuTri="Chăm sóc định kỳ, bổ sung canxi-bo và phòng ngừa bọ trĩ, nhện đỏ.",
            ),
            BenhCay(
                maBenh="BC11",
                tenBenh="Cháy lá ngô",
                loaiCay="Ngô",
                trieuChung="Vết bệnh hình thoi dài (hình điếu xì gà) màu xám xanh hoặc nâu nhạt, chạy dọc theo phiến lá làm khô cháy từng mảng lớn trên lá ngô.",
                bienPhapDieuTri="Gieo trồng mật độ hợp lý, vệ sinh đồng ruộng và phun thuốc đặc trị nấm Propiconazole hoặc Azoxystrobin.",
            ),
            BenhCay(
                maBenh="BC12",
                tenBenh="Gỉ sắt ngô",
                loaiCay="Ngô",
                trieuChung="Hai mặt lá xuất hiện nhiều ổ nấm nhỏ nổi gồ lên màu nâu đỏ hoặc vàng gạch như vết gỉ sắt, khi vỡ giải phóng bột bào tử màu nâu.",
                bienPhapDieuTri="Bón phân cân đối tránh thừa đạm, dọn sạch lá già dưới gốc và phun thuốc trừ nấm nhóm Triazole.",
            ),
            BenhCay(
                maBenh="BC13",
                tenBenh="Đốm lá xám",
                loaiCay="Ngô",
                trieuChung="Các vết bệnh hình chữ nhật hẹp, chạy song song với gân lá, màu nâu xám hoặc vàng nâu làm giảm diện tích quang hợp của lá.",
                bienPhapDieuTri="Luân canh với cây họ đậu, cày vùi tàn dư sau thu hoạch và sử dụng thuốc trừ nấm đặc hiệu.",
            ),
            BenhCay(
                maBenh="BC14",
                tenBenh="Lá khỏe mạnh",
                loaiCay="Ngô",
                trieuChung="Lá ngô xanh mướt, phiến lá rộng và lành lặn, không có vết cháy lá hay ổ gỉ sắt.",
                bienPhapDieuTri="Duy trì chăm sóc, bón thúc đúng thời kỳ và kiểm tra nõn ngô phòng sâu keo mùa thu.",
            ),
        ]
        session.add_all(diseases)
        session.flush()

    # 5. Seed BenhCay_SanPham
    if session.query(BenhCay_SanPham).count() == 0:
        links = [
            ("BC01", "SP02"), ("BC01", "SP03"), ("BC01", "SP04"), ("BC01", "SP01"),
            ("BC02", "SP02"), ("BC02", "SP03"), ("BC02", "SP04"),
            ("BC03", "SP05"), ("BC03", "SP03"), ("BC03", "SP02"),
            ("BC04", "SP06"), ("BC04", "SP01"), ("BC04", "SP03"),
            ("BC05", "SP03"), ("BC05", "SP01"), ("BC05", "SP06"),
            ("BC06", "SP02"), ("BC06", "SP04"), ("BC06", "SP07"),
            ("BC07", "SP07"), ("BC07", "SP02"), ("BC07", "SP04"),
            ("BC08", "SP03"), ("BC08", "SP07"), ("BC08", "SP02"),
            ("BC09", "SP08"), ("BC09", "SP05"), ("BC09", "SP03"),
            ("BC10", "SP03"), ("BC10", "SP01"), ("BC10", "SP08"),
            ("BC11", "SP09"), ("BC11", "SP03"), ("BC11", "SP10"),
            ("BC12", "SP09"), ("BC12", "SP03"), ("BC12", "SP01"),
            ("BC13", "SP09"), ("BC13", "SP03"), ("BC13", "SP10"),
            ("BC14", "SP03"), ("BC14", "SP10"), ("BC14", "SP09"),
        ]
        for ma_benh, ma_sp in links:
            session.add(BenhCay_SanPham(BenhCaymaBenh=ma_benh, SanPhammaSP=ma_sp))
        session.flush()

    # 6. Seed Sample Order DH01 linked to SP01 (for TC20 foreign key transaction check)
    if session.query(DonHang).count() == 0:
        dh01 = DonHang(
            maDH="DH01",
            ngayDat=date(2026, 11, 1),
            trangThai="Đã giao hàng",
            tongTien=240000.0,
            phuongThucTT="COD",
            phiVanChuyen=0.0,
            diaChiNhanHang="Bắc Từ Liêm, Hà Nội",
            hoTenNguoiNhan="Nguyễn Ngọc Luyến",
            soDienThoaiNguoiNhan="0912345678",
            NguoiDungmaND="ND02",
        )
        session.add(dh01)
        session.flush()
        session.add(
            ChiTietDonHang(
                DonHangmaDH="DH01",
                SanPhammaSP="SP01",
                soLuong=2,
                donGia=120000.0,
            )
        )

    session.commit()


def _ensure_product_svgs():
    img_dir = config.BASE_DIR / "static" / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    products = [
        ("sp01.svg", "Thuốc trừ sâu sinh học", "BioAgri - 120.000đ", "#15803d", "#dcfce7"),
        ("sp02.svg", "Thuốc phòng trừ nấm bệnh", "Trạm Xanh - 85.000đ", "#0f766e", "#ccfbf1"),
        ("sp03.svg", "Thuốc bảo vệ cây trồng", "Syngenta - 150.000đ", "#166534", "#bbf7d0"),
        ("sp04.svg", "Đặc trị mốc sương & đốm lá", "VFC - 95.000đ", "#0369a1", "#e0f2fe"),
        ("sp05.svg", "Trừ héo xanh & đốm vi khuẩn", "Lộc Trời - 110.000đ", "#15803d", "#dcfce7"),
        ("sp06.svg", "Sinh học trừ bọ phấn trắng", "EcoGreen - 135.000đ", "#166534", "#f0fdf4"),
        ("sp07.svg", "Đặc trị mốc sương khoai tây", "Trạm Xanh - 90.000đ", "#b45309", "#fef3c7"),
        ("sp08.svg", "Trừ thán thư & đốm lá ớt", "BioAgri - 105.000đ", "#be123c", "#ffe4e6"),
        ("sp09.svg", "Đặc trị cháy lá & gỉ sắt ngô", "VFC - 88.000đ", "#a16207", "#fef9c3"),
        ("sp10.svg", "Trừ sâu keo mùa thu hại ngô", "EcoGreen - 125.000đ", "#15803d", "#dcfce7"),
        ("sp_hethang.svg", "Thuốc nấm bệnh phổ rộng", "TẠM HẾT HÀNG", "#64748b", "#f1f5f9"),
    ]
    for fname, title, sub, c1, c2 in products:
        fpath = img_dir / fname
        if not fpath.exists():
            svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 320" width="400" height="320">
  <rect width="400" height="320" rx="16" fill="{c2}"/>
  <rect x="125" y="35" width="150" height="210" rx="18" fill="#ffffff" stroke="{c1}" stroke-width="4"/>
  <rect x="155" y="15" width="90" height="25" rx="6" fill="{c1}"/>
  <rect x="140" y="80" width="120" height="95" rx="8" fill="{c1}"/>
  <text x="200" y="118" text-anchor="middle" fill="#ffffff" font-family="Arial, sans-serif" font-size="18" font-weight="bold">TRẠM XANH</text>
  <text x="200" y="145" text-anchor="middle" fill="#dcfce7" font-family="Arial, sans-serif" font-size="12">BVTV CHÍNH HÃNG</text>
  <text x="200" y="275" text-anchor="middle" fill="{c1}" font-family="Arial, sans-serif" font-size="16" font-weight="bold">{title}</text>
  <text x="200" y="298" text-anchor="middle" fill="#334155" font-family="Arial, sans-serif" font-size="13">{sub}</text>
</svg>"""
            fpath.write_text(svg, encoding="utf-8")


def init_and_seed_db():
    """Create tables if not existing and populate initial seed data."""
    _ensure_product_svgs()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
