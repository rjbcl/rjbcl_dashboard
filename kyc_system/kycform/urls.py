from django.urls import path
from . import views

urlpatterns = [

    # --------------------
    # LOGIN ROUTES
    # --------------------
    path('', views.policyholder_login, name='policy_login'),
    path('auth/policy/', views.policyholder_login, name='policy_login'),
    path('auth/agent/', views.agent_login, name='agent_login'),

    # --------------------
    # REGISTRATION ROUTES
    # --------------------
    path('register/', views.policyholder_register_view, name='policy_register'),
    path('register/agent/', views.agent_register_view, name='agent_register'),

    # --------------------
    # DASHBOARD ROUTES
    # --------------------
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('agent-dashboard/', views.agent_dashboard_view, name='agent_dashboard'),

    # --------------------
    # KYC FORM PAGE
    # --------------------
    path('kyc-form/', views.kyc_form_view, name='kyc_form'),
]
