# kycform/api_urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import api_views

urlpatterns = [
    # Authentication
    path('login/', api_views.api_policyholder_login, name='api_login'),
    path('logout/', api_views.api_logout, name='api_logout'),
    path('register/', api_views.api_policyholder_register, name='api_register'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/', api_views.api_user_profile, name='api_user_profile'),
    
    # KYC Operations
    path('kyc/data/', api_views.api_get_kyc_data, name='api_get_kyc_data'),
    path('kyc/save/', api_views.api_save_kyc_progress, name='api_save_progress'),
    path('kyc/submit/', api_views.api_submit_kyc, name='api_submit_kyc'),
]