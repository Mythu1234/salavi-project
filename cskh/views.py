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

    # Nếu là Khách hàng, không cho vào Dashboard quản lý mà đẩy về Trang chủ dành cho khách
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
        hinh_anh = request.FILES.get('HinhAnh')
        if noi_dung or hinh_anh:
            ma_tn = "TN" + ''.join(random.choices(string.digits, k=6))
            nv = NhanVien.objects.exclude(MaNV='NV_KH').first()
            if not nv:
                from django.contrib.auth.models import User
                test_user, _ = User.objects.get_or_create(username='admin_test')
                nv, _ = NhanVien.objects.get_or_create(MaNV='NV_ADMIN', defaults={'user': test_user, 'HoTen': 'Admin'})
            
            TinNhanTuVan.objects.create(
                MaTinNhan=ma_tn, MaHoiThoai=current_chat, MaNV=nv, 
                NoiDung=noi_dung, HinhAnh=hinh_anh
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

@csrf_exempt
def api_submit_review(request):
    if request.method == 'POST':
        try:
            import json
            from datetime import date
            
            data = json.loads(request.body)
            ma_sp = data.get('ma_sp')
            so_sao = data.get('so_sao')
            noi_dung = data.get('noi_dung')
            
            # Lấy thông tin khách hàng
            khach_hang = getattr(request.user, 'khachhang', None)
            if not khach_hang:
                return JsonResponse({'status': 'error', 'message': 'Bạn cần đăng nhập để đánh giá'}, status=403)
            
            san_pham = SanPham.objects.get(MaSP=ma_sp)
            
            # Logic tạo mã DG0000X
            last_dg = DanhGia.objects.filter(MaDanhGia__startswith='DG').order_by('-MaDanhGia').first()
            if last_dg:
                try:
                    last_num = int(last_dg.MaDanhGia[2:])
                    new_num = last_num + 1
                except:
                    new_num = DanhGia.objects.count() + 1
            else:
                new_num = 1
            ma_dg = f"DG{new_num:05d}"
            
            # Tạo bản ghi đánh giá
            DanhGia.objects.create(
                MaDanhGia=ma_dg,
                MaKH=khach_hang,
                MaSP=san_pham,
                SoSao=so_sao,
                NoiDung=noi_dung,
                NgayDanhGia=date.today()
            )
            
            return JsonResponse({'status': 'success', 'ma_dg': ma_dg})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


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
    # 1. Nếu là Khách hàng -> Hiển thị trang Tích điểm cá nhân (màu hồng)
    khach_hang = getattr(request.user, 'khachhang', None)
    if khach_hang:
        td_obj = TichDiem.objects.filter(MaKH=khach_hang).first()
        tong_diem = td_obj.TongDiem if td_obj else 0
        history_list = LichSuTichDiem.objects.filter(MaKH=khach_hang).order_by('-NgayThucHien')
        
        context = {
            'khach_hang': khach_hang,
            'tong_diem': tong_diem,
            'history_list': history_list
        }
        return render(request, 'cskh/client_diem_tich_luy.html', context)

    # 2. Nếu là Nhân viên/Admin -> Hiển thị trang Quản lý tích điểm
    phone = request.GET.get('phone', '')
    if phone:
        danh_sach_tich_diem = TichDiem.objects.select_related('MaKH', 'MaKH__user').filter(
            MaKH__user__username__icontains=phone)
    else:
        danh_sach_tich_diem = TichDiem.objects.select_related('MaKH', 'MaKH__user').all()
    
    return render(request, 'cskh/diem_tich_luy.html', {'danh_sach_tich_diem': danh_sach_tich_diem})


def client_diem_tich_luy_view(request):
    # Lấy thông tin khách hàng của user hiện tại
    khach_hang = getattr(request.user, 'khachhang', None)
    
    if not khach_hang:
        # Nếu không phải khách hàng, chuyển hướng hoặc báo lỗi
        return render(request, 'cskh/guest_home.html')

    # Lấy tổng điểm
    td_obj = TichDiem.objects.filter(MaKH=khach_hang).first()
    tong_diem = td_obj.TongDiem if td_obj else 0

    # Lấy lịch sử tích lũy
    history_list = LichSuTichDiem.objects.filter(MaKH=khach_hang).order_by('-NgayThucHien')

    context = {
        'khach_hang': khach_hang,
        'tong_diem': tong_diem,
        'history_list': history_list
    }
    return render(request, 'cskh/client_diem_tich_luy.html', context)


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
            
            # Logic tạo mã LSTD0000X
            last_ls = LichSuTichDiem.objects.filter(MaLS__startswith='LSTD').order_by('-MaLS').first()
            if last_ls:
                last_num = int(last_ls.MaLS[4:])
                new_num = last_num + 1
            else:
                new_num = 1
            ma_ls = f"LSTD{new_num:05d}"

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

            # Logic tạo mã LSTD0000X
            last_ls = LichSuTichDiem.objects.filter(MaLS__startswith='LSTD').order_by('-MaLS').first()
            if last_ls:
                last_num = int(last_ls.MaLS[4:])
                new_num = last_num + 1
            else:
                new_num = 1
            ma_ls = f"LSTD{new_num:05d}"

            nv = getattr(request.user, 'nhanvien', None) if request.user.is_authenticated else None
            LichSuTichDiem.objects.create(MaLS=ma_ls, MaKH=td.MaKH, MaNV=nv, DiemThayDoi=chenh_lech, LyDo='Cập nhật điểm', NgayThucHien=date.today())
            return JsonResponse({'success': True, 'new_tong_diem': td.TongDiem})
        except Exception as e: return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})


