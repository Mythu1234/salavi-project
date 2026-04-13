from django.shortcuts import render, redirect
from django.contrib import messages
from .models import DoiTra
from .forms import DoiTraForm

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
        doitra = None # Gửi giá trị Rỗng sang Template để nó xài Data Fallback

    if request.method == 'POST' and doitra:
        form = DoiTraForm(request.POST, instance=doitra)
        if form.is_valid():
            action = request.POST.get('action')
            doitra_instance = form.save(commit=False)
            
            if action == 'approve':
                doitra_instance.TrangThai = 'DONE'
            elif action == 'reject':
                doitra_instance.TrangThai = 'REJECT'
                
            doitra_instance.save()
            messages.success(request, action)
            status_filter_post = request.GET.get('status')
            from django.urls import reverse
            url = reverse('orders:doitra_list')
            if status_filter_post:
                url += f"?status={status_filter_post}"
            return redirect(url)
    else:
        form = DoiTraForm(instance=doitra) if doitra else None

    # Trả về cả list và selected_doitra để vẽ Modal đè lên trang List
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
