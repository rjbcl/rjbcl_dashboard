from django.urls import path
from . import views  # 👈 this refers to kycform/views.py

urlpatterns = [
    path('', views.auth_view, name='kyc_auth'),          # First page: authentication
    path('kyc-form/', views.kyc_form_view, name='kyc_form'),  # Main KYC form
]

# kycform/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.auth_view, name='kyc_auth'),
    path('kyc-form/', views.kyc_form_view, name='kyc_form'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
