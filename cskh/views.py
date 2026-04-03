from django.shortcuts import render
from .models import HoiThoaiTuVan, TinNhanTuVan, KhuyenMai
from orders.models import DoiTra
from products.models import DanhGia
from accounts.models import KhachHang
from datetime import date

def dashboard_view(request):
    # 1. THỐNG KÊ 4 Ô VUÔNG LỚN TRÊN CÙNG
    # Đếm số lượng theo Trạng thái (Giả định trạng thái có chữ Chưa hoặc Đang)
    chua_phan_hoi = HoiThoaiTuVan.objects.filter(TrangThai__icontains='Chưa').count()
    dang_tu_van = HoiThoaiTuVan.objects.filter(TrangThai__icontains='Đang').count()
    
    # Đơn cần hỗ trợ: Đếm số yêu cầu Đổi trả đang ở trạng thái 'PENDING'
    don_can_ho_tro = DoiTra.objects.filter(TrangThai='PENDING').count()
    
    danh_gia_moi = DanhGia.objects.all().count() # Tạm đếm tổng để dễ thấy số

    # 2. DANH SÁCH TIN NHẮN TƯ VẤN
    recent_chats = HoiThoaiTuVan.objects.all()[:3]

    # 3. HOẠT ĐỘNG CSKH
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

def uudai_list_view(request):
    # Kéo toàn bộ danh sách Khuyến mãi từ Database, xếp cái mới nhất lên đầu
    uudai_list = KhuyenMai.objects.all().order_by('-NgayBatDau')

    return render(request, 'cskh/uudai_list.html', {'uudai_list': uudai_list})


from django.shortcuts import render, get_object_or_404
from .models import HoiThoaiTuVan, TinNhanTuVan, TichDiem, LichSuTichDiem
from django.http import JsonResponse
import json
from datetime import date
import random
import string
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from orders.models import DoiTra, DonHang
from products.models import DanhGia, SanPham
from accounts.models import KhachHang


def dashboard_view(request):
    # 1. THỐNG KÊ 4 Ô VUÔNG LỚN TRÊN CÙNG
    # Đếm số lượng theo Trạng thái (Giả định trạng thái có chữ Chưa hoặc Đang)
    chua_phan_hoi = HoiThoaiTuVan.objects.filter(TrangThai__icontains='Chưa').count()
    dang_tu_van = HoiThoaiTuVan.objects.filter(TrangThai__icontains='Đang').count()

    # Đơn cần hỗ trợ: Đếm số yêu cầu Đổi trả đang ở trạng thái 'PENDING'
    don_can_ho_tro = DoiTra.objects.filter(TrangThai='PENDING').count()

    danh_gia_moi = DanhGia.objects.all().count()  # Tạm đếm tổng để dễ thấy số

    # 2. DANH SÁCH TIN NHẮN TƯ VẤN
    recent_chats = HoiThoaiTuVan.objects.all()[:3]

    # 3. HOẠT ĐỘNG CSKH
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


def diem_tich_luy_view(request):
    phone = request.GET.get('phone', '')
    if phone:
        # TenDangNhap lưu số điện thoại theo như dữ liệu template yêu cầu
        danh_sach_tich_diem = TichDiem.objects.select_related('MaKH', 'MaKH__user').filter(
            MaKH__user__username__icontains=phone)
    else:
        danh_sach_tich_diem = TichDiem.objects.select_related('MaKH', 'MaKH__user').all()

    context = {
        'danh_sach_tich_diem': danh_sach_tich_diem
    }
    return render(request, 'cskh/diem_tich_luy.html', context)


def api_chi_tiet_tich_diem(request, ma_kh):
    try:
        td = TichDiem.objects.select_related('MaKH', 'MaKH__user').get(MaKH__MaKH=ma_kh)
        lich_su = LichSuTichDiem.objects.filter(MaKH__MaKH=ma_kh).order_by('NgayThucHien')

        ls_data = []
        running_total = 0
        for ls in lich_su:
            running_total += ls.DiemThayDoi
            ls_data.append({
                'ngay': ls.NgayThucHien.strftime('%d/%m/%Y'),
                'noi_dung': ls.LyDo,
                'diem_thay_doi': f"+{ls.DiemThayDoi}" if ls.DiemThayDoi > 0 else str(ls.DiemThayDoi),
                'ket_qua': running_total
            })

        # Sắp xếp mới nhất lên đầu
        ls_data.reverse()

        data = {
            'ho_ten': td.MaKH.HoTen,
            'ma_kh': td.MaKH.MaKH,
            'sdt': td.MaKH.user.username,
            'tong_diem': td.TongDiem,
            'lich_su': ls_data
        }
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def api_tru_tich_diem(request, ma_kh):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            diem_tru = int(body.get('diem_tru', 0))

            if diem_tru <= 0:
                return JsonResponse({'success': False, 'error': 'Số điểm không hợp lệ.'})

            td = TichDiem.objects.get(MaKH__MaKH=ma_kh)

            if diem_tru > td.TongDiem:
                return JsonResponse({'success': False, 'error': 'Số điểm xóa không được lớn hơn điểm hiện tại.'})

            # Trừ điểm
            td.TongDiem -= diem_tru
            td.save()

            # Tạo ngẫu nhiên mã lịch sử (vd LS + 6 so)
            ma_ls = "LS" + ''.join(random.choices(string.digits, k=6))
            while LichSuTichDiem.objects.filter(MaLS=ma_ls).exists():
                ma_ls = "LS" + ''.join(random.choices(string.digits, k=6))

            LichSuTichDiem.objects.create(
                MaLS=ma_ls,
                MaKH=td.MaKH,
                DiemThayDoi=-diem_tru,
                LyDo='Trừ điểm',
                NgayThucHien=date.today()
            )

            return JsonResponse({'success': True, 'new_tong_diem': td.TongDiem})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@csrf_exempt
