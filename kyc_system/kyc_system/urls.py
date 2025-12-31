from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path("superadmin/", admin.site.urls),
    path("", include("kycform.urls", namespace="kyc")),
    path('api/auth/', include('react_frontend.urls')),
    
    # Serve React app for login page
    path('login/', TemplateView.as_view(template_name='index.html'), name='react_login'),
]

# Serve media files in development and production
if settings.DEBUG or not settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)