from django.shortcuts import render, redirect
from django.contrib import messages
from .models import DoiTra
from .forms import DoiTraForm
from django.urls import reverse

def doitra_list_view(request):
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
