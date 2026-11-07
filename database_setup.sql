-- =============================================================================
-- TRAMXANH - PESTICIDE DISTRIBUTION & AI PLANT DISEASE RECOGNITION WEBSITE
-- Microsoft SQL Server Database Setup & Seed Script (database_setup.sql)
-- =============================================================================

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'TramXanhDB')
BEGIN
    CREATE DATABASE [TramXanhDB];
END
GO

USE [TramXanhDB];
GO

-- Drop existing tables in reverse dependency order if re-running setup
IF OBJECT_ID('dbo.DonHang_SanPham', 'V') IS NOT NULL DROP VIEW dbo.DonHang_SanPham;
IF OBJECT_ID('dbo.BenhCay_SanPham', 'U') IS NOT NULL DROP TABLE dbo.BenhCay_SanPham;
IF OBJECT_ID('dbo.BenhCay', 'U') IS NOT NULL DROP TABLE dbo.BenhCay;
IF OBJECT_ID('dbo.ChiTietDonHang', 'U') IS NOT NULL DROP TABLE dbo.ChiTietDonHang;
IF OBJECT_ID('dbo.DonHang', 'U') IS NOT NULL DROP TABLE dbo.DonHang;
IF OBJECT_ID('dbo.ChiTietGioHang', 'U') IS NOT NULL DROP TABLE dbo.ChiTietGioHang;
IF OBJECT_ID('dbo.GioHang', 'U') IS NOT NULL DROP TABLE dbo.GioHang;
IF OBJECT_ID('dbo.SanPham', 'U') IS NOT NULL DROP TABLE dbo.SanPham;
IF OBJECT_ID('dbo.DanhMuc', 'U') IS NOT NULL DROP TABLE dbo.DanhMuc;
IF OBJECT_ID('dbo.NguoiDung', 'U') IS NOT NULL DROP TABLE dbo.NguoiDung;
GO

-- =============================================================================
-- 1. TABLE: NguoiDung
-- =============================================================================
CREATE TABLE dbo.NguoiDung (
    maND VARCHAR(20) PRIMARY KEY,
    hoTen NVARCHAR(100) NOT NULL,
    matKhau NVARCHAR(255) NOT NULL,
    soDienThoai VARCHAR(15) NOT NULL UNIQUE,
    gioiTinh NVARCHAR(10) NULL,
    ngaySinh DATE NULL,
    diaChiNhanHang NVARCHAR(255) NULL,
    vaiTro NVARCHAR(30) NOT NULL -- 'KhachHang', 'QuanTriVien'
);
GO

-- =============================================================================
-- 2. TABLE: DanhMuc
-- =============================================================================
CREATE TABLE dbo.DanhMuc (
    maDM VARCHAR(20) PRIMARY KEY,
    tenDM NVARCHAR(100) NOT NULL,
    moTa NVARCHAR(MAX) NULL
);
GO

-- =============================================================================
-- 3. TABLE: SanPham
-- =============================================================================
CREATE TABLE dbo.SanPham (
    maSP VARCHAR(20) PRIMARY KEY,
    tenSP NVARCHAR(200) NOT NULL UNIQUE,
    hinhAnh NVARCHAR(255) NULL,
    donGia FLOAT NOT NULL,
    soLuongTonKho INT NOT NULL DEFAULT 0,
    congDung NVARCHAR(MAX) NULL,
    doiTuongSuDung NVARCHAR(255) NULL,
    huongDanSuDung NVARCHAR(MAX) NULL,
    thuongHieu NVARCHAR(100) NULL,
    thanhPhan NVARCHAR(MAX) NULL,
    hanSuDung DATE NULL,
    DanhMucmaDM VARCHAR(20) NULL,
    CONSTRAINT FK_SanPham_DanhMuc FOREIGN KEY (DanhMucmaDM) REFERENCES dbo.DanhMuc(maDM)
);
GO