def quan_ly_danh_gia_view(request):
    # Nếu là Khách hàng mà vào nhầm trang này, tự động đẩy sang trang Đánh giá sản phẩm
    if hasattr(request.user, 'khachhang'):
        from django.shortcuts import redirect
        return redirect('cskh:danh_gia_san_pham')
    
    # Lấy danh sách sản phẩm kèm theo điểm trung bình và số lượng đánh giá
    danh_sach_sp = SanPham.objects.annotate(
        avg_stars=Avg('danhgia__SoSao'),
        review_count=Count('danhgia')
    ).order_by('MaSP')
    
    return render(request, 'cskh/quan_ly_danh_gia.html', {
        'danh_sach_sp': danh_sach_sp,
        'filter_mode': None 
    })

def danh_gia_san_pham_view(request):
    khach_hang = getattr(request.user, 'khachhang', None)
    filter_mode = request.GET.get('filter')
    
    to_review_ids = []
    if khach_hang:
        from orders.models import ChiTietDonHang
        # 1. Lấy tất cả sản phẩm từ các đơn hàng ĐÃ GIAO THÀNH CÔNG (DONE)
        bought_sp_ids = ChiTietDonHang.objects.filter(
            MaDonHang__MaKH=khach_hang,
            MaDonHang__TrangThaiDonHang='DONE'
        ).values_list('MaBTSP__MaSP', flat=True).distinct()
        
        # 2. Lấy tất cả sản phẩm đã đánh giá của khách này
        reviewed_sp_ids = DanhGia.objects.filter(
            MaKH=khach_hang
        ).values_list('MaSP', flat=True).distinct()
        
        # 3. Lọc ra những ID thực sự chưa được đánh giá
        to_review_ids = [id for id in bought_sp_ids if id not in reviewed_sp_ids]

    if filter_mode == 'todo' and khach_hang:
        # CHẾ ĐỘ 2: Chỉ hiện sản phẩm CẦN ĐÁNH GIÁ
        list_sp = SanPham.objects.filter(MaSP__in=to_review_ids).annotate(
            avg_stars=Avg('danhgia__SoSao'),
            review_count=Count('danhgia')
        ).order_by('MaSP')
    else:
        # CHẾ ĐỘ 1: Hiện TOÀN BỘ sản phẩm
        list_sp = SanPham.objects.annotate(
            avg_stars=Avg('danhgia__SoSao'),
            review_count=Count('danhgia')
        ).all().order_by('MaSP')

    return render(request, 'cskh/danh_gia_san_pham.html', {
        'list_sp': list_sp,
        'khach_hang': khach_hang,
        'filter_mode': filter_mode,
        'to_review_ids': to_review_ids
    })


