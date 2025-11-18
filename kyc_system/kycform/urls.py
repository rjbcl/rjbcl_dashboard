from django.urls import path
from . import views

urlpatterns = [
    path('', views.auth_view, name='kyc_auth'),

    path('auth/policy/', views.policyholder_login, name='policy_login'),
    path('auth/agent/', views.agent_login, name='agent_login'),

    path('kyc-form/', views.kyc_form_view, name='kyc_form'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('agent-dashboard/', views.agent_dashboard_view, name='agent_dashboard'),
    path('register/', views.register_view, name='register'),
]