-- =============================================================================
-- 4. TABLE: GioHang
-- =============================================================================
CREATE TABLE dbo.GioHang (
    maGH VARCHAR(20) PRIMARY KEY,
    tongTien FLOAT DEFAULT 0,
    NguoiDungmaND VARCHAR(20) NULL,
    CONSTRAINT FK_GioHang_NguoiDung FOREIGN KEY (NguoiDungmaND) REFERENCES dbo.NguoiDung(maND)
);
GO

-- =============================================================================
-- 5. TABLE: ChiTietGioHang
-- =============================================================================
CREATE TABLE dbo.ChiTietGioHang (
    GioHangmaGH VARCHAR(20) NOT NULL,
    SanPhammaSP VARCHAR(20) NOT NULL,
    soLuong INT NOT NULL,
    CONSTRAINT PK_ChiTietGioHang PRIMARY KEY (GioHangmaGH, SanPhammaSP),
    CONSTRAINT FK_CTGH_GioHang FOREIGN KEY (GioHangmaGH) REFERENCES dbo.GioHang(maGH) ON DELETE CASCADE,
    CONSTRAINT FK_CTGH_SanPham FOREIGN KEY (SanPhammaSP) REFERENCES dbo.SanPham(maSP) ON DELETE CASCADE
);
GO

-- =============================================================================
-- 6. TABLE: DonHang
-- =============================================================================
CREATE TABLE dbo.DonHang (
    maDH VARCHAR(20) PRIMARY KEY,
    ngayDat DATE DEFAULT CAST(GETDATE() AS DATE),
    trangThai NVARCHAR(50) DEFAULT N'Chờ xác nhận',
    tongTien FLOAT NOT NULL,
    phuongThucTT NVARCHAR(50) NOT NULL, -- N'COD'
    phiVanChuyen FLOAT DEFAULT 0,
    diaChiNhanHang NVARCHAR(255) NOT NULL,
    hoTenNguoiNhan NVARCHAR(100) NULL,
    soDienThoaiNguoiNhan VARCHAR(15) NULL,
    NguoiDungmaND VARCHAR(20) NULL,
    CONSTRAINT FK_DonHang_NguoiDung FOREIGN KEY (NguoiDungmaND) REFERENCES dbo.NguoiDung(maND)
);
GO

-- =============================================================================
-- 7. TABLE: ChiTietDonHang (and alias view DonHang_SanPham)
-- =============================================================================
CREATE TABLE dbo.ChiTietDonHang (
    DonHangmaDH VARCHAR(20) NOT NULL,
    SanPhammaSP VARCHAR(20) NOT NULL,
    soLuong INT NOT NULL,
    donGia FLOAT NOT NULL,
    CONSTRAINT PK_ChiTietDonHang PRIMARY KEY (DonHangmaDH, SanPhammaSP),
    CONSTRAINT FK_CTDH_DonHang FOREIGN KEY (DonHangmaDH) REFERENCES dbo.DonHang(maDH) ON DELETE CASCADE,
    CONSTRAINT FK_CTDH_SanPham FOREIGN KEY (SanPhammaSP) REFERENCES dbo.SanPham(maSP)
);
GO

CREATE VIEW dbo.DonHang_SanPham AS
SELECT DonHangmaDH, SanPhammaSP, soLuong, donGia
FROM dbo.ChiTietDonHang;
GO

-- =============================================================================
-- 8. TABLE: BenhCay
-- =============================================================================
CREATE TABLE dbo.BenhCay (
    maBenh VARCHAR(20) PRIMARY KEY,
    tenBenh NVARCHAR(150) NOT NULL,
    loaiCay NVARCHAR(100) NULL, -- N'Cà chua', N'Khoai tây', N'Ớt chuông', N'Ngô'
    trieuChung NVARCHAR(MAX) NULL,
    bienPhapDieuTri NVARCHAR(MAX) NULL
);
GO