def api_sua_tich_diem(request, ma_kh):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            diem_moi = int(body.get('diem_moi', -1))

            if diem_moi < 0:
                return JsonResponse({'success': False, 'error': 'Số điểm không hợp lệ.'})

            td = TichDiem.objects.get(MaKH__MaKH=ma_kh)

            chenh_lech = diem_moi - td.TongDiem
            if chenh_lech != 0:
                td.TongDiem = diem_moi
                td.save()

                ma_ls = "LS" + ''.join(random.choices(string.digits, k=6))
                while LichSuTichDiem.objects.filter(MaLS=ma_ls).exists():
                    ma_ls = "LS" + ''.join(random.choices(string.digits, k=6))

                LichSuTichDiem.objects.create(
                    MaLS=ma_ls,
                    MaKH=td.MaKH,
                    DiemThayDoi=chenh_lech,
                    LyDo='Cập nhật điểm' if chenh_lech > 0 else 'Trừ điểm (Cập nhật)',
                    NgayThucHien=date.today()
                )

            return JsonResponse({'success': True, 'new_tong_diem': td.TongDiem})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})


def quan_ly_danh_gia_view(request):
    danh_sach_sp = SanPham.objects.all()
    return render(request, 'cskh/quan_ly_danh_gia.html', {'danh_sach_sp': danh_sach_sp})


def chi_tiet_danh_gia_view(request, ma_sp):
    san_pham = get_object_or_404(SanPham, MaSP=ma_sp)
    danh_gia_list = DanhGia.objects.filter(MaSP=ma_sp).select_related('MaKH').order_by('-NgayDanhGia')

    tong_danh_gia = danh_gia_list.count()
    sao_trung_binh = danh_gia_list.aggregate(Avg('SoSao'))['SoSao__avg'] or 0
    sao_trung_binh = round(sao_trung_binh, 1)

    stats = {
        '5': danh_gia_list.filter(SoSao=5).count(),
        '4': danh_gia_list.filter(SoSao=4).count(),
        '3': danh_gia_list.filter(SoSao=3).count(),
        '2': danh_gia_list.filter(SoSao=2).count(),
        '1': danh_gia_list.filter(SoSao=1).count(),
    }
    pct = {k: (v / tong_danh_gia * 100 if tong_danh_gia > 0 else 0) for k, v in stats.items()}

    paginator = Paginator(danh_gia_list, 5)  # 5 đánh giá một trang
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'san_pham': san_pham,
        'page_obj': page_obj,
        'tong_danh_gia': tong_danh_gia,
        'sao_trung_binh': sao_trung_binh,
        'stats': stats,
        'pct': pct
    }
    return render(request, 'cskh/chi_tiet_danh_gia.html', context)


def mot_danh_gia_view(request, ma_dg):
    danh_gia = get_object_or_404(DanhGia.objects.select_related('MaKH', 'MaSP'), MaDanhGia=ma_dg)
    return render(request, 'cskh/mot_danh_gia.html', {'danh_gia': danh_gia})


from django.shortcuts import render
from .models import HoiThoaiTuVan, TinNhanTuVan
from orders.models import DoiTra
from products.models import DanhGia
from accounts.models import KhachHang
from datetime import date


def dashboard_view(request):
    # 1. THỐNG KÊ 4 Ô VUÔNG LỚN TRÊN CÙNG
    # Đếm số lượng theo Trạng thái (Giả định trạng thái có chữ Chưa hoặc Đang)
    chua_phan_hoi = HoiThoaiTuVan.objects.filter(TrangThai__icontains='Chưa').count()
    dang_tu_van = HoiThoaiTuVan.objects.filter(TrangThai__icontains='Đang').count()

    # Đơn cần hỗ trợ: Đếm số yêu cầu Đổi trả đang ở trạng thái 'PENDING'
    don_can_ho_tro = DoiTra.objects.filter(TrangThai='PENDING').count()

    danh_gia_moi = DanhGia.objects.all().count()  # Tạm đếm tổng để dễ thấy số

    # 2. DANH SÁCH TIN NHẮN TƯ VẤN
    recent_chats = HoiThoaiTuVan.objects.all()[:3]

    # 3. HOẠT ĐỘNG CSKH
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


def chat_view(request):
    return render(request, 'cskh/chat.html')


def chat_reply_view(request):
    return render(request, 'cskh/chat_reply.html')


def guest_home_view(request):
    # Trang chủ tĩnh dành cho khách chưa đăng nhập (Guest)
    return render(request, 'cskh/guest_home.html')
