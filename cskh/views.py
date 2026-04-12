from django.shortcuts import render, redirect, get_object_or_404
from .models import HoiThoaiTuVan, TinNhanTuVan, TichDiem, LichSuTichDiem, KhuyenMai
from django.http import JsonResponse
import json
from datetime import date, datetime
import random
import string
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Avg, Count, OuterRef, Subquery, Q
from orders.models import DoiTra, DonHang
from products.models import DanhGia, SanPham
from accounts.models import KhachHang, NhanVien

def dashboard_view(request):
    chua_phan_hoi = HoiThoaiTuVan.objects.filter(TrangThai='Chưa tư vấn').count()
    dang_tu_van = HoiThoaiTuVan.objects.filter(TrangThai='Đang tư vấn').count()
    don_can_ho_tro = DoiTra.objects.filter(TrangThai='PENDING').count()
    danh_gia_moi = DanhGia.objects.all().count()
    recent_chats = HoiThoaiTuVan.objects.all()[:3]
    khach_hang_tong = KhachHang.objects.count()

    context = {
        'chua_phan_hoi': chua_phan_hoi,
        'dang_tu_van': dang_tu_van,
        'don_can_ho_tro': don_can_ho_tro,
        'danh_gia_moi': danh_gia_moi,
        'recent_chats': recent_chats,
        'khach_hang_tong': khach_hang_tong,
    }
    return render(request, 'cskh/dashboard.html', context)

def chat_reply_view(request):
    # 1. Khách hàng mẫu
    mau_data = [
        {"name": "Lê Thị Hồng", "msg": "Shop ơi, váy hoa nhí này còn size S không ạ?"},
        {"name": "Lê Viết Cường", "msg": "Cho mình hỏi quần Jean này có co giãn nhiều không shop?"},
        {"name": "Phạm Minh Hoàng", "msg": "Áo thun cotton này mặc có bị xù lông không shop ơi?"},
        {"name": "Hoàng Thu Thảo", "msg": "Mình cao 1m55 nặng 48kg thì mặc đầm này size gì vừa nhỉ?"},
        {"name": "Đặng Quốc Anh", "msg": "Sản phẩm này có được kiểm tra hàng trước khi nhận không ạ?"}
    ]

    for data in mau_data:
        kh = KhachHang.objects.filter(HoTen=data['name']).first()
        if kh:
            ht, created = HoiThoaiTuVan.objects.get_or_create(
                MaKH=kh,
                defaults={
                    'MaHoiThoai': "HT" + ''.join(random.choices(string.digits, k=6)),
                    'TrangThai': 'Chưa tư vấn'
                }
            )
            if not TinNhanTuVan.objects.filter(MaHoiThoai=ht).exists():
                TinNhanTuVan.objects.create(
                    MaTinNhan="TN" + ''.join(random.choices(string.digits, k=6)),
                    MaHoiThoai=ht, NoiDung=data['msg'], NguoiGui='KH'
                )

    # 2. Xử lý danh sách
    search_query = request.GET.get('search', '')
    last_msg_qs = TinNhanTuVan.objects.filter(MaHoiThoai=OuterRef('pk')).order_by('-ThoiGianGui')
    
    hoi_thoai_list = HoiThoaiTuVan.objects.select_related('MaKH').annotate(
        snippet=Subquery(last_msg_qs.values('NoiDung')[:1]),
        last_time=Subquery(last_msg_qs.values('ThoiGianGui')[:1])
    ).exclude(
        MaKH__HoTen__in=['Nguyễn Việt Cường', 'Nguyễn Văn Nhật', 'Ma Văn Toàn', 'Trần Thị Mai Lan']
    ).order_by('-last_time')

    if search_query:
        hoi_thoai_list = hoi_thoai_list.filter(MaKH__HoTen__icontains=search_query)
    
    ma_kh = request.GET.get('ma_kh')
    current_customer = None
    if ma_kh:
        current_customer = get_object_or_404(KhachHang, MaKH=ma_kh)
    elif hoi_thoai_list.exists():
        current_customer = hoi_thoai_list.first().MaKH

    tin_nhan_list = []
    current_chat = None
    header_status = ""

    if current_customer:
        current_chat = HoiThoaiTuVan.objects.filter(MaKH=current_customer).first()
        if current_chat:
            # --- LOGIC TRẠNG THÁI MỚI THEO YÊU CẦU ---
            # Mặc định luôn là 'Chưa tư vấn' ở danh sách nếu nhân viên CHƯA GỬI TIN NHẮN (rep)
            # Chỉ hiện 'Đang tư vấn' ở phần tiêu đề (Header) khung chat để nhân viên biết
            if current_chat.TrangThai != 'Đã tư vấn':
                header_status = 'Đang tư vấn'
            else:
                header_status = 'Đã tư vấn'
            
            tin_nhan_list = TinNhanTuVan.objects.filter(MaHoiThoai=current_chat).order_by('ThoiGianGui')

    # 3. Xử lý Gửi tin nhắn
    if request.method == 'POST' and current_chat:
        noi_dung = request.POST.get('NoiDung')
        if noi_dung:
            ma_tn = "TN" + ''.join(random.choices(string.digits, k=6))
            nv = NhanVien.objects.first()
            TinNhanTuVan.objects.create(
                MaTinNhan=ma_tn, MaHoiThoai=current_chat, MaNV=nv, NoiDung=noi_dung, NguoiGui='NV'
            )
            # CHỈ KHI GỬI TIN NHẮN THÌ MỚI CẬP NHẬT TRẠNG THÁI LÀ "ĐÃ TƯ VẤN" (MÀU XANH)
            current_chat.TrangThai = 'Đã tư vấn'
            current_chat.save()
            return redirect(f"{request.path}?ma_kh={current_customer.MaKH}")

    context = {
        'khach_hang_list': hoi_thoai_list,
        'current_customer': current_customer,
        'tin_nhan_list': tin_nhan_list,
        'current_chat': current_chat,
        'header_status': header_status,
        'search_query': search_query
    }
    return render(request, 'cskh/chat_reply.html', context)