-- =============================================================================
-- 9. TABLE: BenhCay_SanPham
-- =============================================================================
CREATE TABLE dbo.BenhCay_SanPham (
    BenhCaymaBenh VARCHAR(20) NOT NULL,
    SanPhammaSP VARCHAR(20) NOT NULL,
    CONSTRAINT PK_BenhCay_SanPham PRIMARY KEY (BenhCaymaBenh, SanPhammaSP),
    CONSTRAINT FK_BCSP_BenhCay FOREIGN KEY (BenhCaymaBenh) REFERENCES dbo.BenhCay(maBenh) ON DELETE CASCADE,
    CONSTRAINT FK_BCSP_SanPham FOREIGN KEY (SanPhammaSP) REFERENCES dbo.SanPham(maSP) ON DELETE CASCADE
);
GO

-- =============================================================================
-- SEED DATA
-- =============================================================================

-- 1. Seed NguoiDung (Passwords hashed with bcrypt/werkzeug; application verifies both hashed & fallback)
INSERT INTO dbo.NguoiDung (maND, hoTen, matKhau, soDienThoai, gioiTinh, ngaySinh, diaChiNhanHang, vaiTro)
VALUES
('ND01', N'Quản Trị Viên Trạm Xanh', N'$2b$12$KIX/hashed_by_app_init_admin123', '0900000001', N'Nam', '1990-01-01', N'Số 1 Đại Cồ Việt, Hai Bà Trưng, Hà Nội', N'QuanTriVien'),
('ND02', N'Nguyễn Ngọc Luyến', N'$2b$12$KIX/hashed_by_app_init_123456', '0912345678', N'Nữ', '2003-05-15', N'Bắc Từ Liêm, Hà Nội', N'KhachHang'),
('ND03', N'Trần Văn Nông', N'$2b$12$KIX/hashed_by_app_init_123456', '0987654321', N'Nam', '1985-08-20', N'Gia Lâm, Hà Nội', N'KhachHang');
GO

-- 2. Seed DanhMuc (DM04 kept empty with 0 products for TC09 / Branch 4.1)
INSERT INTO dbo.DanhMuc (maDM, tenDM, moTa)
VALUES
('DM01', N'Thuốc trừ nấm bệnh', N'Các dòng thuốc đặc trị nấm bệnh, mốc sương, đốm lá, gỉ sắt trên cây hoa màu.'),
('DM02', N'Thuốc trừ sâu sinh học', N'Chế phẩm sinh học an toàn giúp tiêu diệt sâu tơ, sâu xanh, bọ phấn trắng, nhện đỏ.'),
('DM03', N'Thuốc đặc trị vi khuẩn & bảo vệ cây trồng', N'Thuốc phòng trị bệnh héo xanh vi khuẩn, đốm vi khuẩn và tăng sức đề kháng cây trồng.'),
('DM04', N'Chế phẩm vi sinh mới', N'Danh mục các dòng chế phẩm vi sinh thế hệ mới (Chưa có sản phẩm).');
GO

-- 3. Seed SanPham (Exact 6 products targeting 'Cà chua' for TC01, plus products for Khoai tây, Ớt chuông, Ngô, and SP_HET_HANG for TC05)
INSERT INTO dbo.SanPham (maSP, tenSP, hinhAnh, donGia, soLuongTonKho, congDung, doiTuongSuDung, huongDanSuDung, thuongHieu, thanhPhan, hanSuDung, DanhMucmaDM)
VALUES
('SP01', N'Thuốc trừ sâu sinh học', N'/static/images/sp01.svg', 120000, 50,
 N'Đặc trị sâu xanh, sâu tơ, bọ trĩ, nhện đỏ và côn trùng chích hút truyền bệnh virus trên cây hoa màu.',
 N'Cà chua, Ngô, Ớt chuông',
 N'Pha 20ml cho bình 16-20 lít nước. Phun ướt đều hai mặt lá vào sáng sớm hoặc chiều mát.',
 N'BioAgri Việt Nam', N'Abamectin 1.8% w/w + Phụ gia sinh học 98.2%', '2028-12-31', 'DM02'),

