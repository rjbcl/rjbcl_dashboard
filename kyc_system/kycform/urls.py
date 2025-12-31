from django.urls import path
from . import views

app_name = "kyc"

urlpatterns = [

    # -------------------------------
    # AUTHENTICATION (LOGIN)
    # -------------------------------
    path("", views.policyholder_login, name="login"),
    path("auth/policy/", views.policyholder_login, name="policy_login"),
    path("auth/agent/", views.agent_login, name="agent_login"),

    # POLICY LOGOUT (NEW)
    path("logout/", views.policy_logout, name="policy_logout"),

    # CUSTOM RJBC ADMIN LOGIN (NOT Django admin)
    path("rjbcl-admin/login/", views.admin_login, name="admin_login"),
    path("rjbcl-admin/logout/", views.admin_logout, name="admin_logout"),

    # -------------------------------
    # REGISTRATION
    # -------------------------------
    path("register/", views.policyholder_register_view, name="policy_register"),
    path("register/agent/", views.agent_register_view, name="agent_register"),

    # -------------------------------
    # POLICY HOLDER WORKFLOW
    # -------------------------------
    path("kyc-form/", views.kyc_form_view, name="kyc_form"),
    path("kyc-submit/", views.kyc_form_submit, name="kyc_submit"),
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # -------------------------------
    # AGENT WORKFLOW
    # -------------------------------
    path("agent-dashboard/", views.agent_dashboard_view, name="agent_dashboard"),

    # -------------------------------
    # ADMIN DASHBOARD
    # -------------------------------
    path("rjbcl-admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),

    # -------------------------------
    # PASSWORD FLOW
    # -------------------------------
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("reset-password/", views.reset_password, name="reset_password"),

    # -------------------------------
    # SAVE PROGRESS ENDPOINT
    # -------------------------------
    path("save-progress/", views.save_kyc_progress, name="save_kyc_progress"),

    # -------------------------------
    # DOCUMENT VIEWING (SECURE)
    # -------------------------------
    path(
        "kyc/additional-doc/<int:doc_id>/",
        views.view_additional_doc,
        name="view_additional_doc"
    ),
    # -------------------------------
    # DIRECT KYC ENTRY (NO LOGIN)
    path("direct-kyc/", views.direct_kyc_entry_view, name="direct_kyc_entry"),

    # -------------------------------
    # KYC SUBMITTED CONFIRMATION
    path("kyc-submitted/", views.kyc_submitted_view, name="kyc_submitted"),

    # -------------------------------
    # MOBILE OTP SENDING
    path("otp/send/", views.send_mobile_otp, name="send_mobile_otp"),
    path("otp/verify/", views.verify_mobile_otp, name="verify_mobile_otp"),


]
