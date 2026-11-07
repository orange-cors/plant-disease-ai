from datetime import date
from sqlalchemy import (
    Column,
    String,
    Unicode,
    UnicodeText,
    Float,
    Integer,
    Date,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class NguoiDung(Base):
    __tablename__ = "NguoiDung"

    maND = Column(String(20), primary_key=True)
    hoTen = Column(Unicode(100), nullable=False)
    matKhau = Column(Unicode(255), nullable=False)
    soDienThoai = Column(String(15), nullable=False, unique=True)
    gioiTinh = Column(Unicode(10), nullable=True)
    ngaySinh = Column(Date, nullable=True)
    diaChiNhanHang = Column(Unicode(255), nullable=True)
    vaiTro = Column(Unicode(30), nullable=False, default="KhachHang")  # 'KhachHang', 'QuanTriVien'

    gio_hangs = relationship("GioHang", back_populates="nguoi_dung")
    don_hangs = relationship("DonHang", back_populates="nguoi_dung")


class DanhMuc(Base):
    __tablename__ = "DanhMuc"

    maDM = Column(String(20), primary_key=True)
    tenDM = Column(Unicode(100), nullable=False)
    moTa = Column(UnicodeText, nullable=True)

    san_phams = relationship("SanPham", back_populates="danh_muc")


class SanPham(Base):
    __tablename__ = "SanPham"

    maSP = Column(String(20), primary_key=True)
    tenSP = Column(Unicode(200), nullable=False, unique=True)
    hinhAnh = Column(Unicode(255), nullable=True)
    donGia = Column(Float, nullable=False)
    soLuongTonKho = Column(Integer, nullable=False, default=0)
    congDung = Column(UnicodeText, nullable=True)
    doiTuongSuDung = Column(Unicode(255), nullable=True)
    huongDanSuDung = Column(UnicodeText, nullable=True)
    thuongHieu = Column(Unicode(100), nullable=True)
    thanhPhan = Column(UnicodeText, nullable=True)
    hanSuDung = Column(Date, nullable=True)
    DanhMucmaDM = Column(String(20), ForeignKey("DanhMuc.maDM"), nullable=True)

    danh_muc = relationship("DanhMuc", back_populates="san_phams")
    chi_tiet_gio_hangs = relationship("ChiTietGioHang", back_populates="san_pham", cascade="all, delete-orphan")
    chi_tiet_don_hangs = relationship("ChiTietDonHang", back_populates="san_pham")
    benh_cay_links = relationship("BenhCay_SanPham", back_populates="san_pham", cascade="all, delete-orphan")


class GioHang(Base):
    __tablename__ = "GioHang"

    maGH = Column(String(20), primary_key=True)
    tongTien = Column(Float, default=0.0)
    NguoiDungmaND = Column(String(20), ForeignKey("NguoiDung.maND"), nullable=True)

    nguoi_dung = relationship("NguoiDung", back_populates="gio_hangs")
    chi_tiets = relationship("ChiTietGioHang", back_populates="gio_hang", cascade="all, delete-orphan")


class ChiTietGioHang(Base):
    __tablename__ = "ChiTietGioHang"

    GioHangmaGH = Column(String(20), ForeignKey("GioHang.maGH", ondelete="CASCADE"), primary_key=True)
    SanPhammaSP = Column(String(20), ForeignKey("SanPham.maSP", ondelete="CASCADE"), primary_key=True)
    soLuong = Column(Integer, nullable=False, default=1)

    gio_hang = relationship("GioHang", back_populates="chi_tiets")
    san_pham = relationship("SanPham", back_populates="chi_tiet_gio_hangs")


class DonHang(Base):
    __tablename__ = "DonHang"

    maDH = Column(String(20), primary_key=True)
    ngayDat = Column(Date, default=date.today)
    trangThai = Column(Unicode(50), default="Chờ xác nhận")
    tongTien = Column(Float, nullable=False)
    phuongThucTT = Column(Unicode(50), nullable=False, default="COD")
    phiVanChuyen = Column(Float, default=0.0)
    diaChiNhanHang = Column(Unicode(255), nullable=False)
    hoTenNguoiNhan = Column(Unicode(100), nullable=True)
    soDienThoaiNguoiNhan = Column(String(15), nullable=True)
    NguoiDungmaND = Column(String(20), ForeignKey("NguoiDung.maND"), nullable=True)

    nguoi_dung = relationship("NguoiDung", back_populates="don_hangs")
    chi_tiets = relationship("ChiTietDonHang", back_populates="don_hang", cascade="all, delete-orphan")


class ChiTietDonHang(Base):
    __tablename__ = "ChiTietDonHang"

    DonHangmaDH = Column(String(20), ForeignKey("DonHang.maDH", ondelete="CASCADE"), primary_key=True)
    SanPhammaSP = Column(String(20), ForeignKey("SanPham.maSP"), primary_key=True)
    soLuong = Column(Integer, nullable=False)
    donGia = Column(Float, nullable=False)

    don_hang = relationship("DonHang", back_populates="chi_tiets")
    san_pham = relationship("SanPham", back_populates="chi_tiet_don_hangs")


# Alias to also support DonHang_SanPham as requested in Section 3.7
DonHang_SanPham = ChiTietDonHang


class BenhCay(Base):
    __tablename__ = "BenhCay"

    maBenh = Column(String(20), primary_key=True)
    tenBenh = Column(Unicode(150), nullable=False)
    loaiCay = Column(Unicode(100), nullable=True)  # 'Cà chua', 'Khoai tây', 'Ớt chuông', 'Ngô'
    trieuChung = Column(UnicodeText, nullable=True)
    bienPhapDieuTri = Column(UnicodeText, nullable=True)

    san_pham_links = relationship("BenhCay_SanPham", back_populates="benh_cay", cascade="all, delete-orphan")


class BenhCay_SanPham(Base):
    __tablename__ = "BenhCay_SanPham"

    BenhCaymaBenh = Column(String(20), ForeignKey("BenhCay.maBenh", ondelete="CASCADE"), primary_key=True)
    SanPhammaSP = Column(String(20), ForeignKey("SanPham.maSP", ondelete="CASCADE"), primary_key=True)

    benh_cay = relationship("BenhCay", back_populates="san_pham_links")
    san_pham = relationship("SanPham", back_populates="benh_cay_links")

