from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg, Count, OuterRef, Subquery
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import json
import random
import string
from datetime import date, datetime

from .models import HoiThoaiTuVan, TinNhanTuVan, KhuyenMai, TichDiem, LichSuTichDiem
from orders.models import DoiTra, DonHang
from products.models import DanhGia, SanPham, BienTheSanPham
from accounts.models import KhachHang, NhanVien
from .forms import KhuyenMaiForm


def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('cskh:guest_home')

    # Nếu là khách hàng, chuyển hướng sang giao diện mua sắm
    if hasattr(request.user, 'khachhang'):
        return redirect('cskh:guest_home')

    # Lấy thống kê cơ bản dành cho Nhân viên/Admin
    chua_phan_hoi = HoiThoaiTuVan.objects.filter(TrangThai='Chưa xử lý').count()
    dang_tu_van = HoiThoaiTuVan.objects.filter(Q(TrangThai='Đang xử lý') | Q(TrangThai='Đã phản hồi')).count()
    don_can_ho_tro = DoiTra.objects.filter(TrangThai='PENDING').count()
    danh_gia_moi = DanhGia.objects.all().count()
    
    # Lấy danh sách tin nhắn gần đây có kèm nội dung tin nhắn cuối
    last_msg_qs = TinNhanTuVan.objects.filter(MaHoiThoai=OuterRef('pk')).order_by('-ThoiGianGui')
    recent_chats = HoiThoaiTuVan.objects.select_related('MaKH').annotate(
        last_msg=Subquery(last_msg_qs.values('NoiDung')[:1]),
        last_time=Subquery(last_msg_qs.values('ThoiGianGui')[:1])
    ).order_by('-last_time')[:5]
    
    khach_hang_tong = KhachHang.objects.count()

    context = {
        'chua_phan_hoi': chua_phan_hoi,
        'dang_tu_van': dang_tu_van,
        'don_can_ho_tro': don_can_ho_tro,
        'danh_gia_moi': danh_gia_moi,
        'recent_chats': recent_chats,
        'khach_hang_tong': khach_hang_tong,
        'is_staff_view': not request.user.is_superuser
    }
    return render(request, 'cskh/dashboard.html', context)