('SP02', N'Thuốc phòng trừ nấm bệnh', N'/static/images/sp02.svg', 85000, 50,
 N'Phòng và đặc trị hiệu quả bệnh đốm lá sớm, mốc sương, thán thư, nấm bệnh gây hại lá và thân.',
 N'Cà chua, Khoai tây',
 N'Pha 40g cho bình 16 lít nước. Phun định kỳ 7-10 ngày/lần khi bệnh mới xuất hiện.',
 N'Trạm Xanh CropCare', N'Mancozeb 640g/kg + Metalaxyl 80g/kg', '2028-06-30', 'DM01'),

('SP03', N'Thuốc bảo vệ cây trồng', N'/static/images/sp03.svg', 150000, 50,
 N'Bảo vệ toàn diện cây trồng trước nấm và vi khuẩn gây bệnh đốm lá, cháy lá, tăng cường đề kháng.',
 N'Cà chua, Khoai tây, Ớt chuông, Ngô',
 N'Pha 25ml cho bình 20 lít nước. Phun phòng ngừa hoặc ngay khi phát hiện vết bệnh đầu tiên.',
 N'Syngenta Việt Nam', N'Azoxystrobin 200g/L + Difenoconazole 125g/L', '2028-10-15', 'DM03'),

('SP04', N'Thuốc đặc trị mốc sương và đốm lá cà chua', N'/static/images/sp04.svg', 95000, 40,
 N'Đặc trị nấm bệnh gây đốm lá sớm (Alternaria solani) và mốc sương (Phytophthora infestans) trên cà chua và khoai tây.',
 N'Cà chua, Khoai tây',
 N'Pha 30g cho bình 16 lít nước. Phun kỹ mặt dưới lá nơi bào tử nấm trú ngụ.',
 N'VFC Nông Dược', N'Chlorothalonil 75% WP', '2028-09-01', 'DM01'),

('SP05', N'Thuốc trừ bệnh héo xanh và đốm vi khuẩn cà chua', N'/static/images/sp05.svg', 110000, 35,
 N'Tiêu diệt nhanh vi khuẩn gây bệnh đốm vi khuẩn, loét vi khuẩn và héo xanh trên cà chua, ớt chuông.',
 N'Cà chua, Ớt chuông',
 N'Pha 18g cho bình 16 lít nước. Phun 2 lần cách nhau 5-7 ngày khi trời ráo.',
 N'Lộc Trời Group', N'Kasugamycin 2% + Copper Oxychloride 45%', '2028-11-20', 'DM03'),

('SP06', N'Chế phẩm sinh học phòng trừ bọ phấn trắng hại cà chua', N'/static/images/sp06.svg', 135000, 45,
 N'Kiểm soát bọ phấn trắng môi giới truyền bệnh virus vàng xoăn lá cà chua, an toàn cho thiên địch.',
 N'Cà chua',
 N'Pha 25ml cho bình 20 lít nước. Phun đều lên tán lá định kỳ 7 ngày/lần.',
 N'EcoGreen Đồng Bằng', N'Matrine 1.2% + Tinh dầu Neem tự nhiên', '2028-08-15', 'DM02'),

('SP07', N'Thuốc đặc trị nấm mốc sương khoai tây', N'/static/images/sp07.svg', 90000, 60,
 N'Chuyên dùng phòng trừ nấm bệnh mốc sương và đốm vòng cháy lá sớm trên cây khoai tây vụ Đông.',
 N'Khoai tây',
 N'Pha 35g cho bình 16 lít nước. Phun sớm khi thời tiết ẩm ướt, sương muối.',
 N'Trạm Xanh CropCare', N'Cymoxanil 8% + Mancozeb 64%', '2028-05-30', 'DM01'),

