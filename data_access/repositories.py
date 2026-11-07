from datetime import date
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .models_db import (
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


class NguoiDungRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, maND: str) -> Optional[NguoiDung]:
        return self.db.query(NguoiDung).filter(NguoiDung.maND == maND).first()

    def get_by_phone(self, soDienThoai: str) -> Optional[NguoiDung]:
        return self.db.query(NguoiDung).filter(NguoiDung.soDienThoai == soDienThoai).first()

    def get_customers(self, tuKhoa: Optional[str] = None) -> List[NguoiDung]:
        q = self.db.query(NguoiDung).filter(NguoiDung.vaiTro == "KhachHang")
        if tuKhoa:
            kw = f"%{tuKhoa.strip()}%"
            q = q.filter(
                or_(
                    NguoiDung.hoTen.ilike(kw),
                    NguoiDung.soDienThoai.ilike(kw),
                    NguoiDung.maND.ilike(kw),
                    NguoiDung.diaChiNhanHang.ilike(kw),
                )
            )
        return q.order_by(NguoiDung.maND.asc()).all()

    def generate_next_id(self) -> str:
        all_ids = [r[0] for r in self.db.query(NguoiDung.maND).all()]
        max_num = 0
        for item in all_ids:
            if item and item.startswith("ND") and item[2:].isdigit():
                max_num = max(max_num, int(item[2:]))
        return f"ND{max_num + 1:02d}"

    def create(self, user: NguoiDung) -> NguoiDung:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: NguoiDung) -> NguoiDung:
        self.db.commit()
        self.db.refresh(user)
        return user


class DanhMucRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[DanhMuc]:
        return self.db.query(DanhMuc).order_by(DanhMuc.maDM.asc()).all()

    def get_by_id(self, maDM: str) -> Optional[DanhMuc]:
        return self.db.query(DanhMuc).filter(DanhMuc.maDM == maDM).first()

    def get_by_name(self, tenDM: str) -> Optional[DanhMuc]:
        return self.db.query(DanhMuc).filter(DanhMuc.tenDM == tenDM).first()

    def generate_next_id(self) -> str:
        all_ids = [r[0] for r in self.db.query(DanhMuc.maDM).all()]
        max_num = 0
        for item in all_ids:
            if item and item.startswith("DM") and item[2:].isdigit():
                max_num = max(max_num, int(item[2:]))
        return f"DM{max_num + 1:02d}"

    def create(self, dm: DanhMuc) -> DanhMuc:
        self.db.add(dm)
        self.db.commit()
        self.db.refresh(dm)
        return dm

    def update(self, dm: DanhMuc) -> DanhMuc:
        self.db.commit()
        self.db.refresh(dm)
        return dm


class SanPhamRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        tuKhoa: Optional[str] = None,
        maDM: Optional[str] = None,
        loaiCay: Optional[str] = None,
        maBenh: Optional[str] = None,
    ) -> List[SanPham]:
        q = self.db.query(SanPham)
        if maDM:
            q = q.filter(SanPham.DanhMucmaDM == maDM)
        if loaiCay:
            crop_kw = f"%{loaiCay.strip()}%"
            q = q.filter(SanPham.doiTuongSuDung.ilike(crop_kw))
        if maBenh:
            q = q.join(BenhCay_SanPham, BenhCay_SanPham.SanPhammaSP == SanPham.maSP).filter(
                BenhCay_SanPham.BenhCaymaBenh == maBenh
            )
        if tuKhoa:
            kw = f"%{tuKhoa.strip()}%"
            q = q.filter(
                or_(
                    SanPham.tenSP.ilike(kw),
                    SanPham.congDung.ilike(kw),
                    SanPham.doiTuongSuDung.ilike(kw),
                    SanPham.thanhPhan.ilike(kw),
                    SanPham.thuongHieu.ilike(kw),
                )
            )
        return q.order_by(SanPham.maSP.asc()).all()

    def get_by_id(self, maSP: str) -> Optional[SanPham]:
        return self.db.query(SanPham).filter(SanPham.maSP == maSP).first()

    def get_by_name(self, tenSP: str) -> Optional[SanPham]:
        return self.db.query(SanPham).filter(SanPham.tenSP == tenSP).first()

    def generate_next_id(self) -> str:
        all_ids = [r[0] for r in self.db.query(SanPham.maSP).all()]
        max_num = 0
        for item in all_ids:
            if item and item.startswith("SP") and item[2:].isdigit():
                max_num = max(max_num, int(item[2:]))
        return f"SP{max_num + 1:02d}"

    def is_in_any_order(self, maSP: str) -> bool:
        count = self.db.query(ChiTietDonHang).filter(ChiTietDonHang.SanPhammaSP == maSP).count()
        return count > 0

    def create(self, sp: SanPham) -> SanPham:
        self.db.add(sp)
        self.db.commit()
        self.db.refresh(sp)
        return sp

    def update(self, sp: SanPham) -> SanPham:
        self.db.commit()
        self.db.refresh(sp)
        return sp

    def delete(self, sp: SanPham) -> None:
        self.db.query(BenhCay_SanPham).filter(BenhCay_SanPham.SanPhammaSP == sp.maSP).delete()
        self.db.query(ChiTietGioHang).filter(ChiTietGioHang.SanPhammaSP == sp.maSP).delete()
        self.db.delete(sp)
        self.db.commit()


class GioHangRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, maGH: str, maND: Optional[str] = None) -> GioHang:
        gh = self.db.query(GioHang).filter(GioHang.maGH == maGH).first()
        if not gh and maND:
            gh = self.db.query(GioHang).filter(GioHang.NguoiDungmaND == maND).first()
        if not gh:
            gh = GioHang(maGH=maGH, tongTien=0.0, NguoiDungmaND=maND)
            self.db.add(gh)
            self.db.commit()
            self.db.refresh(gh)
        elif maND and not gh.NguoiDungmaND:
            gh.NguoiDungmaND = maND
            self.db.commit()
        return gh

    def recalculate_total(self, gh: GioHang) -> float:
        total = 0.0
        for item in gh.chi_tiets:
            if item.san_pham:
                total += item.soLuong * item.san_pham.donGia
        gh.tongTien = total
        self.db.commit()
        return total

    def get_item(self, maGH: str, maSP: str) -> Optional[ChiTietGioHang]:
        return (
            self.db.query(ChiTietGioHang)
            .filter(
                ChiTietGioHang.GioHangmaGH == maGH,
                ChiTietGioHang.SanPhammaSP == maSP,
            )
            .first()
        )

    def clear_cart(self, maGH: str) -> None:
        self.db.query(ChiTietGioHang).filter(ChiTietGioHang.GioHangmaGH == maGH).delete()
        gh = self.db.query(GioHang).filter(GioHang.maGH == maGH).first()
        if gh:
            gh.tongTien = 0.0
        self.db.commit()


class DonHangRepository:
    def __init__(self, db: Session):
        self.db = db

    def generate_next_id(self) -> str:
        all_ids = [r[0] for r in self.db.query(DonHang.maDH).all()]
        max_num = 0
        for item in all_ids:
            if item and item.startswith("DH") and item[2:].isdigit():
                max_num = max(max_num, int(item[2:]))
        return f"DH{max_num + 1:02d}"

    def get_by_id(self, maDH: str) -> Optional[DonHang]:
        return self.db.query(DonHang).filter(DonHang.maDH == maDH).first()

    def get_by_user(self, maND: str) -> List[DonHang]:
        return (
            self.db.query(DonHang)
            .filter(DonHang.NguoiDungmaND == maND)
            .order_by(DonHang.ngayDat.desc(), DonHang.maDH.desc())
            .all()
        )

    def get_all_admin(self, trangThai: Optional[str] = None, tuKhoa: Optional[str] = None) -> List[DonHang]:
        q = self.db.query(DonHang)
        if trangThai:
            q = q.filter(DonHang.trangThai == trangThai)
        if tuKhoa:
            kw = f"%{tuKhoa.strip()}%"
            q = q.filter(
                or_(
                    DonHang.maDH.ilike(kw),
                    DonHang.hoTenNguoiNhan.ilike(kw),
                    DonHang.soDienThoaiNguoiNhan.ilike(kw),
                    DonHang.diaChiNhanHang.ilike(kw),
                )
            )
        return q.order_by(DonHang.ngayDat.desc(), DonHang.maDH.desc()).all()


class BenhCayRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, loaiCay: Optional[str] = None) -> List[BenhCay]:
        q = self.db.query(BenhCay)
        if loaiCay:
            q = q.filter(BenhCay.loaiCay == loaiCay)
        return q.order_by(BenhCay.maBenh.asc()).all()

    def get_by_id(self, maBenh: str) -> Optional[BenhCay]:
        return self.db.query(BenhCay).filter(BenhCay.maBenh == maBenh).first()

    def get_related_products(self, maBenh: str) -> List[SanPham]:
        return (
            self.db.query(SanPham)
            .join(BenhCay_SanPham, BenhCay_SanPham.SanPhammaSP == SanPham.maSP)
            .filter(BenhCay_SanPham.BenhCaymaBenh == maBenh)
            .order_by(SanPham.maSP.asc())
            .all()
        )