def chat_reply_view(request):
    # Fix triệt để DB dính tên trạng thái cũ
    HoiThoaiTuVan.objects.filter(TrangThai='Chưa tư vấn').update(TrangThai='Chưa xử lý')
    HoiThoaiTuVan.objects.filter(TrangThai='Đang tư vấn').update(TrangThai='Đang xử lý')
    HoiThoaiTuVan.objects.filter(TrangThai='Đã tư vấn').update(TrangThai='Đã đóng')

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
                    'TrangThai': 'Chưa xử lý'
                }
            )
            if not TinNhanTuVan.objects.filter(MaHoiThoai=ht).exists():
                # Tạo 1 user ảo đại diện cho Khách Hàng để lách luật NOT NULL của SQLite
                from django.contrib.auth.models import User
                bot_user, _ = User.objects.get_or_create(username='khachhang_bot')
                nv_khachhang, _ = NhanVien.objects.get_or_create(MaNV='NV_KH', defaults={'user': bot_user, 'HoTen': 'Khách Hàng (Hệ thống)'})
                
                TinNhanTuVan.objects.create(
                    MaTinNhan="TN" + ''.join(random.choices(string.digits, k=6)),
                    MaHoiThoai=ht, NoiDung=data['msg'], MaNV=nv_khachhang
                )

    # 2. Xử lý danh sách
    search_query = request.GET.get('search', '')
    last_msg_qs = TinNhanTuVan.objects.filter(MaHoiThoai=OuterRef('pk')).order_by('-ThoiGianGui')
    
    hoi_thoai_list = HoiThoaiTuVan.objects.select_related('MaKH').annotate(
        snippet=Subquery(last_msg_qs.values('NoiDung')[:1]),
        last_time=Subquery(last_msg_qs.values('ThoiGianGui')[:1])
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
            header_status = current_chat.TrangThai
            
            tin_nhan_list = TinNhanTuVan.objects.filter(MaHoiThoai=current_chat).order_by('ThoiGianGui')

    # 3. Xử lý Gửi tin nhắn
    if request.method == 'POST' and current_chat:
        noi_dung = request.POST.get('NoiDung')
        if noi_dung:
            ma_tn = "TN" + ''.join(random.choices(string.digits, k=6))
            nv = NhanVien.objects.exclude(MaNV='NV_KH').first()
            if not nv:
                from django.contrib.auth.models import User
                test_user, _ = User.objects.get_or_create(username='admin_test')
                nv, _ = NhanVien.objects.get_or_create(MaNV='NV_ADMIN', defaults={'user': test_user, 'HoTen': 'Admin'})
            
            TinNhanTuVan.objects.create(
                MaTinNhan=ma_tn, MaHoiThoai=current_chat, MaNV=nv, NoiDung=noi_dung
            )
            # Khi nhân viên gửi tin, nếu trạng thái là Chưa xử lý hoặc Đang xử lý -> Đã phản hồi
            if current_chat.TrangThai in ['Chưa xử lý', 'Đang xử lý']:
                current_chat.TrangThai = 'Đã phản hồi'
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


def nhan_xu_ly_view(request, ma_kh):
    if request.method == 'POST':
        chat = get_object_or_404(HoiThoaiTuVan, MaKH__MaKH=ma_kh)
        chat.TrangThai = 'Đang xử lý'
        chat.save()
    return redirect(f"/chat/reply/?ma_kh={ma_kh}")

def ket_thuc_tu_van_view(request, ma_kh):
    if request.method == 'POST':
        chat = get_object_or_404(HoiThoaiTuVan, MaKH__MaKH=ma_kh)
        chat.TrangThai = 'Đã đóng'
        chat.save()
    return redirect(f"/chat/reply/?ma_kh={ma_kh}")

def uudai_list_view(request):
    q = request.GET.get('q', '').strip()
    uudai_list = KhuyenMai.objects.all().order_by('-NgayBatDau')
    if q:
        uudai_list = uudai_list.filter(Q(TenKhuyenMai__icontains=q) | Q(MaKM__icontains=q))
    return render(request, 'cskh/uudai_list.html', {'uudai_list': uudai_list, 'search_query': q})


def uudai_detail_view(request, pk):
    q = request.GET.get('q', '').strip()
    uudai_list = KhuyenMai.objects.all().order_by('-NgayBatDau')
    if q:
        uudai_list = uudai_list.filter(Q(TenKhuyenMai__icontains=q) | Q(MaKM__icontains=q))
    uudai = get_object_or_404(KhuyenMai, pk=pk)
    return render(request, 'cskh/uudai_list.html', {'uudai_list': uudai_list, 'action': 'detail', 'selected_uudai': uudai, 'search_query': q})


def uudai_create_view(request):
    temp_makm = "UD" + "".join(random.choices(string.digits, k=4))
    
    if request.method == 'POST':
        form = KhuyenMaiForm(request.POST)
        if form.is_valid():
            makm = request.POST.get('makm')
            km_instance = form.save(commit=False)
            km_instance.MaKM = makm if makm else temp_makm
            km_instance.save()
            
            q_post = request.GET.get('q')
            url = reverse('cskh:uudai_list')
            if q_post:
                url += f"?q={q_post}"
            return redirect(url)
    else:
        form = KhuyenMaiForm()

    q = request.GET.get('q', '').strip()
    uudai_list = KhuyenMai.objects.all().order_by('-NgayBatDau')
    if q:
        uudai_list = uudai_list.filter(Q(TenKhuyenMai__icontains=q) | Q(MaKM__icontains=q))
        
    return render(request, 'cskh/uudai_list.html', {
        'uudai_list': uudai_list, 
        'action': 'create', 
        'temp_makm': temp_makm,
        'form': form,
        'search_query': q
    })


def uudai_edit_view(request, pk):
    uudai = get_object_or_404(KhuyenMai, pk=pk)
    
    if request.method == 'POST':
        form = KhuyenMaiForm(request.POST, instance=uudai)
        if form.is_valid():
            form.save()
            messages.success(request, 'edit_success')
            q_post = request.GET.get('q')
            url = reverse('cskh:uudai_list')
            if q_post:
                url += f"?q={q_post}"
            return redirect(url)
    else:
        form = KhuyenMaiForm(instance=uudai)

    q = request.GET.get('q', '').strip()
    uudai_list = KhuyenMai.objects.all().order_by('-NgayBatDau')
    if q:
        uudai_list = uudai_list.filter(Q(TenKhuyenMai__icontains=q) | Q(MaKM__icontains=q))
        
    return render(request, 'cskh/uudai_list.html', {
        'uudai_list': uudai_list, 
        'action': 'edit', 
        'selected_uudai': uudai,
        'form': form,
        'search_query': q
    })


def uudai_delete_view(request, pk):
    uudai = get_object_or_404(KhuyenMai, pk=pk)
    if request.method == 'POST':
        uudai.delete()
        messages.success(request, 'delete_success')
        q_post = request.GET.get('q')
        url = reverse('cskh:uudai_list')
        if q_post:
            url += f"?q={q_post}"
        return redirect(url)

    q = request.GET.get('q', '').strip()
    uudai_list = KhuyenMai.objects.all().order_by('-NgayBatDau')
    if q:
        uudai_list = uudai_list.filter(Q(TenKhuyenMai__icontains=q) | Q(MaKM__icontains=q))
        
    return render(request, 'cskh/uudai_list.html', {'uudai_list': uudai_list, 'action': 'delete', 'selected_uudai': uudai, 'search_query': q})


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
        lich_su = LichSuTichDiem.objects.filter(MaKH__MaKH=ma_kh).select_related('MaNV').order_by('NgayThucHien')
        ls_data = []
        running_total = 0
        for ls in lich_su:
            running_total += ls.DiemThayDoi
            ten_nv = f" (Bởi: {ls.MaNV.HoTen})" if hasattr(ls, 'MaNV') and ls.MaNV else ""
            ls_data.append({'ngay': ls.NgayThucHien.strftime('%d/%m/%Y'), 'noi_dung': f"{ls.LyDo}{ten_nv}", 'diem_thay_doi': f"+{ls.DiemThayDoi}" if ls.DiemThayDoi > 0 else str(ls.DiemThayDoi), 'ket_qua': running_total})
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
            nv = getattr(request.user, 'nhanvien', None) if request.user.is_authenticated else None
            LichSuTichDiem.objects.create(MaLS=ma_ls, MaKH=td.MaKH, MaNV=nv, DiemThayDoi=-diem_tru, LyDo='Trừ điểm', NgayThucHien=date.today())
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
            nv = getattr(request.user, 'nhanvien', None) if request.user.is_authenticated else None
            LichSuTichDiem.objects.create(MaLS=ma_ls, MaKH=td.MaKH, MaNV=nv, DiemThayDoi=chenh_lech, LyDo='Cập nhật điểm', NgayThucHien=date.today())
            return JsonResponse({'success': True, 'new_tong_diem': td.TongDiem})
        except Exception as e: return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})


