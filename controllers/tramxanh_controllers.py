import io
import re
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from PIL import Image
from sqlalchemy.orm import Session

import config
from ai_service import ai_service
from data_access import (
    NguoiDung,
    DanhMuc,
    SanPham,
    GioHang,
    ChiTietGioHang,
    DonHang,
    ChiTietDonHang,
    BenhCay,
    BenhCay_SanPham,
    NguoiDungRepository,
    DanhMucRepository,
    SanPhamRepository,
    GioHangRepository,
    DonHangRepository,
    BenhCayRepository,
    hash_password,
    verify_password,
)


def _parse_date(val: Any) -> Optional[date]:
    if not val:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
    return None


# =============================================================================
# 1. TaiKhoanController
# =============================================================================
class TaiKhoanController:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NguoiDungRepository(db)

    def xuLyDangKy(
        self,
        hoTen: str,
        soDienThoai: str,
        matKhau: str,
        gioiTinh: Optional[str] = None,
        ngaySinh: Optional[str] = None,
        diaChiNhanHang: Optional[str] = None,
    ) -> Dict[str, Any]:
        hoTen = (hoTen or "").strip()
        soDienThoai = (soDienThoai or "").strip()
        matKhau = (matKhau or "").strip()

        if not hoTen or not soDienThoai or not matKhau:
            return {
                "success": False,
                "message": "Vui lòng nhập đầy đủ Họ và tên, Số điện thoại và Mật khẩu.",
            }

        if not re.match(r"^0\d{8,10}$", soDienThoai):
            return {
                "success": False,
                "message": "Số điện thoại không hợp lệ (phải bắt đầu bằng số 0 và gồm 9-11 chữ số).",
            }

        if len(matKhau) < 6:
            return {
                "success": False,
                "message": "Mật khẩu phải có ít nhất 6 ký tự.",
            }

        existing = self.repo.get_by_phone(soDienThoai)
        if existing:
            return {
                "success": False,
                "message": "Số điện thoại này đã được đăng ký tài khoản.",
            }

        new_id = self.repo.generate_next_id()
        user = NguoiDung(
            maND=new_id,
            hoTen=hoTen,
            matKhau=hash_password(matKhau),
            soDienThoai=soDienThoai,
            gioiTinh=(gioiTinh or "").strip() or None,
            ngaySinh=_parse_date(ngaySinh),
            diaChiNhanHang=(diaChiNhanHang or "").strip() or None,
            vaiTro="KhachHang",
        )
        self.repo.create(user)
        return {
            "success": True,
            "message": "Đăng ký tài khoản thành công.",
            "user": user,
        }

    def xuLyDangNhap(self, taiKhoan: str, matKhau: str) -> Dict[str, Any]:
        taiKhoan = (taiKhoan or "").strip()
        matKhau = (matKhau or "").strip()

        if not taiKhoan or not matKhau:
            return {
                "success": False,
                "message": "Vui lòng nhập số điện thoại/tài khoản và mật khẩu.",
            }

        # Support convenient aliases 'admin' -> '0900000001' and 'khachhang' -> '0912345678'
        lookup_phone = taiKhoan
        if taiKhoan.lower() == "admin":
            lookup_phone = "0900000001"
        elif taiKhoan.lower() in ("khachhang", "customer"):
            lookup_phone = "0912345678"

        user = self.repo.get_by_phone(lookup_phone)
        if not user:
            user = self.repo.get_by_id(taiKhoan)

        if not user or not verify_password(matKhau, user.matKhau):
            return {
                "success": False,
                "message": "Số điện thoại hoặc mật khẩu không chính xác.",
            }

        return {
            "success": True,
            "message": "Đăng nhập thành công.",
            "user": user,
        }

    def xuLyDangXuat(self) -> Dict[str, Any]:
        return {
            "success": True,
            "message": "Đã đăng xuất tài khoản.",
        }

    def getDanhSachKH(self, tuKhoa: Optional[str] = None) -> List[NguoiDung]:
        return self.repo.get_customers(tuKhoa=tuKhoa)

    def getThongTinChiTietKH(self, maND: str) -> Optional[NguoiDung]:
        return self.repo.get_by_id(maND)

    def capNhatThongTinKH(
        self,
        maND: str,
        hoTen: str,
        gioiTinh: Optional[str] = None,
        ngaySinh: Optional[str] = None,
        diaChiNhanHang: Optional[str] = None,
    ) -> Dict[str, Any]:
        user = self.repo.get_by_id(maND)
        if not user:
            return {"success": False, "message": "Không tìm thấy người dùng."}
        hoTen = (hoTen or "").strip()
        if not hoTen:
            return {"success": False, "message": "Họ và tên không được để trống."}
        user.hoTen = hoTen
        user.gioiTinh = (gioiTinh or "").strip() or None
        user.ngaySinh = _parse_date(ngaySinh)
        user.diaChiNhanHang = (diaChiNhanHang or "").strip() or None
        self.repo.update(user)
        return {"success": True, "message": "Cập nhật thông tin tài khoản thành công.", "user": user}