def uudai_list_view(request):
    uudai_list = KhuyenMai.objects.all().order_by('-NgayBatDau')
    return render(request, 'cskh/uudai_list.html', {'uudai_list': uudai_list})

def diem_tich_luy_view(request):
    phone = request.GET.get('phone', '')
    if phone:
        danh_sach_tich_diem = TichDiem.objects.select_related('MaKH', 'MaKH__user').filter(
            MaKH__user__username__icontains=phone)
    else:
        danh_sach_tich_diem = TichDiem.objects.select_related('MaKH', 'MaKH__user').all()
    return render(request, 'cskh/diem_tich_luy.html', {'danh_sach_tich_diem': danh_sach_tich_diem})

def api_chi_tiet_tich_diem(request, ma_kh):
    try:
        td = TichDiem.objects.select_related('MaKH', 'MaKH__user').get(MaKH__MaKH=ma_kh)
        lich_su = LichSuTichDiem.objects.filter(MaKH__MaKH=ma_kh).order_by('NgayThucHien')
        ls_data = []
        running_total = 0
        for ls in lich_su:
            running_total += ls.DiemThayDoi
            ls_data.append({'ngay': ls.NgayThucHien.strftime('%d/%m/%Y'), 'noi_dung': ls.LyDo, 'diem_thay_doi': f"+{ls.DiemThayDoi}" if ls.DiemThayDoi > 0 else str(ls.DiemThayDoi), 'ket_qua': running_total})
        ls_data.reverse()
        return JsonResponse({'success': True, 'data': {'ho_ten': td.MaKH.HoTen, 'ma_kh': td.MaKH.MaKH, 'sdt': td.MaKH.user.username, 'tong_diem': td.TongDiem, 'lich_su': ls_data}})
    except Exception as e: return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_tru_tich_diem(request, ma_kh):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            diem_tru = int(body.get('diem_tru', 0))
            td = TichDiem.objects.get(MaKH__MaKH=ma_kh)
            td.TongDiem -= diem_tru
            td.save()
            ma_ls = "LS" + ''.join(random.choices(string.digits, k=6))
            LichSuTichDiem.objects.create(MaLS=ma_ls, MaKH=td.MaKH, DiemThayDoi=-diem_tru, LyDo='Trừ điểm', NgayThucHien=date.today())
            return JsonResponse({'success': True, 'new_tong_diem': td.TongDiem})
        except Exception as e: return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@csrf_exempt
def api_sua_tich_diem(request, ma_kh):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            diem_moi = int(body.get('diem_moi', -1))
            td = TichDiem.objects.get(MaKH__MaKH=ma_kh)
            chenh_lech = diem_moi - td.TongDiem
            td.TongDiem = diem_moi
            td.save()
            ma_ls = "LS" + ''.join(random.choices(string.digits, k=6))
            LichSuTichDiem.objects.create(MaLS=ma_ls, MaKH=td.MaKH, DiemThayDoi=chenh_lech, LyDo='Cập nhật điểm', NgayThucHien=date.today())
            return JsonResponse({'success': True, 'new_tong_diem': td.TongDiem})
        except Exception as e: return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

def quan_ly_danh_gia_view(request):
    danh_sach_sp = SanPham.objects.all()
    return render(request, 'cskh/quan_ly_danh_gia.html', {'danh_sach_sp': danh_sach_sp})

def chi_tiet_danh_gia_view(request, ma_sp):
    san_pham = get_object_or_404(SanPham, MaSP=ma_sp)
    danh_gia_list = DanhGia.objects.filter(MaSP=ma_sp).select_related('MaKH').order_by('-NgayDanhGia')
    tong_danh_gia = danh_gia_list.count()
    sao_trung_binh = round(danh_gia_list.aggregate(Avg('SoSao'))['SoSao__avg'] or 0, 1)
    stats = {str(i): danh_gia_list.filter(SoSao=i).count() for i in range(5, 0, -1)}
    pct = {k: (v / tong_danh_gia * 100 if tong_danh_gia > 0 else 0) for k, v in stats.items()}
    paginator = Paginator(danh_gia_list, 5)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'cskh/chi_tiet_danh_gia.html', {'san_pham': san_pham, 'page_obj': page_obj, 'tong_danh_gia': tong_danh_gia, 'sao_trung_binh': sao_trung_binh, 'stats': stats, 'pct': pct})

def mot_danh_gia_view(request, ma_dg):
    danh_gia = get_object_or_404(DanhGia.objects.select_related('MaKH', 'MaSP'), MaDanhGia=ma_dg)
    return render(request, 'cskh/mot_danh_gia.html', {'danh_gia': danh_gia})

def guest_home_view(request):
    return render(request, 'cskh/guest_home.html')
