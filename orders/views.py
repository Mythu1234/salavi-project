from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import DoiTra, ChiTietDonHang, DonHang
from .forms import DoiTraForm
import random
import string
from datetime import date
from django.urls import reverse

def doitra_list_view(request):
    if hasattr(request.user, 'khachhang'):
        return redirect('orders:customer_doitra_list')

    status_filter = request.GET.get('status')
    base_qs = DoiTra.objects.all().order_by('-NgayYeuCau')
    
    total_count = base_qs.count()
    pending_count = base_qs.filter(TrangThai='PENDING').count()
    done_count = base_qs.filter(TrangThai='DONE').count()
    reject_count = base_qs.filter(TrangThai='REJECT').count()
    
    if status_filter:
        doitra_list = base_qs.filter(TrangThai=status_filter)
    else:
        doitra_list = base_qs
    
    context = {
        'doitra_list': doitra_list,
        'status_filter': status_filter,
        'total_count': total_count,
        'pending_count': pending_count,
        'done_count': done_count,
        'reject_count': reject_count,
    }
    
    return render(request, 'orders/doitra_list.html', context)

def doitra_detail_view(request, pk):
    try:
        doitra = DoiTra.objects.get(pk=pk)
    except DoiTra.DoesNotExist:
        doitra = None

    if request.method == 'POST' and doitra:
        action = request.POST.get('action')
        # Lấy ghi chú từ form, nếu không có thì giữ lại ghi chú cũ
        ghi_chu = request.POST.get('GhiChuXuLy', doitra.GhiChuXuLy)

        if action in ['approve', 'reject']:
            if action == 'approve':
                doitra.TrangThai = 'DONE'
                messages.success(request, f"Đã duyệt thành công yêu cầu '{doitra.MaDoiTra}'.")
            else:  # 'reject'
                doitra.TrangThai = 'REJECT'
                messages.success(request, f"Đã từ chối yêu cầu '{doitra.MaDoiTra}'.")

            doitra.GhiChuXuLy = ghi_chu
            # Chỉ cập nhật các trường cần thiết để tránh lỗi foreign key
            doitra.save(update_fields=['TrangThai', 'GhiChuXuLy'])

            # Redirect về trang list, giữ nguyên bộ lọc status
            status_filter_post = request.GET.get('status')
            url = reverse('orders:doitra_list')
            if status_filter_post:
                url += f"?status={status_filter_post}"
            return redirect(url)

    # Logic cho GET request hoặc nếu POST không hợp lệ
    form = DoiTraForm(instance=doitra) if doitra else None
    status_filter = request.GET.get('status')
    base_qs = DoiTra.objects.all().order_by('-NgayYeuCau')
    
    total_count = base_qs.count()
    pending_count = base_qs.filter(TrangThai='PENDING').count()
    done_count = base_qs.filter(TrangThai='DONE').count()
    reject_count = base_qs.filter(TrangThai='REJECT').count()
    
    if status_filter:
        doitra_list = base_qs.filter(TrangThai=status_filter)
    else:
        doitra_list = base_qs

    context = {
        'doitra_list': doitra_list,
        'selected_doitra': doitra,
        'form': form,
        'status_filter': status_filter,
        'total_count': total_count,
        'pending_count': pending_count,
        'done_count': done_count,
        'reject_count': reject_count,
    }
    
    return render(request, 'orders/doitra_list.html', context)

# --- CUSTOMER VIEWS ---

def customer_doitra_list_view(request):
    """Màn hình liệt kê những yêu cầu đổi trả đã gửi của khách hàng đó"""
    if not hasattr(request.user, 'khachhang'):
        return redirect('accounts:login')
    
    kh = request.user.khachhang
    doitra_list = DoiTra.objects.filter(MaKH=kh).order_by('-NgayYeuCau')
    
    context = {
        'doitra_list': doitra_list,
    }
    return render(request, 'orders/customer_doitra_list.html', context)