# =============================================================================
# 2. SanPhamController
# =============================================================================
class SanPhamController:
    def __init__(self, db: Session):
        self.db = db
        self.sp_repo = SanPhamRepository(db)
        self.dm_repo = DanhMucRepository(db)
        self.bc_repo = BenhCayRepository(db)

    def getDanhSachSanPham(
        self,
        tuKhoa: Optional[str] = None,
        maDM: Optional[str] = None,
        loaiCay: Optional[str] = None,
        maBenh: Optional[str] = None,
    ) -> List[SanPham]:
        return self.sp_repo.get_all(
            tuKhoa=tuKhoa,
            maDM=maDM,
            loaiCay=loaiCay,
            maBenh=maBenh,
        )

    def getChiTietSanPham(self, maSP: str) -> Optional[SanPham]:
        return self.sp_repo.get_by_id(maSP)

    def getDanhSachDanhMuc(self) -> List[DanhMuc]:
        return self.dm_repo.get_all()

    def themDanhMuc(self, tenDM: str, moTa: Optional[str] = None, maDM: Optional[str] = None) -> Dict[str, Any]:
        tenDM = (tenDM or "").strip()
        if not tenDM:
            return {"success": False, "message": "Tên danh mục không được bỏ trống."}
        if self.dm_repo.get_by_name(tenDM):
            return {"success": False, "message": "Tên danh mục đã tồn tại."}
        new_id = (maDM or "").strip() or self.dm_repo.generate_next_id()
        dm = DanhMuc(maDM=new_id, tenDM=tenDM, moTa=(moTa or "").strip() or None)
        self.dm_repo.create(dm)
        return {"success": True, "message": "Thêm danh mục thành công.", "danh_muc": dm}

    def capNhatDanhMuc(self, maDM: str, tenDM: str, moTa: Optional[str] = None) -> Dict[str, Any]:
        dm = self.dm_repo.get_by_id(maDM)
        if not dm:
            return {"success": False, "message": "Không tìm thấy danh mục."}
        tenDM = (tenDM or "").strip()
        if not tenDM:
            return {"success": False, "message": "Tên danh mục không được bỏ trống."}
        existing = self.dm_repo.get_by_name(tenDM)
        if existing and existing.maDM != maDM:
            return {"success": False, "message": "Tên danh mục đã tồn tại."}
        dm.tenDM = tenDM
        dm.moTa = (moTa or "").strip() or None
        self.dm_repo.update(dm)
        return {"success": True, "message": "Cập nhật danh mục thành công.", "danh_muc": dm}

    def themSanPham(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        TC15 & TC16:
        If required fields (tenSP, DanhMucmaDM, donGia) are empty OR tenSP already exists,
        return exact error message: "Không được bỏ trống dữ liệu hoặc sản phẩm đã tồn tại"
        """
        tenSP = str(data.get("tenSP") or "").strip()
        maDM = str(data.get("DanhMucmaDM") or "").strip()
        donGia_raw = data.get("donGia")
        soLuong_raw = data.get("soLuongTonKho", 0)

        if not tenSP or not maDM or donGia_raw is None or str(donGia_raw).strip() == "":
            return {
                "success": False,
                "message": "Không được bỏ trống dữ liệu hoặc sản phẩm đã tồn tại",
            }

        try:
            donGia = float(donGia_raw)
            soLuongTonKho = int(soLuong_raw) if str(soLuong_raw).strip() != "" else 0
            if donGia <= 0 or soLuongTonKho < 0:
                return {
                    "success": False,
                    "message": "Không được bỏ trống dữ liệu hoặc sản phẩm đã tồn tại",
                }
        except (ValueError, TypeError):
            return {
                "success": False,
                "message": "Không được bỏ trống dữ liệu hoặc sản phẩm đã tồn tại",
            }

        if self.sp_repo.get_by_name(tenSP):
            return {
                "success": False,
                "message": "Không được bỏ trống dữ liệu hoặc sản phẩm đã tồn tại",
            }

        maSP = str(data.get("maSP") or "").strip() or self.sp_repo.generate_next_id()
        if self.sp_repo.get_by_id(maSP):
            maSP = self.sp_repo.generate_next_id()

        hinhAnh = str(data.get("hinhAnh") or "").strip() or "/static/images/sp01.svg"
        sp = SanPham(
            maSP=maSP,
            tenSP=tenSP,
            hinhAnh=hinhAnh,
            donGia=donGia,
            soLuongTonKho=soLuongTonKho,
            congDung=str(data.get("congDung") or "").strip() or None,
            doiTuongSuDung=str(data.get("doiTuongSuDung") or "").strip() or None,
            huongDanSuDung=str(data.get("huongDanSuDung") or "").strip() or None,
            thuongHieu=str(data.get("thuongHieu") or "").strip() or None,
            thanhPhan=str(data.get("thanhPhan") or "").strip() or None,
            hanSuDung=_parse_date(data.get("hanSuDung")),
            DanhMucmaDM=maDM,
        )
        self.sp_repo.create(sp)
        return {
            "success": True,
            "message": "Thêm sản phẩm mới thành công.",
            "san_pham": sp,
        }

    def capNhatSanPham(self, maSP: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        TC17 & TC18:
        If required fields are blank, price is invalid, or tenSP duplicates another existing product,
        block update and show exact error message: "Dữ liệu không hợp lệ hoặc sản phẩm đã tồn tại"
        """
        sp = self.sp_repo.get_by_id(maSP)
        if not sp:
            return {
                "success": False,
                "message": "Dữ liệu không hợp lệ hoặc sản phẩm đã tồn tại",
            }

        tenSP = str(data.get("tenSP") or "").strip()
        maDM = str(data.get("DanhMucmaDM") or "").strip()
        donGia_raw = data.get("donGia")
        soLuong_raw = data.get("soLuongTonKho", sp.soLuongTonKho)

        if not tenSP or not maDM or donGia_raw is None or str(donGia_raw).strip() == "":
            return {
                "success": False,
                "message": "Dữ liệu không hợp lệ hoặc sản phẩm đã tồn tại",
            }

        try:
            donGia = float(donGia_raw)
            soLuongTonKho = int(soLuong_raw) if str(soLuong_raw).strip() != "" else 0
            if donGia <= 0 or soLuongTonKho < 0:
                return {
                    "success": False,
                    "message": "Dữ liệu không hợp lệ hoặc sản phẩm đã tồn tại",
                }
        except (ValueError, TypeError):
            return {
                "success": False,
                "message": "Dữ liệu không hợp lệ hoặc sản phẩm đã tồn tại",
            }

        existing = self.sp_repo.get_by_name(tenSP)
        if existing and existing.maSP != maSP:
            return {
                "success": False,
                "message": "Dữ liệu không hợp lệ hoặc sản phẩm đã tồn tại",
            }

        sp.tenSP = tenSP
        sp.DanhMucmaDM = maDM
        sp.donGia = donGia
        sp.soLuongTonKho = soLuongTonKho
        if data.get("hinhAnh"):
            sp.hinhAnh = str(data.get("hinhAnh")).strip()
        sp.congDung = str(data.get("congDung") or "").strip() or None
        sp.doiTuongSuDung = str(data.get("doiTuongSuDung") or "").strip() or None
        sp.huongDanSuDung = str(data.get("huongDanSuDung") or "").strip() or None
        sp.thuongHieu = str(data.get("thuongHieu") or "").strip() or None
        sp.thanhPhan = str(data.get("thanhPhan") or "").strip() or None
        if "hanSuDung" in data:
            sp.hanSuDung = _parse_date(data.get("hanSuDung"))

        self.sp_repo.update(sp)
        return {
            "success": True,
            "message": "Cập nhật sản phẩm thành công.",
            "san_pham": sp,
        }

    def deleteSanPham(self, maSP: str) -> Dict[str, Any]:
        """
        TC19 & TC20:
        Check if maSP exists in ChiTietDonHang. If it has already been part of any order/transaction,
        DO NOT delete it; display exact error message: "Không thể xóa sản phẩm đã có trong giao dịch".
        Otherwise delete from BenhCay_SanPham, ChiTietGioHang, and SanPham.
        """
        sp = self.sp_repo.get_by_id(maSP)
        if not sp:
            return {
                "success": False,
                "message": "Không tìm thấy sản phẩm cần xóa.",
            }

        if self.sp_repo.is_in_any_order(maSP):
            return {
                "success": False,
                "message": "Không thể xóa sản phẩm đã có trong giao dịch",
            }

        self.sp_repo.delete(sp)
        return {
            "success": True,
            "message": "Xóa sản phẩm thành công.",
        }


# =============================================================================
# 3. GioHangController
# =============================================================================
class GioHangController:
    def __init__(self, db: Session):
        self.db = db
        self.gh_repo = GioHangRepository(db)
        self.sp_repo = SanPhamRepository(db)

    def getGioHang(self, maGH: str, maND: Optional[str] = None) -> Dict[str, Any]:
        gh = self.gh_repo.get_or_create(maGH=maGH, maND=maND)
        total_money = self.gh_repo.recalculate_total(gh)
        items = []
        total_qty = 0
        has_out_of_stock = False

        for ct in gh.chi_tiets:
            sp = ct.san_pham
            if not sp:
                continue
            thanh_tien = ct.soLuong * sp.donGia
            total_qty += ct.soLuong
            is_oos = sp.soLuongTonKho <= 0 or ct.soLuong > sp.soLuongTonKho
            if is_oos:
                has_out_of_stock = True
            items.append({
                "maSP": sp.maSP,
                "tenSP": sp.tenSP,
                "hinhAnh": sp.hinhAnh or "/static/images/sp01.svg",
                "donGia": sp.donGia,
                "soLuong": ct.soLuong,
                "soLuongTonKho": sp.soLuongTonKho,
                "thanhTien": thanh_tien,
                "hetHang": is_oos,
            })

        return {
            "maGH": gh.maGH,
            "items": items,
            "tongSoLuong": total_qty,
            "tongTien": total_money,
            "hasOutOfStock": has_out_of_stock,
        }

    def getTongTien(self, maGH: str) -> float:
        gh = self.gh_repo.get_or_create(maGH=maGH)
        return self.gh_repo.recalculate_total(gh)

    def themVaoGioHang(
        self,
        maGH: str,
        maSP: str,
        soLuong: int = 1,
        maND: Optional[str] = None,
    ) -> Dict[str, Any]:
        sp = self.sp_repo.get_by_id(maSP)
        if not sp:
            return {"success": False, "message": "Không tìm thấy sản phẩm."}

        try:
            soLuong = max(1, int(soLuong))
        except (ValueError, TypeError):
            soLuong = 1

        gh = self.gh_repo.get_or_create(maGH=maGH, maND=maND)
        item = self.gh_repo.get_item(gh.maGH, maSP)
        if item:
            item.soLuong += soLuong
        else:
            item = ChiTietGioHang(GioHangmaGH=gh.maGH, SanPhammaSP=maSP, soLuong=soLuong)
            self.db.add(item)

        self.db.commit()
        self.gh_repo.recalculate_total(gh)

        if sp.soLuongTonKho <= 0 or item.soLuong > sp.soLuongTonKho:
            return {
                "success": True,
                "warning": True,
                "message": "Sản phẩm này hiện tại hết hàng",
            }

        return {
            "success": True,
            "warning": False,
            "message": f"Đã thêm '{sp.tenSP}' vào giỏ hàng.",
        }

    def capNhatSoLuong(self, maGH: str, maSP: str, soLuong: int) -> Dict[str, Any]:
        gh = self.gh_repo.get_or_create(maGH=maGH)
        item = self.gh_repo.get_item(gh.maGH, maSP)
        if not item:
            return {"success": False, "message": "Sản phẩm không có trong giỏ hàng."}

        try:
            soLuong = int(soLuong)
        except (ValueError, TypeError):
            soLuong = 1

        if soLuong <= 0:
            self.db.delete(item)
            self.db.commit()
            self.gh_repo.recalculate_total(gh)
            return {"success": True, "message": "Đã xóa sản phẩm khỏi giỏ hàng."}

        item.soLuong = soLuong
        self.db.commit()
        self.gh_repo.recalculate_total(gh)

        if item.san_pham and (item.san_pham.soLuongTonKho <= 0 or soLuong > item.san_pham.soLuongTonKho):
            return {
                "success": False,
                "message": "Sản phẩm này hiện tại hết hàng",
            }

        return {"success": True, "message": "Đã cập nhật số lượng."}

    def xoaSanPham(self, maGH: str, maSP: str) -> Dict[str, Any]:
        gh = self.gh_repo.get_or_create(maGH=maGH)
        item = self.gh_repo.get_item(gh.maGH, maSP)
        if item:
            self.db.delete(item)
            self.db.commit()
            self.gh_repo.recalculate_total(gh)
        return {"success": True, "message": "Đã xóa sản phẩm khỏi giỏ hàng."}

    def kiemTraGioHangTruocKhiMua(self, maGH: str, maND: Optional[str] = None) -> Dict[str, Any]:
        """
        TC05 Validation Rules:
        - If cart has 0 items -> "Giỏ hàng của bạn đang trống"
        - If any item in cart has soLuongTonKho == 0 or requested quantity > stock -> "Sản phẩm này hiện tại hết hàng"
        """
        cart_data = self.getGioHang(maGH=maGH, maND=maND)
        if not cart_data["items"] or cart_data["tongSoLuong"] == 0:
            return {
                "success": False,
                "message": "Giỏ hàng của bạn đang trống",
                "cart": cart_data,
            }

        for item in cart_data["items"]:
            if item["soLuongTonKho"] <= 0 or item["soLuong"] > item["soLuongTonKho"]:
                return {
                    "success": False,
                    "message": "Sản phẩm này hiện tại hết hàng",
                    "cart": cart_data,
                }

        return {
            "success": True,
            "message": "Hợp lệ",
            "cart": cart_data,
        }


# =============================================================================
# 4. DonHangController
# =============================================================================
class DonHangController:
    def __init__(self, db: Session):
        self.db = db
        self.dh_repo = DonHangRepository(db)
        self.gh_repo = GioHangRepository(db)
        self.sp_repo = SanPhamRepository(db)
        self.gh_ctrl = GioHangController(db)

    def taoDonHang(
        self,
        maGH: str,
        hoTenNguoiNhan: Optional[str],
        soDienThoaiNguoiNhan: Optional[str],
        diaChiNhanHang: Optional[str],
        phuongThucTT: Optional[str],
        maND: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        TC05, TC06, TC07:
        - Check cart not empty ("Giỏ hàng của bạn đang trống") and in stock ("Sản phẩm này hiện tại hết hàng").
        - Check shipping info (hoTenNguoiNhan, soDienThoaiNguoiNhan, diaChiNhanHang).
        - Check payment method selected; if empty -> exact message: "Chưa chọn phương thức thanh toán".
        - On valid submission -> create DonHang + ChiTietDonHang, deduct stock, clear cart, return "Đặt hàng thành công".
        """
        check = self.gh_ctrl.kiemTraGioHangTruocKhiMua(maGH=maGH, maND=maND)
        if not check["success"]:
            return check

        hoTen = (hoTenNguoiNhan or "").strip()
        sdt = (soDienThoaiNguoiNhan or "").strip()
        diaChi = (diaChiNhanHang or "").strip()
        pttt = (phuongThucTT or "").strip()

        if not hoTen or not sdt or not diaChi:
            return {
                "success": False,
                "message": "Vui lòng nhập đầy đủ thông tin nhận hàng (Họ và tên, Số điện thoại, Địa chỉ nhận hàng).",
            }

        if not re.match(r"^0\d{8,10}$", sdt):
            return {
                "success": False,
                "message": "Số điện thoại nhận hàng không hợp lệ (phải gồm 9-11 chữ số bắt đầu bằng 0).",
            }

        if not pttt:
            return {
                "success": False,
                "message": "Chưa chọn phương thức thanh toán",
            }

        cart_data = check["cart"]
        new_maDH = self.dh_repo.generate_next_id()
        don_hang = DonHang(
            maDH=new_maDH,
            ngayDat=date.today(),
            trangThai="Chờ xác nhận",
            tongTien=cart_data["tongTien"],
            phuongThucTT="COD" if pttt.upper() == "COD" else pttt,
            phiVanChuyen=0.0,
            diaChiNhanHang=diaChi,
            hoTenNguoiNhan=hoTen,
            soDienThoaiNguoiNhan=sdt,
            NguoiDungmaND=maND,
        )
        self.db.add(don_hang)
        self.db.flush()

        for item in cart_data["items"]:
            sp = self.sp_repo.get_by_id(item["maSP"])
            if not sp or sp.soLuongTonKho < item["soLuong"]:
                self.db.rollback()
                return {
                    "success": False,
                    "message": "Sản phẩm này hiện tại hết hàng",
                }
            sp.soLuongTonKho -= item["soLuong"]
            ct_dh = ChiTietDonHang(
                DonHangmaDH=new_maDH,
                SanPhammaSP=sp.maSP,
                soLuong=item["soLuong"],
                donGia=sp.donGia,
            )
            self.db.add(ct_dh)

        self.gh_repo.clear_cart(cart_data["maGH"])
        self.db.commit()
        self.db.refresh(don_hang)

        return {
            "success": True,
            "message": "Đặt hàng thành công",
            "don_hang": don_hang,
        }

    def getLichSuTrangThaiDH(self, maND: str) -> List[DonHang]:
        return self.dh_repo.get_by_user(maND=maND)

    def getDSDonHangAdmin(self, trangThai: Optional[str] = None, tuKhoa: Optional[str] = None) -> List[DonHang]:
        return self.dh_repo.get_all_admin(trangThai=trangThai, tuKhoa=tuKhoa)

    def capNhatTrangThai(self, maDH: str, trangThaiMoi: str) -> Dict[str, Any]:
        dh = self.dh_repo.get_by_id(maDH)
        if not dh:
            return {"success": False, "message": "Không tìm thấy đơn hàng."}
        dh.trangThai = trangThaiMoi
        self.db.commit()
        return {"success": True, "message": f"Đã cập nhật trạng thái đơn hàng {maDH} thành '{trangThaiMoi}'."}

    def huyDonHang(self, maDH: str, maND: Optional[str] = None) -> Dict[str, Any]:
        dh = self.dh_repo.get_by_id(maDH)
        if not dh:
            return {"success": False, "message": "Không tìm thấy đơn hàng."}
        if maND and dh.NguoiDungmaND != maND:
            return {"success": False, "message": "Bạn không có quyền hủy đơn hàng này."}
        if dh.trangThai not in ("Chờ xác nhận",):
            return {"success": False, "message": "Chỉ có thể hủy đơn hàng đang ở trạng thái 'Chờ xác nhận'."}

        # Restore stock
        for ct in dh.chi_tiets:
            if ct.san_pham:
                ct.san_pham.soLuongTonKho += ct.soLuong
        dh.trangThai = "Đã hủy"
        self.db.commit()
        return {"success": True, "message": f"Đã hủy đơn hàng {maDH}."}


# =============================================================================
# 5. NhanDienBenhController
# =============================================================================
class NhanDienBenhController:
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
    ALLOWED_MIMES = {"image/jpeg", "image/jpg", "image/png"}

    def __init__(self, db: Session):
        self.db = db
        self.bc_repo = BenhCayRepository(db)

    def taiHinhAnh(
        self,
        filename: Optional[str],
        content_type: Optional[str],
        file_bytes: Optional[bytes],
    ) -> Dict[str, Any]:
        """
        TC11 & Use Case 2.5 Validation Rules:
        - If no image selected: "Vui lòng tải hình ảnh cần nhận diện"
        - If file is not a valid .jpg, .jpeg, or .png: "Vui lòng chọn tệp ảnh hợp lệ (JPG, JPEG, PNG)"
        """
        if not filename or not file_bytes or len(file_bytes) == 0:
            return {
                "success": False,
                "message": "Vui lòng tải hình ảnh cần nhận diện",
            }

        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            return {
                "success": False,
                "message": "Vui lòng chọn tệp ảnh hợp lệ (JPG, JPEG, PNG)",
            }

        if content_type and content_type.lower() not in self.ALLOWED_MIMES and not content_type.lower().startswith("image/"):
            return {
                "success": False,
                "message": "Vui lòng chọn tệp ảnh hợp lệ (JPG, JPEG, PNG)",
            }

        try:
            img = Image.open(io.BytesIO(file_bytes))
            img_format = (img.format or "").upper()
            if img_format not in ("JPEG", "JPG", "PNG"):
                return {
                    "success": False,
                    "message": "Vui lòng chọn tệp ảnh hợp lệ (JPG, JPEG, PNG)",
                }
            img.verify()
        except Exception:
            return {
                "success": False,
                "message": "Vui lòng chọn tệp ảnh hợp lệ (JPG, JPEG, PNG)",
            }

        # Save uploaded file to static/uploads for display
        safe_name = f"{uuid.uuid4().hex[:12]}{ext}"
        save_path = config.UPLOAD_DIR / safe_name
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        return {
            "success": True,
            "image_url": f"/static/uploads/{safe_name}",
            "filename": filename,
        }

    def goiAPI(self, file_bytes: bytes, filename: str = "") -> Dict[str, Any]:
        return ai_service.predict(file_bytes, filename=filename)

    def hienThiKetQua(self, prediction: Dict[str, Any], image_url: str = "") -> Dict[str, Any]:
        """
        If confidence < threshold (50%), return exact message:
        "Chưa thể xác định bệnh từ ảnh. Vui lòng tải lên hình ảnh rõ nét hơn"
        Otherwise return BenhCay info and related SanPham list.
        """
        if prediction.get("is_low_confidence") or prediction.get("confidence", 0.0) < config.CONFIDENCE_THRESHOLD:
            return {
                "success": False,
                "low_confidence": True,
                "image_url": image_url,
                "confidence_percent": prediction.get("confidence_percent", 0.0),
                "confidence_display": f"{prediction.get('confidence_percent', 0.0):.1f}%".replace(".", ","),
                "message": "Chưa thể xác định bệnh từ ảnh. Vui lòng tải lên hình ảnh rõ nét hơn",
            }

        ma_benh = prediction.get("maBenh", "BC01")
        benh = self.bc_repo.get_by_id(ma_benh)
        if not benh:
            benh = self.bc_repo.get_by_id("BC01")

        related_products = self.bc_repo.get_related_products(benh.maBenh) if benh else []
        conf_pct = prediction.get("confidence_percent", 94.6)
        conf_display = f"{conf_pct:.1f}%".replace(".", ",")

        return {
            "success": True,
            "image_url": image_url,
            "maBenh": benh.maBenh if benh else ma_benh,
            "tenBenh": benh.tenBenh if benh else "Đốm lá sớm",
            "loaiCay": benh.loaiCay if benh else "Cà chua",
            "trieuChung": benh.trieuChung if benh else "",
            "bienPhapDieuTri": benh.bienPhapDieuTri if benh else "",
            "confidence": prediction.get("confidence", 0.946),
            "confidence_percent": conf_pct,
            "confidence_display": conf_display,
            "inference_time_ms": prediction.get("inference_time_ms", 12.0),
            "related_products": related_products,
        }

