from django.shortcuts import render
from .models import DoiTra

def doitra_list_view(request):
    # Lấy toàn bộ danh sách đổi trả từ Database
    doitra_list = DoiTra.objects.all().order_by('-NgayYeuCau')
    
    context = {
        'doitra_list': doitra_list
    }
    
    return render(request, 'orders/doitra_list.html', context)

def doitra_detail_view(request, pk):
    try:
        doitra = DoiTra.objects.get(pk=pk)
    except DoiTra.DoesNotExist:
        doitra = None # Gửi giá trị Rỗng sang Template để nó xài Data Fallback

    context = {
        'doitra': doitra
    }
    
    return render(request, 'orders/doitra_detail.html', context)