('SP08', N'Thuốc trừ bệnh thán thư và đốm lá ớt chuông', N'/static/images/sp08.svg', 105000, 40,
 N'Đặc trị đốm vi khuẩn và nấm thán thư trên lá và quả ớt chuông.',
 N'Ớt chuông',
 N'Pha 20ml cho bình 16 lít nước. Ngừng phun trước khi thu hoạch 7 ngày.',
 N'BioAgri Việt Nam', N'Copper Hydroxide 77% WP', '2028-07-20', 'DM03'),

('SP09', N'Thuốc đặc trị cháy lá và gỉ sắt hại ngô', N'/static/images/sp09.svg', 88000, 70,
 N'Đặc trị nấm bệnh cháy lá lớn, đốm lá xám và gỉ sắt trên cây ngô vùng bãi sông Hồng.',
 N'Ngô',
 N'Pha 20ml cho bình 16 lít nước. Phun khi ngô giai đoạn xoáy nõn đến trỗ cờ.',
 N'VFC Nông Dược', N'Propiconazole 250g/L EC', '2028-12-01', 'DM01'),

('SP10', N'Thuốc trừ sâu keo mùa thu hại ngô sinh học', N'/static/images/sp10.svg', 125000, 55,
 N'Diệt trừ sâu keo mùa thu, sâu đục thân hại ngô bằng vi khuẩn sinh học Bt.',
 N'Ngô',
 N'Pha 25g cho bình 16 lít nước, phun trực tiếp vào nõn ngô.',
 N'EcoGreen Đồng Bằng', N'Bacillus thuringiensis var. kurstaki 32.000 IU/mg', '2028-10-01', 'DM02'),

('SP_HET_HANG', N'Thuốc đặc trị nấm bệnh phổ rộng (Tạm hết hàng)', N'/static/images/sp_hethang.svg', 99000, 0,
 N'Thuốc trừ nấm bệnh phổ rộng trên khoai tây, ngô và ớt chuông (Sản phẩm đang tạm hết hàng trong kho).',
 N'Khoai tây, Ngô, Ớt chuông',
 N'Pha 30ml cho bình 16 lít nước.',
 N'Trạm Xanh CropCare', N'Hexaconazole 50g/L', '2028-04-01', 'DM01');
GO

-- 4. Seed BenhCay (14 classes across the 4 target crops: Cà chua, Khoai tây, Ớt chuông, Ngô)
INSERT INTO dbo.BenhCay (maBenh, tenBenh, loaiCay, trieuChung, bienPhapDieuTri)
VALUES
('BC01', N'Đốm lá sớm', N'Cà chua',
 N'Xuất hiện các đốm nâu sẫm có vòng đồng tâm như bia bắn trên lá già phía dưới trước, sau đó lan dần lên trên làm vàng lá và rụng sớm.',
 N'Tỉa bỏ lá bệnh già ở gốc, luân canh cây trồng, giữ ruộng thông thoáng và phun thuốc trừ nấm hoạt chất Mancozeb, Azoxystrobin hoặc Chlorothalonil.'),

('BC02', N'Mốc sương', N'Cà chua',
 N'Vết bệnh ban đầu là các đốm xanh tái ngập nước ở mép lá, sau chuyển nâu đen. Mặt dưới lá có lớp mốc trắng mịn khi trời ẩm ướt, bệnh lan rất nhanh.',
 N'Thoát nước tốt, không tưới phun mưa vào chiều tối, thu gom tiêu hủy cây bệnh nặng và phun ngay thuốc đặc trị Metalaxyl + Mancozeb.'),

('BC03', N'Đốm vi khuẩn', N'Cà chua',
 N'Các đốm nhỏ sũng nước màu nâu đen xuất hiện rải rác trên lá, xung quanh có quầng vàng hẹp; các đốm có thể liên kết làm cháy rách phiến lá.',
 N'Sử dụng hạt giống sạch bệnh, hạn chế làm xây xát lá khi chăm sóc và phun thuốc gốc Đồng hoặc kháng sinh Kasugamycin.'),

