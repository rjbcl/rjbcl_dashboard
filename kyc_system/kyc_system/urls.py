from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("superadmin/", admin.site.urls),

    # All KYC system actions
    path("", include("kycform.urls", namespace="kyc")),
]

# Serve media files in development and production
if settings.DEBUG or not settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)