from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('kycform.urls')),  # ✅ Only include the app's URLs
]