('BC04', N'Vàng xoăn lá', N'Cà chua',
 N'Lá ngọn nhỏ lại, xoăn cong lên phía trên, phiến lá dày giòn và chuyển màu vàng giữa các gân lá; cây còi cọc, đốt ngắn, hoa dễ rụng.',
 N'Nhổ bỏ cây nhiễm bệnh sớm, quây lưới chắn côn trùng và phun chế phẩm sinh học tiêu diệt bọ phấn trắng truyền virus.'),

('BC05', N'Lá khỏe mạnh', N'Cà chua',
 N'Phiến lá cà chua có màu xanh tươi đồng đều, bề mặt lá phẳng, không có vết đốm nấm, vi khuẩn hay biến dạng do virus.',
 N'Duy trì chế độ bón phân cân đối NPK, tưới nước hợp lý và thăm đồng định kỳ để phòng ngừa sâu bệnh.'),

('BC06', N'Đốm vòng / Cháy lá sớm', N'Khoai tây',
 N'Trên lá xuất hiện những đốm tròn hoặc góc cạnh màu nâu sẫm có các vòng đồng tâm rõ rệt, mô lá xung quanh vết bệnh chuyển màu vàng.',
 N'Bón đủ phân kali tăng sức chống chịu, vệ sinh tàn dư cây trồng và phun thuốc trừ nấm Mancozeb hoặc Chlorothalonil.'),

('BC07', N'Mốc sương khoai tây', N'Khoai tây',
 N'Mép lá và chóp lá có vết bệnh màu nâu xám như bị dội nước sôi, mặt dưới lá có lớp tơ nấm trắng xốp khi trời lạnh và sương mù.',
 N'Lên luống cao thoát nước tốt, vun gốc kỹ và phun phòng trừ kịp thời bằng thuốc đặc trị Cymoxanil + Mancozeb.'),

('BC08', N'Lá khỏe mạnh', N'Khoai tây',
 N'Lá khoai tây xanh đậm, dày khỏe, phát triển bình thường, không có dấu hiệu đốm lá hay mốc sương.',
 N'Tiếp tục chăm sóc, vun xới và theo dõi thời tiết sương muối để chủ động bảo vệ cây.'),

('BC09', N'Đốm vi khuẩn ớt chuông', N'Ớt chuông',
 N'Trên lá xuất hiện các đốm nhỏ màu xanh sẫm ướt, sau chuyển sang màu nâu đen, viền sẫm, lá bị bệnh nặng chuyển vàng và rụng hàng loạt.',
 N'Tránh tưới nước lên tán lá, cắt tỉa cành lá thông thoáng và phun thuốc gốc Đồng hoặc Kasugamycin.'),

('BC10', N'Lá khỏe mạnh', N'Ớt chuông',
 N'Lá ớt chuông bóng mượt, xanh tốt, không có vết đốm hay biến dạng.',
 N'Chăm sóc định kỳ, bổ sung canxi-bo và phòng ngừa bọ trĩ, nhện đỏ.'),

('BC11', N'Cháy lá ngô', N'Ngô',
 N'Vết bệnh hình thoi dài (hình điếu xì gà) màu xám xanh hoặc nâu nhạt, chạy dọc theo phiến lá làm khô cháy từng mảng lớn trên lá ngô.',
 N'Gieo trồng mật độ hợp lý, vệ sinh đồng ruộng và phun thuốc đặc trị nấm Propiconazole hoặc Azoxystrobin.'),

('BC12', N'Gỉ sắt ngô', N'Ngô',
 N'Hai mặt lá xuất hiện nhiều ổ nấm nhỏ nổi gồ lên màu nâu đỏ hoặc vàng gạch như vết gỉ sắt, khi vỡ giải phóng bột bào tử màu nâu.',
 N'Bón phân cân đối tránh thừa đạm, dọn sạch lá già dưới gốc và phun thuốc trừ nấm nhóm Triazole.'),

('BC13', N'Đốm lá xám', N'Ngô',
 N'Các vết bệnh hình chữ nhật hẹp, chạy song song với gân lá, màu nâu xám hoặc vàng nâu làm giảm diện tích quang hợp của lá.',
 N'Luân canh với cây họ đậu, cày vùi tàn dư sau thu hoạch và sử dụng thuốc trừ nấm đặc hiệu.'),

