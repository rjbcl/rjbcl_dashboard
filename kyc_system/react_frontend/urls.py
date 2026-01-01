from django.urls import path
from .views import PolicyHolderLoginView, LogoutView, GetCSRFToken, CheckAuthView, DirectKYCEntryView  

app_name = 'react_frontend'

urlpatterns = [
    path('csrf/', GetCSRFToken.as_view(), name='csrf'),
    path('policyholder/login/', PolicyHolderLoginView.as_view(), name='policyholder-login'),
    path('direct-kyc/', DirectKYCEntryView.as_view(), name='direct-kyc'), 
    path('logout/', LogoutView.as_view(), name='logout'),
    path('check-auth/', CheckAuthView.as_view(), name='check-auth'),
]