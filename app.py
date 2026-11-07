import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

import config
from ai_service import ai_service
from data_access import (
    get_db,
    init_and_seed_db,
    ACTIVE_DB_BACKEND,
    NguoiDung,
    DanhMuc,
    SanPham,
    DonHang,
    BenhCay,
)
from controllers import (
    TaiKhoanController,
    SanPhamController,
    GioHangController,
    DonHangController,
    NhanDienBenhController,
)

# Initialize and seed database on startup
init_and_seed_db()

app = FastAPI(
    title="TramXanh - Phân phối thuốc BVTV & AI Nhận diện bệnh cây",
    description="Hệ thống phân phối thuốc bảo vệ thực vật tích hợp AI nhận diện bệnh trên cây hoa màu ở Đồng bằng sông Hồng",
    version="3.0.0",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=config.SECRET_KEY,
    session_cookie="tramxanh_session",
)

# Mount Static Files & Templates
STATIC_DIR = config.BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

TEMPLATES_DIR = config.BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def format_vnd(value) -> str:
    try:
        num = int(round(float(value or 0)))
        return f"{num:,}".replace(",", ".") + " đ"
    except Exception:
        return "0 đ"


templates.env.filters["vnd"] = format_vnd


# =============================================================================
# SESSION & CONTEXT HELPERS
# =============================================================================
def get_current_user(request: Request, db: Session) -> Optional[NguoiDung]:
    maND = request.session.get("user_maND")
    if not maND:
        return None
    return TaiKhoanController(db).getThongTinChiTietKH(maND)


def get_session_cart_id(request: Request, current_user: Optional[NguoiDung] = None) -> str:
    if current_user:
        return f"GH_{current_user.maND}"
    maGH = request.session.get("maGH")
    if not maGH:
        maGH = f"GH_{uuid.uuid4().hex[:10].upper()}"
        request.session["maGH"] = maGH
    return maGH


def set_flash(request: Request, message: str, flash_type: str = "success") -> None:
    request.session["flash_message"] = message
    request.session["flash_type"] = flash_type


def build_context(request: Request, db: Session, **extra) -> dict:
    current_user = get_current_user(request, db)
    maGH = get_session_cart_id(request, current_user)
    cart_ctrl = GioHangController(db)
    cart_summary = cart_ctrl.getGioHang(
        maGH=maGH,
        maND=current_user.maND if current_user else None,
    )
    flash_message = request.session.pop("flash_message", None)
    flash_type = request.session.pop("flash_type", "success")

    ctx = {
        "request": request,
        "current_user": current_user,
        "cart_count": cart_summary["tongSoLuong"],
        "flash_message": flash_message,
        "flash_type": flash_type,
        "db_backend": ACTIVE_DB_BACKEND,
    }
    ctx.update(extra)
    return ctx


# =============================================================================
# FEATURE GROUP 2: HOME, PRODUCT CATALOG, CART & COD CHECKOUT
# =============================================================================
@app.get("/", response_class=HTMLResponse)
def home_page(request: Request, db: Session = Depends(get_db)):
    sp_ctrl = SanPhamController(db)
    all_products = sp_ctrl.getDanhSachSanPham()
    featured_products = [p for p in all_products if p.soLuongTonKho > 0][:8]
    return templates.TemplateResponse(
        request,
        "index.html",
        build_context(request, db, featured_products=featured_products),
    )


@app.get("/san-pham", response_class=HTMLResponse)
def product_list_page(
    request: Request,
    tuKhoa: Optional[str] = None,
    maDM: Optional[str] = None,
    loaiCay: Optional[str] = None,
    maBenh: Optional[str] = None,
    db: Session = Depends(get_db),
):
    sp_ctrl = SanPhamController(db)
    products = sp_ctrl.getDanhSachSanPham(
        tuKhoa=tuKhoa,
        maDM=maDM,
        loaiCay=loaiCay,
        maBenh=maBenh,
    )
    categories = sp_ctrl.getDanhSachDanhMuc()
    diseases = db.query(BenhCay).order_by(BenhCay.maBenh.asc()).all()

    return templates.TemplateResponse(
        request,
        "san_pham.html",
        build_context(
            request,
            db,
            products=products,
            categories=categories,
            diseases=diseases,
            selected_tuKhoa=tuKhoa or "",
            selected_maDM=maDM or "",
            selected_loaiCay=loaiCay or "",
            selected_maBenh=maBenh or "",
        ),
    )