def chi_tiet_danh_gia_view(request, ma_sp):
    san_pham = get_object_or_404(SanPham, MaSP=ma_sp)
    all_danh_gia = DanhGia.objects.filter(MaSP=ma_sp).select_related('MaKH')
    
    # 1. Tính toán số liệu thống kê TỔNG QUAN (Luôn dựa trên tất cả đánh giá)
    tong_so_luong = all_danh_gia.count()
    sao_trung_binh = 0
    pct = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    
    if tong_so_luong > 0:
        sao_trung_binh = round(all_danh_gia.aggregate(Avg('SoSao'))['SoSao__avg'] or 0, 1)
        for s in range(1, 6):
            count_s = all_danh_gia.filter(SoSao=s).count()
            pct[s] = round((count_s / tong_so_luong) * 100)

    # 2. Xử lý BỘ LỌC cho danh sách hiển thị
    danh_gia_filtered = all_danh_gia.order_by('-NgayDanhGia')
    
    sao_filter = request.GET.get('sao')
    if sao_filter and sao_filter != 'all':
        danh_gia_filtered = danh_gia_filtered.filter(SoSao=sao_filter)
        
    thoi_gian = request.GET.get('thoi_gian')
    if thoi_gian == 'month':
        current_month = date.today().month
        current_year = date.today().year
        danh_gia_filtered = danh_gia_filtered.filter(NgayDanhGia__month=current_month, NgayDanhGia__year=current_year)
    elif thoi_gian == 'year':
        current_year = date.today().year
        danh_gia_filtered = danh_gia_filtered.filter(NgayDanhGia__year=current_year)

    # 3. Phân trang kết quả đã lọc
    paginator = Paginator(danh_gia_filtered, 5)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'san_pham': san_pham,
        'page_obj': page_obj,
        'tong_danh_gia': tong_so_luong, # Tổng số gốc
        'sao_trung_binh': sao_trung_binh,
        'pct': pct,
        'results_count': danh_gia_filtered.count() # Số lượng sau khi lọc (nếu cần dùng)
    }
    return render(request, 'cskh/chi_tiet_danh_gia.html', context)


def mot_danh_gia_view(request, ma_dg):
    danh_gia = get_object_or_404(DanhGia.objects.select_related('MaKH', 'MaSP'), MaDanhGia=ma_dg)
    return render(request, 'cskh/mot_danh_gia.html', {'danh_gia': danh_gia})


def guest_home_view(request):
    loai = request.GET.get('loai', 'Tất cả')
    san_pham_qs = SanPham.objects.all()

    if loai and loai != 'Tất cả':
        san_pham_qs = san_pham_qs.filter(TenSP__icontains=loai)

    return render(request, 'cskh/guest_home.html', {
        'san_pham_list': san_pham_qs,
        'current_loai': loai
    })


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
    
    # Sản phẩm liên quan (cùng loại dựa trên từ đầu tiên của tên SP)
    first_word = san_pham.TenSP.split(' ')[0]
    related_products = SanPham.objects.filter(TenSP__icontains=first_word).exclude(MaSP=ma_sp).annotate(
        avg_stars=Avg('danhgia__SoSao')
    )[:4]
    
    return render(request, 'cskh/store_product_detail.html', {
        'product': san_pham,
        'variants': variants,
        'colors': colors,
        'sizes': sizes,
        'avg_rating': round(avg_rating, 1) if avg_rating > 0 else 0,
        'review_count': rating_data['count'],
        'color_list': list(colors),
        'size_list': list(sizes),
        'related_products': related_products,
    })


