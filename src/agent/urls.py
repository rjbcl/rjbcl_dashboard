from django.urls import path, include
from . import views

urlpatterns = [
    path('register/', views.register_agent, name='register_agent'),
    path('login/', views.login_agent, name='login_agent'),
    path('forget-password/', views.forget_password, name='forget_password'),
]
