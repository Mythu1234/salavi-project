from django.urls import path
from . import views

app_name = 'cskh'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('uudai/', views.uudai_list_view, name='uudai_list'),
    path('uudai/detail/<str:pk>/', views.uudai_detail_view, name='uudai_detail'),
    path('uudai/create/', views.uudai_create_view, name='uudai_create'),
    path('uudai/edit/<str:pk>/', views.uudai_edit_view, name='uudai_edit'),
    path('uudai/delete/<str:pk>/', views.uudai_delete_view, name='uudai_delete'),
    path('diem-tich-luy/', views.diem_tich_luy_view, name='diem_tich_luy'),
    path('diem-tich-luy/api/<str:ma_kh>/', views.api_chi_tiet_tich_diem, name='api_chi_tiet_tich_diem'),
    path('diem-tich-luy/api/<str:ma_kh>/tru-diem/', views.api_tru_tich_diem, name='api_tru_tich_diem'),
    path('diem-tich-luy/api/<str:ma_kh>/sua-diem/', views.api_sua_tich_diem, name='api_sua_tich_diem'),
    path('danh-gia/', views.quan_ly_danh_gia_view, name='quan_ly_danh_gia'),
    path('danh-gia/chi-tiet/<str:ma_sp>/', views.chi_tiet_danh_gia_view, name='chi_tiet_danh_gia'),
    path('danh-gia/review/<str:ma_dg>/', views.mot_danh_gia_view, name='mot_danh_gia'),
    path('chat/reply/', views.chat_reply_view, name='chat_reply'),
    path('store/', views.guest_home_view, name='guest_home'),
]