def quan_ly_danh_gia_view(request):
    danh_sach_sp = SanPham.objects.all()
    return render(request, 'cskh/quan_ly_danh_gia.html', {'danh_sach_sp': danh_sach_sp})


def chi_tiet_danh_gia_view(request, ma_sp):
    san_pham = get_object_or_404(SanPham, MaSP=ma_sp)
    danh_gia_list = DanhGia.objects.filter(MaSP=ma_sp).select_related('MaKH').order_by('-NgayDanhGia')

    # Xử lý Bộ lọc
    sao = request.GET.get('sao')
    if sao and sao != 'all':
        danh_gia_list = danh_gia_list.filter(SoSao=sao)
        
    thoi_gian = request.GET.get('thoi_gian')
    if thoi_gian == 'month':
        current_month = date.today().month
        current_year = date.today().year
        danh_gia_list = danh_gia_list.filter(NgayDanhGia__month=current_month, NgayDanhGia__year=current_year)
    elif thoi_gian == 'year':
        current_year = date.today().year
        danh_gia_list = danh_gia_list.filter(NgayDanhGia__year=current_year)

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
    danh_sach_sp = SanPham.objects.all()
    return render(request, 'cskh/guest_home.html', {'san_pham_list': danh_sach_sp})


def store_product_list_view(request):
    loai = request.GET.get('loai', 'Tất cả')
    q = request.GET.get('q', '')
    san_pham_qs = SanPham.objects.all()

    if q:
        from django.db.models import Q
        san_pham_qs = san_pham_qs.filter(
            Q(MaSP__icontains=q) |
            Q(TenSP__icontains=q)
        ).distinct()

    if loai and loai != 'Tất cả':
        san_pham_qs = san_pham_qs.filter(TenSP__icontains=loai)

    return render(request, 'cskh/store_product_list.html', {
        'san_pham_list': san_pham_qs,
        'current_loai': loai,
        'search_query': q
    })