def global_notifications(request):
    notifications = []
    user = request.user

    try:
        # 1. TRƯỜNG HỢP: NHÂN VIÊN / ADMIN (Giữ nguyên logic cũ)
        if user.is_authenticated and (user.is_superuser or user.is_staff or hasattr(user, 'nhanvien')):
            # Tin nhắn mới nhất (từ cuộc hội thoại Chưa xử lý)
            hoi_thoai_chua_tl = HoiThoaiTuVan.objects.filter(TrangThai='Chưa xử lý').first()
            if hoi_thoai_chua_tl:
                msg = TinNhanTuVan.objects.filter(MaHoiThoai=hoi_thoai_chua_tl).order_by('-ThoiGianGui').first()
                if msg:
                    notifications.append({
                        'type': 'msg',
                        'tag': 'Tin nhắn mới',
                        'author': msg.MaHoiThoai.MaKH.HoTen if msg.MaHoiThoai.MaKH else 'Khách hàng',
                        'preview': (msg.NoiDung[:45] + '...') if msg.NoiDung and len(msg.NoiDung) > 45 else msg.NoiDung,
                        'time': msg.ThoiGianGui.strftime('%H:%M - %d/%m/%Y'),
                        'link': f'/chat/reply/?ma_kh={msg.MaHoiThoai.MaKH.MaKH}' if msg.MaHoiThoai.MaKH else '/chat/reply/'
                    })

            # Đổi trả mới nhất (Chờ xử lý)
            dt = DoiTra.objects.filter(TrangThai='PENDING').order_by('-NgayYeuCau').first()
            if dt:
                notifications.append({
                    'type': 'return',
                    'tag': 'Yêu cầu đổi trả mới',
                    'author': dt.MaKH.HoTen if dt.MaKH else 'Khách hàng',
                    'preview': (dt.LyDo[:45] + '...') if dt.LyDo and len(dt.LyDo) > 45 else dt.LyDo,
                    'time': dt.NgayYeuCau.strftime('00:00 - %d/%m/%Y'),
                    'link': '/orders/doitra/'
                })

            # Đánh giá mới nhất
            dg = DanhGia.objects.order_by('-NgayDanhGia').first()
            if dg:
                notifications.append({
                    'type': 'review',
                    'tag': 'Đánh giá mới',
                    'author': dg.MaKH.HoTen if dg.MaKH else 'Khách hàng',
                    'preview': (dg.NoiDung[:45] + '...') if dg.NoiDung and len(dg.NoiDung) > 45 else (dg.NoiDung or "Không có nội dung"),
                    'time': dg.NgayDanhGia.strftime('00:00 - %d/%m/%Y'),
                    'link': f'/danh-gia/review/{dg.MaDanhGia}/'
                })

        # 2. TRƯỜNG HỢP: KHÁCH HÀNG ĐÃ ĐĂNG NHẬP
        elif user.is_authenticated and hasattr(user, 'khachhang'):
            kh = user.khachhang

            # Cập nhật trạng thái Đổi trả (Chỉ những cái đã Xử lý hoặc Từ chối)
            doitras = DoiTra.objects.filter(MaKH=kh, TrangThai__in=['DONE', 'REJECT']).order_by('-NgayYeuCau')[:2]
            for dt in doitras:
                status_text = "đã được duyệt" if dt.TrangThai == 'DONE' else "đã bị từ chối"
                notifications.append({
                    'type': 'return_update',
                    'tag': 'Cập nhật đổi trả',
                    'author': 'Hệ thống',
                    'preview': f"Yêu cầu {dt.MaDoiTra} {status_text}.",
                    'time': dt.NgayYeuCau.strftime('%d/%m/%Y'),
                    'link': '/orders/my-returns/'
                })

            # Khuyến mãi sắp tới / đang diễn ra
            promotions = KhuyenMai.objects.filter(NgayKetThuc__gte=date.today()).order_by('-NgayBatDau')[:2]
            for km in promotions:
                notifications.append({
                    'type': 'promo',
                    'tag': 'Ưu đãi mới',
                    'author': 'Salavi Store',
                    'preview': km.TenKhuyenMai,
                    'time': km.NgayBatDau.strftime('%d/%m/%Y'),
                    'link': '/store/'
                })

            # Phản hồi từ nhân viên trong chat
            chat = HoiThoaiTuVan.objects.filter(MaKH=kh).first()
            if chat:
                last_reply = TinNhanTuVan.objects.filter(MaHoiThoai=chat, MaNV__isnull=False).order_by('-ThoiGianGui').first()
                if last_reply:
                    notifications.append({
                        'type': 'chat_reply',
                        'tag': 'Tin nhắn từ shop',
                        'author': last_reply.MaNV.HoTen if last_reply.MaNV else 'Nhân viên',
                        'preview': (last_reply.NoiDung[:45] + '...') if last_reply.NoiDung and len(last_reply.NoiDung) > 45 else (last_reply.NoiDung or "Đã gửi một hình ảnh"),
                        'time': last_reply.ThoiGianGui.strftime('%H:%M - %d/%m/%Y'),
                        'link': '/chat/reply/' # Màn hình chat
                    })

        # 3. TRƯỜNG HỢP: KHÁCH VÃNG LAI (Chưa đăng nhập)
        else:
            promotions = KhuyenMai.objects.filter(NgayKetThuc__gte=date.today()).order_by('-NgayBatDau')[:3]
            for km in promotions:
                notifications.append({
                    'type': 'promo_guest',
                    'tag': 'Khuyến mãi',
                    'author': 'Salavi Store',
                    'preview': km.TenKhuyenMai,
                    'time': km.NgayBatDau.strftime('%d/%m/%Y'),
                    'link': '/store/'
                })

    except Exception:
        pass

    return {
        'nav_notifications': notifications,
        'nav_notifications_count': len(notifications)
    }