('BC14', N'Lá khỏe mạnh', N'Ngô',
 N'Lá ngô xanh mướt, phiến lá rộng và lành lặn, không có vết cháy lá hay ổ gỉ sắt.',
 N'Duy trì chăm sóc, bón thúc đúng thời kỳ và kiểm tra nõn ngô phòng sâu keo mùa thu.');
GO

-- 5. Seed BenhCay_SanPham (Link each disease to 3 relevant products; BC01 linked to SP01, SP02, SP03, SP04 for TC08 & TC09)
INSERT INTO dbo.BenhCay_SanPham (BenhCaymaBenh, SanPhammaSP)
VALUES
-- BC01: Đốm lá sớm (Cà chua)
('BC01', 'SP02'),
('BC01', 'SP03'),
('BC01', 'SP04'),
('BC01', 'SP01'),
-- BC02: Mốc sương (Cà chua)
('BC02', 'SP02'),
('BC02', 'SP03'),
('BC02', 'SP04'),
-- BC03: Đốm vi khuẩn (Cà chua)
('BC03', 'SP05'),
('BC03', 'SP03'),
('BC03', 'SP02'),
-- BC04: Vàng xoăn lá (Cà chua)
('BC04', 'SP06'),
('BC04', 'SP01'),
('BC04', 'SP03'),
-- BC05: Lá khỏe mạnh (Cà chua)
('BC05', 'SP03'),
('BC05', 'SP01'),
('BC05', 'SP06'),
-- BC06: Đốm vòng / Cháy lá sớm (Khoai tây)
('BC06', 'SP02'),
('BC06', 'SP04'),
('BC06', 'SP07'),
-- BC07: Mốc sương khoai tây (Khoai tây)
('BC07', 'SP07'),
('BC07', 'SP02'),
('BC07', 'SP04'),
-- BC08: Lá khỏe mạnh (Khoai tây)
('BC08', 'SP03'),
('BC08', 'SP07'),
('BC08', 'SP02'),
-- BC09: Đốm vi khuẩn ớt chuông (Ớt chuông)
('BC09', 'SP08'),
('BC09', 'SP05'),
('BC09', 'SP03'),
-- BC10: Lá khỏe mạnh (Ớt chuông)
('BC10', 'SP03'),
('BC10', 'SP01'),
('BC10', 'SP08'),
-- BC11: Cháy lá ngô (Ngô)
('BC11', 'SP09'),
('BC11', 'SP03'),
('BC11', 'SP10'),
-- BC12: Gỉ sắt ngô (Ngô)
('BC12', 'SP09'),
('BC12', 'SP03'),
('BC12', 'SP01'),
-- BC13: Đốm lá xám (Ngô)
('BC13', 'SP09'),
('BC13', 'SP03'),
('BC13', 'SP10'),
-- BC14: Lá khỏe mạnh (Ngô)
('BC14', 'SP03'),
('BC14', 'SP10'),
('BC14', 'SP09');
GO

-- 6. Seed DonHang & ChiTietDonHang (Sample Order linked to SP01 so Admin deleting SP01 triggers TC20)
INSERT INTO dbo.DonHang (maDH, ngayDat, trangThai, tongTien, phuongThucTT, phiVanChuyen, diaChiNhanHang, hoTenNguoiNhan, soDienThoaiNguoiNhan, NguoiDungmaND)
VALUES
('DH01', '2026-11-01', N'Đã giao hàng', 240000, N'COD', 0, N'Bắc Từ Liêm, Hà Nội', N'Nguyễn Ngọc Luyến', '0912345678', 'ND02');

INSERT INTO dbo.ChiTietDonHang (DonHangmaDH, SanPhammaSP, soLuong, donGia)
VALUES
('DH01', 'SP01', 2, 120000);
GO