def store_product_detail_view(request, ma_sp):
    san_pham = get_object_or_404(SanPham, MaSP=ma_sp)
    variants = BienTheSanPham.objects.filter(MaSP=ma_sp)
    colors = variants.values_list('MauSac', flat=True).distinct()
    sizes = variants.values_list('Size', flat=True).distinct()
    
    rating_data = san_pham.danhgia_set.aggregate(avg=Avg('SoSao'), count=Count('MaDanhGia'))
    avg_rating = float(rating_data['avg'] or 0.0)
    san_pham.star_percent = avg_rating * 20
    
    return render(request, 'cskh/store_product_detail.html', {
        'product': san_pham,
        'variants': variants,
        'colors': colors,
        'sizes': sizes,
        'avg_rating': round(avg_rating, 1),
        'review_count': rating_data['count'],
        'color_list': list(colors),
        'size_list': list(sizes),
    })


def global_notifications(request):
    notifications = []

    try:
        # 1. Tin nhắn mới nhất (từ cuộc hội thoại Chưa xử lý)
        hoi_thoai_chua_tl = HoiThoaiTuVan.objects.filter(TrangThai='Chưa xử lý').first()
        if hoi_thoai_chua_tl:
            msg = TinNhanTuVan.objects.filter(MaHoiThoai=hoi_thoai_chua_tl).order_by('-ThoiGianGui').first()
            if msg:
                notifications.append({
                    'type': 'msg',
                    'tag': 'Tin nhắn mới',
                    'author': msg.MaHoiThoai.MaKH.HoTen if msg.MaHoiThoai.MaKH else 'Khách hàng',
                    'preview': (msg.NoiDung[:45] + '...') if len(msg.NoiDung) > 45 else msg.NoiDung,
                    'time': msg.ThoiGianGui.strftime('%H:%M - %d/%m/%Y'),
                    'link': f'/chat/reply/?ma_kh={msg.MaHoiThoai.MaKH.MaKH}' if msg.MaHoiThoai.MaKH else '/chat/reply/'
                })

        # 2. Đổi trả mới nhất (Chờ xử lý)
        dt = DoiTra.objects.filter(TrangThai='PENDING').order_by('-NgayYeuCau').first()
        if dt:
            notifications.append({
                'type': 'return',
                'tag': 'Yêu cầu đổi trả mới',
                'author': dt.MaKH.HoTen if dt.MaKH else 'Khách hàng',
                'preview': (dt.LyDo[:45] + '...') if len(dt.LyDo) > 45 else dt.LyDo,
                'time': dt.NgayYeuCau.strftime('00:00 - %d/%m/%Y'),
                'link': '/orders/doitra/'
            })

        # 3. Đánh giá mới nhất
        dg = DanhGia.objects.order_by('-NgayDanhGia').first()
        if dg:
            notifications.append({
                'type': 'review',
                'tag': 'Đánh giá mới',
                'author': dg.MaKH.HoTen if dg.MaKH else 'Khách hàng',
                'preview': (dg.NoiDung[:45] + '...') if dg.NoiDung and len(dg.NoiDung) > 45 else (dg.NoiDung or "Không có nội dung"),
                'time': dg.NgayDanhGia.strftime('00:00 - %d/%m/%Y'),
                'link': '/danh-gia/'
            })
    except Exception:
        pass # Fallback an toàn nếu thiếu DB model chưa migrate

    return {
        'nav_notifications': notifications,
        'nav_notifications_count': sum(1 for n in notifications)
    }