def gui_danh_gia_view(request, ma_sp):
    khach_hang = getattr(request.user, 'khachhang', None)
    if not khach_hang:
        messages.error(request, "Bạn cần đăng nhập với tư cách khách hàng để đánh giá.")
        return redirect('cskh:guest_home')

    san_pham = get_object_or_404(SanPham, MaSP=ma_sp)

    if request.method == 'POST':
        so_sao = request.POST.get('so_sao', 5)
        noi_dung = request.POST.get('noi_dung', '')
        hinh_anh = request.FILES.get('hinh_anh')

        # Tạo mã MaDanhGia tự động (DGXXXXX)
        last_dg = DanhGia.objects.filter(MaDanhGia__startswith='DG').order_by('-MaDanhGia').first()
        if last_dg:
            try:
                last_num = int(last_dg.MaDanhGia[2:])
                new_num = last_num + 1
            except:
                new_num = DanhGia.objects.count() + 1
        else:
            new_num = 1
        ma_dg = f"DG{new_num:05d}"

        # Lưu vào DB
        DanhGia.objects.create(
            MaDanhGia=ma_dg,
            MaKH=khach_hang,
            MaSP=san_pham,
            SoSao=so_sao,
            NoiDung=noi_dung,
            HinhAnh=hinh_anh,
            NgayDanhGia=date.today()
        )
        
        messages.success(request, f"Cảm ơn bạn đã đánh giá sản phẩm {san_pham.TenSP}!")
        return redirect(reverse('cskh:danh_gia_san_pham') + "?filter=todo")

    return redirect('cskh:danh_gia_san_pham')

@csrf_exempt
def api_customer_send_message(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Yêu cầu đăng nhập'}, status=403)
    
    khach_hang = getattr(request.user, 'khachhang', None)
    if not khach_hang:
        return JsonResponse({'status': 'error', 'message': 'Chỉ dành cho khách hàng'}, status=403)

    if request.method == 'POST':
        noi_dung = request.POST.get('NoiDung', '').strip()
        hinh_anh = request.FILES.get('HinhAnh')

        if not noi_dung and not hinh_anh:
            return JsonResponse({'status': 'error', 'message': 'Nội dung trống'}, status=400)

        # 1. Tìm hoặc tạo hội thoại cho khách này
        chat, created = HoiThoaiTuVan.objects.get_or_create(
            MaKH=khach_hang,
            defaults={
                'MaHoiThoai': "HT" + ''.join(random.choices(string.digits, k=6)),
                'TrangThai': 'Chưa xử lý'
            }
        )
        
        # Nếu hội thoại đã kết thúc, mở lại nó
        if chat.TrangThai == 'Đã đóng':
            chat.TrangThai = 'Chưa xử lý'
            chat.save()

        # 2. Tạo mã tin nhắn duy nhất
        ma_tn = "TN" + ''.join(random.choices(string.digits, k=6))
        
        # 3. Lưu tin nhắn (MaNV = None vì là khách gửi)
        TinNhanTuVan.objects.create(
            MaTinNhan=ma_tn,
            MaHoiThoai=chat,
            NoiDung=noi_dung,
            HinhAnh=hinh_anh
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Đã gửi tin nhắn',
            'time': datetime.now().strftime('%H:%M')
        })

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def api_get_chat_history(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Yêu cầu đăng nhập'}, status=403)
    
    khach_hang = getattr(request.user, 'khachhang', None)
    if not khach_hang:
        return JsonResponse({'status': 'error', 'message': 'Chỉ dành cho khách hàng'}, status=403)

    chat = HoiThoaiTuVan.objects.filter(MaKH=khach_hang).first()
    if not chat:
        return JsonResponse({'status': 'success', 'messages': []})

    messages_qs = TinNhanTuVan.objects.filter(MaHoiThoai=chat).order_by('ThoiGianGui')
    history = []
    for msg in messages_qs:
        history.append({
            'content': msg.NoiDung,
            'image_url': msg.HinhAnh.url if msg.HinhAnh else None,
            'time': msg.ThoiGianGui.strftime('%H:%M'),
            'is_mine': msg.MaNV is None # Nếu MaNV là None thì là khách gửi (bên phải)
        })

    return JsonResponse({'status': 'success', 'messages': history})
