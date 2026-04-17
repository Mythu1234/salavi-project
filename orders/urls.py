from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # --- STAFF URLS ---
    path('doitra/', views.doitra_list_view, name='doitra_list'),
    path('doitra/<str:pk>/', views.doitra_detail_view, name='doitra_detail'),

    # --- CUSTOMER URLS ---
    path('my-returns/', views.customer_doitra_list_view, name='customer_doitra_list'),
    path('my-returns/select/', views.customer_doitra_product_select_view, name='customer_doitra_product_select'),
    path('my-returns/create/<str:ctdh_id>/', views.customer_doitra_create_view, name='customer_doitra_create'),
    path('my-returns/<str:ma_doitra>/', views.customer_doitra_detail_view, name='customer_doitra_detail'),
]
