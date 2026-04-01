from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.add_product, name='add_product'),
    path('edit/<str:pk>/', views.edit_product, name='edit_product'),
    path('detail/<str:pk>/', views.product_detail, name='product_detail'),
    path('delete/<str:pk>/', views.delete_product, name='delete_product'),
    
    # Success Views
    path('success/add/', views.add_success, name='add_success'),
    path('success/edit/', views.edit_success, name='edit_success'),
    path('success/delete/', views.delete_success, name='delete_success'),
]
