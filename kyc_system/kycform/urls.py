from django.urls import path
from . import views

app_name = "kyc"   # Namespacing recommended for all enterprise modules

urlpatterns = [

    # -------------------------------
    # AUTHENTICATION (LOGIN)
    # -------------------------------
    path("", views.policyholder_login, name="login"),  
    path("auth/policy/", views.policyholder_login, name="policy_login"),
    path("auth/agent/", views.agent_login, name="agent_login"),

    # -------------------------------
    # REGISTRATION
    # -------------------------------
    path("register/", views.policyholder_register_view, name="policy_register"),

    path("register/agent/", views.agent_register_view, name="agent_register"),

    # -------------------------------
    # POLICYHOLDER APPLICATION FLOWS
    # -------------------------------
    path("kyc-form/", views.kyc_form_view, name="kyc_form"),
    path("kyc-submit/", views.kyc_form_submit, name="kyc_submit"),
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # -------------------------------
    # AGENT APPLICATION FLOWS
    # -------------------------------
    path("agent-dashboard/", views.agent_dashboard_view, name="agent_dashboard"),

]
