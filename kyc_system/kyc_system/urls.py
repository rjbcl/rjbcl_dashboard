from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("superadmin/", admin.site.urls),


    # All KYC system actions
    path("", include("kycform.urls", namespace="kyc")),
]
