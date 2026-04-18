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
    path('my-points/', views.client_diem_tich_luy_view, name='client_diem_tich_luy'),
    path('diem-tich-luy/api/<str:ma_kh>/', views.api_chi_tiet_tich_diem, name='api_chi_tiet_tich_diem'),
    path('diem-tich-luy/api/<str:ma_kh>/tru-diem/', views.api_tru_tich_diem, name='api_tru_tich_diem'),
    path('diem-tich-luy/api/<str:ma_kh>/sua-diem/', views.api_sua_tich_diem, name='api_sua_tich_diem'),
    path('danh-gia/', views.quan_ly_danh_gia_view, name='quan_ly_danh_gia'),
    path('danh-gia-san-pham/', views.danh_gia_san_pham_view, name='danh_gia_san_pham'),
    path('submit-danh-gia/', views.api_submit_review, name='api_submit_review'),
    path('danh-gia/chi-tiet/<str:ma_sp>/', views.chi_tiet_danh_gia_view, name='chi_tiet_danh_gia'),
    path('gui-danh-gia/<str:ma_sp>/', views.gui_danh_gia_view, name='gui_danh_gia'),
    path('danh-gia/review/<str:ma_dg>/', views.mot_danh_gia_view, name='mot_danh_gia'),
    path('chat/reply/', views.chat_reply_view, name='chat_reply'),
    path('chat/nhan/<str:ma_kh>/', views.nhan_xu_ly_view, name='nhan_xu_ly'),
    path('chat/ket-thuc/<str:ma_kh>/', views.ket_thuc_tu_van_view, name='ket_thuc_tu_van'),
    path('api/chat/send/', views.api_customer_send_message, name='api_customer_send_message'),
    path('api/chat/history/', views.api_get_chat_history, name='api_get_chat_history'),
    path('store/', views.guest_home_view, name='guest_home'),
    path('store/product/<str:ma_sp>/', views.store_product_detail_view, name='store_product_detail'),
    path('store/products/', views.store_product_list_view, name='store_product_list'),
]








