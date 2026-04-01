from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Gắn URL cho danh sách
    path('doitra/', views.doitra_list_view, name='doitra_list'),
    
    # Gắn URL cho màn hình xem chi tiết 1 đơn (PK là mã DoiTra)
    path('doitra/<str:pk>/', views.doitra_detail_view, name='doitra_detail'),
]