@app.get("/san-pham/{maSP}", response_class=HTMLResponse)
def product_detail_page(
    request: Request,
    maSP: str,
    db: Session = Depends(get_db),
):
    sp_ctrl = SanPhamController(db)
    sp = sp_ctrl.getChiTietSanPham(maSP)
    if not sp:
        set_flash(request, "Không tìm thấy sản phẩm yêu cầu.", "error")
        return RedirectResponse(url="/san-pham", status_code=303)

    return templates.TemplateResponse(
        request,
        "chi_tiet_san_pham.html",
        build_context(request, db, sp=sp),
    )


@app.get("/gio-hang", response_class=HTMLResponse)
def cart_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    maGH = get_session_cart_id(request, current_user)
    gh_ctrl = GioHangController(db)
    cart = gh_ctrl.getGioHang(maGH=maGH, maND=current_user.maND if current_user else None)
    error_message = request.session.pop("cart_error", None)

    return templates.TemplateResponse(
        request,
        "gio_hang.html",
        build_context(request, db, cart=cart, error_message=error_message),
    )


@app.post("/gio-hang/them")
def add_to_cart(
    request: Request,
    maSP: str = Form(...),
    soLuong: int = Form(1),
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    maGH = get_session_cart_id(request, current_user)
    gh_ctrl = GioHangController(db)
    res = gh_ctrl.themVaoGioHang(
        maGH=maGH,
        maSP=maSP,
        soLuong=soLuong,
        maND=current_user.maND if current_user else None,
    )
    if res.get("warning"):
        request.session["cart_error"] = res["message"]
    else:
        set_flash(request, res["message"], "success" if res["success"] else "error")
    return RedirectResponse(url="/gio-hang", status_code=303)


@app.post("/gio-hang/cap-nhat")
def update_cart_item(
    request: Request,
    maSP: str = Form(...),
    soLuong: int = Form(...),
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    maGH = get_session_cart_id(request, current_user)
    gh_ctrl = GioHangController(db)
    res = gh_ctrl.capNhatSoLuong(maGH=maGH, maSP=maSP, soLuong=soLuong)
    if not res["success"]:
        request.session["cart_error"] = res["message"]
    return RedirectResponse(url="/gio-hang", status_code=303)


@app.post("/gio-hang/xoa")
def remove_cart_item(
    request: Request,
    maSP: str = Form(...),
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    maGH = get_session_cart_id(request, current_user)
    gh_ctrl = GioHangController(db)
    gh_ctrl.xoaSanPham(maGH=maGH, maSP=maSP)
    set_flash(request, "Đã xóa sản phẩm khỏi giỏ hàng.", "success")
    return RedirectResponse(url="/gio-hang", status_code=303)


@app.post("/gio-hang/mua-hang", response_class=HTMLResponse)
def proceed_to_checkout(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    maGH = get_session_cart_id(request, current_user)
    gh_ctrl = GioHangController(db)
    check = gh_ctrl.kiemTraGioHangTruocKhiMua(
        maGH=maGH,
        maND=current_user.maND if current_user else None,
    )
    if not check["success"]:
        return templates.TemplateResponse(
            request,
            "gio_hang.html",
            build_context(request, db, cart=check["cart"], error_message=check["message"]),
        )
    return RedirectResponse(url="/dat-hang", status_code=303)


@app.get("/dat-hang", response_class=HTMLResponse)
def checkout_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    maGH = get_session_cart_id(request, current_user)
    gh_ctrl = GioHangController(db)
    check = gh_ctrl.kiemTraGioHangTruocKhiMua(
        maGH=maGH,
        maND=current_user.maND if current_user else None,
    )
    if not check["success"]:
        return templates.TemplateResponse(
            request,
            "gio_hang.html",
            build_context(request, db, cart=check["cart"], error_message=check["message"]),
        )

    form_data = {
        "hoTenNguoiNhan": current_user.hoTen if current_user else "",
        "soDienThoaiNguoiNhan": current_user.soDienThoai if current_user else "",
        "diaChiNhanHang": (current_user.diaChiNhanHang or "") if current_user else "",
        "phuongThucTT": "COD",
    }
    return templates.TemplateResponse(
        request,
        "dat_hang.html",
        build_context(request, db, cart=check["cart"], form_data=form_data, error_message=None, success_message=None),
    )


@app.post("/dat-hang", response_class=HTMLResponse)
def submit_order(
    request: Request,
    hoTenNguoiNhan: Optional[str] = Form(None),
    soDienThoaiNguoiNhan: Optional[str] = Form(None),
    diaChiNhanHang: Optional[str] = Form(None),
    phuongThucTT: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    maGH = get_session_cart_id(request, current_user)
    dh_ctrl = DonHangController(db)
    gh_ctrl = GioHangController(db)

    res = dh_ctrl.taoDonHang(
        maGH=maGH,
        hoTenNguoiNhan=hoTenNguoiNhan,
        soDienThoaiNguoiNhan=soDienThoaiNguoiNhan,
        diaChiNhanHang=diaChiNhanHang,
        phuongThucTT=phuongThucTT,
        maND=current_user.maND if current_user else None,
    )

    if not res["success"]:
        cart = gh_ctrl.getGioHang(maGH=maGH, maND=current_user.maND if current_user else None)
        if res["message"] in ("Giỏ hàng của bạn đang trống", "Sản phẩm này hiện tại hết hàng"):
            return templates.TemplateResponse(
                request,
                "gio_hang.html",
                build_context(request, db, cart=cart, error_message=res["message"]),
            )
        form_data = {
            "hoTenNguoiNhan": hoTenNguoiNhan or "",
            "soDienThoaiNguoiNhan": soDienThoaiNguoiNhan or "",
            "diaChiNhanHang": diaChiNhanHang or "",
            "phuongThucTT": phuongThucTT or "",
        }
        return templates.TemplateResponse(
            request,
            "dat_hang.html",
            build_context(
                request,
                db,
                cart=cart,
                form_data=form_data,
                error_message=res["message"],
                success_message=None,
            ),
        )

    return templates.TemplateResponse(
        request,
        "dat_hang.html",
        build_context(
            request,
            db,
            cart={"items": [], "tongSoLuong": 0, "tongTien": 0},
            form_data={},
            error_message=None,
            success_message=res["message"],
            created_order=res["don_hang"],
        ),
    )


# =============================================================================
# FEATURE GROUP 1: AUTHENTICATION & ACCESS CONTROL
# =============================================================================
@app.get("/dang-nhap", response_class=HTMLResponse)
def login_page(request: Request, next: Optional[str] = None, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request,
        "dang_nhap.html",
        build_context(request, db, next_url=next or "", error_message=None, taiKhoan=""),
    )


@app.post("/dang-nhap", response_class=HTMLResponse)
def login_submit(
    request: Request,
    taiKhoan: Optional[str] = Form(None),
    matKhau: Optional[str] = Form(None),
    next: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    guest_maGH = request.session.get("maGH")
    tk_ctrl = TaiKhoanController(db)
    res = tk_ctrl.xuLyDangNhap(taiKhoan=taiKhoan or "", matKhau=matKhau or "")
    if not res["success"]:
        return templates.TemplateResponse(
            request,
            "dang_nhap.html",
            build_context(request, db, next_url=next or "", error_message=res["message"], taiKhoan=taiKhoan or ""),
        )

    user: NguoiDung = res["user"]
    request.session["user_maND"] = user.maND

    # Merge any guest cart items into user's cart
    if guest_maGH:
        gh_ctrl = GioHangController(db)
        guest_cart = gh_ctrl.getGioHang(maGH=guest_maGH)
        user_maGH = f"GH_{user.maND}"
        for item in guest_cart["items"]:
            gh_ctrl.themVaoGioHang(maGH=user_maGH, maSP=item["maSP"], soLuong=item["soLuong"], maND=user.maND)
        gh_ctrl.gh_repo.clear_cart(guest_maGH)

    set_flash(request, f"Xin chào {user.hoTen}! Đăng nhập thành công.", "success")
    if next and next.startswith("/"):
        return RedirectResponse(url=next, status_code=303)
    if user.vaiTro == "QuanTriVien":
        return RedirectResponse(url="/admin", status_code=303)
    return RedirectResponse(url="/", status_code=303)


@app.get("/dang-ky", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request,
        "dang_ky.html",
        build_context(request, db, form_data={}, error_message=None),
    )


@app.post("/dang-ky", response_class=HTMLResponse)
def register_submit(
    request: Request,
    hoTen: Optional[str] = Form(None),
    soDienThoai: Optional[str] = Form(None),
    matKhau: Optional[str] = Form(None),
    gioiTinh: Optional[str] = Form(None),
    ngaySinh: Optional[str] = Form(None),
    diaChiNhanHang: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    tk_ctrl = TaiKhoanController(db)
    res = tk_ctrl.xuLyDangKy(
        hoTen=hoTen or "",
        soDienThoai=soDienThoai or "",
        matKhau=matKhau or "",
        gioiTinh=gioiTinh,
        ngaySinh=ngaySinh,
        diaChiNhanHang=diaChiNhanHang,
    )
    if not res["success"]:
        form_data = {
            "hoTen": hoTen or "",
            "soDienThoai": soDienThoai or "",
            "gioiTinh": gioiTinh or "Nam",
            "ngaySinh": ngaySinh or "",
            "diaChiNhanHang": diaChiNhanHang or "",
        }
        return templates.TemplateResponse(
            request,
            "dang_ky.html",
            build_context(request, db, form_data=form_data, error_message=res["message"]),
        )

    user: NguoiDung = res["user"]
    request.session["user_maND"] = user.maND
    set_flash(request, "Đăng ký tài khoản thành công!", "success")
    return RedirectResponse(url="/", status_code=303)


@app.get("/dang-xuat")
def logout_route(request: Request, db: Session = Depends(get_db)):
    TaiKhoanController(db).xuLyDangXuat()
    request.session.clear()
    return RedirectResponse(url="/dang-nhap", status_code=303)


@app.get("/tai-khoan", response_class=HTMLResponse)
@app.get("/lich-su-don-hang", response_class=HTMLResponse)
def profile_and_orders_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/dang-nhap?next=/tai-khoan", status_code=303)

    dh_ctrl = DonHangController(db)
    orders = dh_ctrl.getLichSuTrangThaiDH(maND=current_user.maND)
    return templates.TemplateResponse(
        request,
        "tai_khoan.html",
        build_context(request, db, orders=orders),
    )


@app.post("/tai-khoan")
def update_profile_submit(
    request: Request,
    hoTen: Optional[str] = Form(None),
    gioiTinh: Optional[str] = Form(None),
    ngaySinh: Optional[str] = Form(None),
    diaChiNhanHang: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    res = TaiKhoanController(db).capNhatThongTinKH(
        maND=current_user.maND,
        hoTen=hoTen or "",
        gioiTinh=gioiTinh,
        ngaySinh=ngaySinh,
        diaChiNhanHang=diaChiNhanHang,
    )
    set_flash(request, res["message"], "success" if res["success"] else "error")
    return RedirectResponse(url="/tai-khoan", status_code=303)


@app.post("/don-hang/huy/{maDH}")
def cancel_order_submit(request: Request, maDH: str, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/dang-nhap", status_code=303)
    res = DonHangController(db).huyDonHang(maDH=maDH, maND=current_user.maND)
    set_flash(request, res["message"], "success" if res["success"] else "error")
    return RedirectResponse(url="/lich-su-don-hang", status_code=303)


# =============================================================================
# FEATURE GROUP 3: AI PLANT LEAF DISEASE RECOGNITION (TC08-TC13)
# =============================================================================
@app.get("/nhan-dien-benh", response_class=HTMLResponse)
def ai_recognition_page(request: Request, db: Session = Depends(get_db)):
    # TC12 Rule: If an unauthenticated user tries to access /nhan-dien-benh, redirect immediately to /dang-nhap
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/dang-nhap?next=/nhan-dien-benh", status_code=303)

    return templates.TemplateResponse(
        request,
        "nhan_dien_benh.html",
        build_context(request, db, result=None, error_message=None),
    )


@app.post("/nhan-dien-benh", response_class=HTMLResponse)
async def ai_recognition_submit(
    request: Request,
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # TC12 Rule
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/dang-nhap?next=/nhan-dien-benh", status_code=303)

    nd_ctrl = NhanDienBenhController(db)
    filename = file.filename if file else None
    content_type = file.content_type if file else None
    file_bytes = await file.read() if file else b""

    upload_check = nd_ctrl.taiHinhAnh(
        filename=filename,
        content_type=content_type,
        file_bytes=file_bytes,
    )
    if not upload_check["success"]:
        return templates.TemplateResponse(
            request,
            "nhan_dien_benh.html",
            build_context(request, db, result=None, error_message=upload_check["message"]),
        )

    prediction = nd_ctrl.goiAPI(file_bytes=file_bytes, filename=filename or "")
    result = nd_ctrl.hienThiKetQua(prediction=prediction, image_url=upload_check["image_url"])

    if not result["success"]:
        return templates.TemplateResponse(
            request,
            "nhan_dien_benh.html",
            build_context(request, db, result=None, error_message=result["message"]),
        )

    return templates.TemplateResponse(
        request,
        "nhan_dien_benh.html",
        build_context(request, db, result=result, error_message=None),
    )


@app.post("/api/ai/predict")
@app.post("/api/predict")
async def api_ai_predict(
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    nd_ctrl = NhanDienBenhController(db)
    filename = file.filename if file else None
    content_type = file.content_type if file else None
    file_bytes = await file.read() if file else b""

    upload_check = nd_ctrl.taiHinhAnh(
        filename=filename,
        content_type=content_type,
        file_bytes=file_bytes,
    )
    if not upload_check["success"]:
        return JSONResponse(status_code=400, content=upload_check)

    prediction = nd_ctrl.goiAPI(file_bytes=file_bytes, filename=filename or "")
    result = nd_ctrl.hienThiKetQua(prediction=prediction, image_url=upload_check["image_url"])
    if not result["success"]:
        return JSONResponse(status_code=422, content=result)

    return {
        "success": True,
        "maBenh": result["maBenh"],
        "tenBenh": result["tenBenh"],
        "loaiCay": result["loaiCay"],
        "confidence": result["confidence"],
        "confidence_percent": result["confidence_percent"],
        "confidence_display": result["confidence_display"],
        "trieuChung": result["trieuChung"],
        "bienPhapDieuTri": result["bienPhapDieuTri"],
        "image_url": result["image_url"],
        "related_products": [
            {
                "maSP": sp.maSP,
                "tenSP": sp.tenSP,
                "donGia": sp.donGia,
                "doiTuongSuDung": sp.doiTuongSuDung,
                "hinhAnh": sp.hinhAnh,
            }
            for sp in result["related_products"]
        ],
    }


# =============================================================================
# FEATURE GROUP 4: ADMIN DASHBOARD & PRODUCT MANAGEMENT CRUD (TC14-TC22)
# =============================================================================
def _check_admin_access(request: Request, db: Session):
    """TC22 Rule: Block Guest or non-admin Customer from accessing /admin/* routes."""
    current_user = get_current_user(request, db)
    if not current_user or current_user.vaiTro != "QuanTriVien":
        return templates.TemplateResponse(
            request,
            "403.html",
            build_context(request, db),
            status_code=403,
        )
    return None


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard_page(request: Request, db: Session = Depends(get_db)):
    blocked = _check_admin_access(request, db)
    if blocked:
        return blocked

    stats = {
        "categories_count": db.query(DanhMuc).count(),
        "products_count": db.query(SanPham).count(),
        "orders_count": db.query(DonHang).count(),
        "customers_count": db.query(NguoiDung).filter(NguoiDung.vaiTro == "KhachHang").count(),
    }
    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        build_context(request, db, stats=stats),
    )


@app.get("/admin/san-pham", response_class=HTMLResponse)
def admin_products_page(
    request: Request,
    maDM: Optional[str] = None,
    db: Session = Depends(get_db),
):
    blocked = _check_admin_access(request, db)
    if blocked:
        return blocked

    sp_ctrl = SanPhamController(db)
    products = sp_ctrl.getDanhSachSanPham(maDM=maDM)
    categories = sp_ctrl.getDanhSachDanhMuc()
    total_all_products = db.query(SanPham).count()
    error_message = request.session.pop("admin_sp_error", None)
    success_message = request.session.pop("admin_sp_success", None)

    return templates.TemplateResponse(
        request,
        "admin/san_pham.html",
        build_context(
            request,
            db,
            products=products,
            categories=categories,
            selected_maDM=maDM or "",
            total_all_products=total_all_products,
            error_message=error_message,
            success_message=success_message,
        ),
    )


@app.post("/admin/san-pham/them", response_class=HTMLResponse)
def admin_add_product(
    request: Request,
    tenSP: Optional[str] = Form(None),
    DanhMucmaDM: Optional[str] = Form(None),
    donGia: Optional[str] = Form(None),
    soLuongTonKho: Optional[str] = Form("50"),
    hinhAnh: Optional[str] = Form("/static/images/sp01.svg"),
    congDung: Optional[str] = Form(None),
    doiTuongSuDung: Optional[str] = Form(None),
    huongDanSuDung: Optional[str] = Form(None),
    thuongHieu: Optional[str] = Form(None),
    thanhPhan: Optional[str] = Form(None),
    hanSuDung: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    blocked = _check_admin_access(request, db)
    if blocked:
        return blocked

    sp_ctrl = SanPhamController(db)
    res = sp_ctrl.themSanPham({
        "tenSP": tenSP,
        "DanhMucmaDM": DanhMucmaDM,
        "donGia": donGia,
        "soLuongTonKho": soLuongTonKho,
        "hinhAnh": hinhAnh,
        "congDung": congDung,
        "doiTuongSuDung": doiTuongSuDung,
        "huongDanSuDung": huongDanSuDung,
        "thuongHieu": thuongHieu,
        "thanhPhan": thanhPhan,
        "hanSuDung": hanSuDung,
    })

    if not res["success"]:
        request.session["admin_sp_error"] = res["message"]
    else:
        request.session["admin_sp_success"] = res["message"]

    return RedirectResponse(url="/admin/san-pham", status_code=303)


@app.post("/admin/san-pham/cap-nhat/{maSP}", response_class=HTMLResponse)
def admin_update_product(
    request: Request,
    maSP: str,
    tenSP: Optional[str] = Form(None),
    DanhMucmaDM: Optional[str] = Form(None),
    donGia: Optional[str] = Form(None),
    soLuongTonKho: Optional[str] = Form("0"),
    hinhAnh: Optional[str] = Form(None),
    congDung: Optional[str] = Form(None),
    doiTuongSuDung: Optional[str] = Form(None),
    huongDanSuDung: Optional[str] = Form(None),
    thuongHieu: Optional[str] = Form(None),
    thanhPhan: Optional[str] = Form(None),
    hanSuDung: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    blocked = _check_admin_access(request, db)
    if blocked:
        return blocked

    sp_ctrl = SanPhamController(db)
    res = sp_ctrl.capNhatSanPham(
        maSP=maSP,
        data={
            "tenSP": tenSP,
            "DanhMucmaDM": DanhMucmaDM,
            "donGia": donGia,
            "soLuongTonKho": soLuongTonKho,
            "hinhAnh": hinhAnh,
            "congDung": congDung,
            "doiTuongSuDung": doiTuongSuDung,
            "huongDanSuDung": huongDanSuDung,
            "thuongHieu": thuongHieu,
            "thanhPhan": thanhPhan,
            "hanSuDung": hanSuDung,
        },
    )

    if not res["success"]:
        request.session["admin_sp_error"] = res["message"]
    else:
        request.session["admin_sp_success"] = res["message"]

    return RedirectResponse(url="/admin/san-pham", status_code=303)


@app.post("/admin/san-pham/xoa/{maSP}", response_class=HTMLResponse)
def admin_delete_product(
    request: Request,
    maSP: str,
    db: Session = Depends(get_db),
):
    blocked = _check_admin_access(request, db)
    if blocked:
        return blocked

    sp_ctrl = SanPhamController(db)
    res = sp_ctrl.deleteSanPham(maSP=maSP)
    if not res["success"]:
        request.session["admin_sp_error"] = res["message"]
    else:
        request.session["admin_sp_success"] = res["message"]

    return RedirectResponse(url="/admin/san-pham", status_code=303)


@app.get("/admin/danh-muc", response_class=HTMLResponse)
def admin_categories_page(request: Request, db: Session = Depends(get_db)):
    blocked = _check_admin_access(request, db)
    if blocked:
        return blocked

    categories = SanPhamController(db).getDanhSachDanhMuc()
    return templates.TemplateResponse(
        request,
        "admin/danh_muc.html",
        build_context(request, db, categories=categories),
    )


@app.post("/admin/danh-muc/them")
def admin_add_category(
    request: Request,
    tenDM: Optional[str] = Form(None),
    moTa: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    blocked = _check_admin_access(request, db)
    if blocked:
        return blocked

    res = SanPhamController(db).themDanhMuc(tenDM=tenDM or "", moTa=moTa)
    set_flash(request, res["message"], "success" if res["success"] else "error")
    return RedirectResponse(url="/admin/danh-muc", status_code=303)


@app.get("/admin/don-hang", response_class=HTMLResponse)
def admin_orders_page(request: Request, trangThai: Optional[str] = None, db: Session = Depends(get_db)):
    blocked = _check_admin_access(request, db)
    if blocked:
        return blocked

    orders = DonHangController(db).getDSDonHangAdmin(trangThai=trangThai)
    return templates.TemplateResponse(
        request,
        "admin/don_hang.html",
        build_context(request, db, orders=orders),
    )


@app.post("/admin/don-hang/cap-nhat/{maDH}")
def admin_update_order_status(
    request: Request,
    maDH: str,
    trangThai: str = Form(...),
    db: Session = Depends(get_db),
):
    blocked = _check_admin_access(request, db)
    if blocked:
        return blocked

    res = DonHangController(db).capNhatTrangThai(maDH=maDH, trangThaiMoi=trangThai)
    set_flash(request, res["message"], "success" if res["success"] else "error")
    return RedirectResponse(url="/admin/don-hang", status_code=303)


@app.get("/admin/khach-hang", response_class=HTMLResponse)
def admin_customers_page(request: Request, tuKhoa: Optional[str] = None, db: Session = Depends(get_db)):
    blocked = _check_admin_access(request, db)
    if blocked:
        return blocked

    customers = TaiKhoanController(db).getDanhSachKH(tuKhoa=tuKhoa)
    return templates.TemplateResponse(
        request,
        "admin/khach_hang.html",
        build_context(request, db, customers=customers, tuKhoa=tuKhoa or ""),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
