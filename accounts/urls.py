from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='accounts:login', permanent=False)),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('forgot_password/', views.forgot_password_view),
    path('customers/', views.customer_list_view, name='customer_list'),
    path('customers/add/', views.customer_create_view, name='customer_create'),
    path('customers/<str:customer_code>/delete/', views.customer_delete_view, name='customer_delete'),
    path('customers/<str:customer_code>/edit/', views.customer_edit_view, name='customer_edit'),
    path('customers/<str:customer_code>/', views.customer_detail_view, name='customer_detail'),
]
