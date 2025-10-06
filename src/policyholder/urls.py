from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('login/', views.login_policyholder, name='login_policyholder'),
    path('forget-password/', views.forget_password, name='forget-password'),
    path('register/', views.register_policy, name='register-policy'),

]