def customer_doitra_product_select_view(request):
    """Màn hình những sản phẩm mình đã mua và chưa có yêu cầu đổi trả"""
    if not hasattr(request.user, 'khachhang'):
        return redirect('accounts:login')
    
    kh = request.user.khachhang
    
    # Lấy ID của các ChiTietDonHang đã có yêu cầu đổi trả
    existing_doitra_ids = DoiTra.objects.filter(MaKH=kh).values_list('MaCTDH_id', flat=True)
    
    # Tìm các sản phẩm từ các đơn hàng đã giao (DONE) và chưa đổi trả
    eligible_items = ChiTietDonHang.objects.filter(
        MaDonHang__MaKH=kh,
        MaDonHang__TrangThaiDonHang='DONE'
    ).exclude(MaCTDH__in=existing_doitra_ids).select_related('MaDonHang', 'MaBTSP', 'MaBTSP__MaSP')
    
    context = {
        'eligible_items': eligible_items,
    }
    return render(request, 'orders/customer_doitra_select.html', context)

def customer_doitra_create_view(request, ctdh_id):
    """Màn hình form nhập thông tin yêu cầu đổi trả"""
    if not hasattr(request.user, 'khachhang'):
        return redirect('accounts:login')
    
    kh = request.user.khachhang
    ctdh = get_object_or_404(ChiTietDonHang, MaCTDH=ctdh_id, MaDonHang__MaKH=kh)
    form_errors = {}
    
    if request.method == 'POST':
        loai = request.POST.get('LoaiYeuCau')
        ly_do = request.POST.get('LyDo')
        hinh_anh = request.FILES.get('HinhAnh')
        
        # Exception flows: Check required fields using inline errors dict
        if not hinh_anh:
            form_errors['HinhAnh'] = "Hình ảnh minh chứng thiếu. Vui lòng tải ảnh lên"
        
        if not ly_do or not ly_do.strip():
            form_errors['LyDo'] = "Lý do không thể trống. Vui lòng nhập lại"
        
        if not form_errors:
            try:
                ma_dt = "DT" + ''.join(random.choices(string.digits, k=6))
                DoiTra.objects.create(
                    MaDoiTra=ma_dt,
                    MaCTDH=ctdh,
                    MaKH=kh,
                    LoaiYeuCau=loai,
                    LyDo=ly_do,
                    HinhAnh=hinh_anh,
                    NgayYeuCau=date.today(),
                    TrangThai='PENDING'
                )
                messages.success(request, "Gửi yêu cầu thành công")
                return redirect('orders:customer_doitra_list')
            except Exception:
                form_errors['system'] = "Hệ thống đang lỗi, không thể gửi yêu cầu"
    
    doitra_list = DoiTra.objects.filter(MaKH=kh).order_by('-NgayYeuCau')
    
    context = {
        'ctdh': ctdh,
        'form_errors': form_errors,
        'doitra_list': doitra_list,
    }
    return render(request, 'orders/customer_doitra_form.html', context)

def customer_doitra_detail_view(request, ma_doitra):
    """Màn hình chi tiết một yêu cầu đổi trả"""
    if not hasattr(request.user, 'khachhang'):
        return redirect('accounts:login')
    
    kh = request.user.khachhang
    # Lấy thông tin đổi trả và các thông tin liên quan (Chi tiết đơn hàng, đơn hàng)
    doitra = get_object_or_404(
        DoiTra.objects.select_related('MaCTDH', 'MaCTDH__MaDonHang', 'MaCTDH__MaBTSP', 'MaCTDH__MaBTSP__MaSP'), 
        MaDoiTra=ma_doitra, 
        MaKH=kh
    )
    
    doitra_list = DoiTra.objects.filter(MaKH=kh).order_by('-NgayYeuCau')
    
    context = {
        'doitra': doitra,
        'doitra_list': doitra_list,
    }
    return render(request, 'orders/customer_doitra_detail.html', context)
