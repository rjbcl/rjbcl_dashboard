from django.urls import path
from kycform.api.agent_summary import AgentSummaryAPIView
from kycform.api.agent_profile import AgentProfileAPIView
from kycform.api.agent_business_report import AgentBusinessReportAPIView
from kycform.api.agent_due_report import AgentDueReportAPIView
from kycform.api.agent_commission_report import AgentCommissionReportAPIView
from kycform.api.agent_hierarchy import AgentHierarchyAPIView
from kycform.api.agent_downline_business_report import AgentDownlineBusinessReportAPIView
from kycform.api.agent_maturity_forecasting import AgentMaturityForecastingAPIView
from kycform.api.policy_summary import PolicySummaryAPIView
from kycform.api.policy_profile import PolicyProfileAPIView
from kycform.api.policy_policies import PolicyPoliciesAPIView
from kycform.api.policy_payment_history import PolicyPaymentHistoryAPIView
from kycform.api.policy_renewal_pending import PolicyRenewalPendingAPIView
from kycform.api.policy_rastra_sewak import PolicyRastraSewakAPIView
from kycform.api.policy_loan_details import PolicyLoanDetailsAPIView
from kycform.api.claim_status import ClaimStatusHistoryAPIView
from kycform.api.policy_mobile_services import (
    PolicyForeignEmploymentAPIView,
    PolicyPaymentOptionsAPIView,
)
from . import views

app_name = "kyc"

urlpatterns = [

    # -------------------------------
    # AUTHENTICATION (LOGIN)
    # -------------------------------
    path("", views.direct_kyc_entry_view, name="DirectKYCEntry"),
    path("auth/policy/", views.policyholder_login, name="policy_login"),
    path("auth/agent/", views.agent_login, name="agent_login"),

    # POLICY LOGOUT (NEW)
    path("logout/", views.policy_logout, name="policy_logout"),
    path("agent/logout/", views.agent_logout, name="agent_logout"),
    path("contact-us/", views.contact_us_view, name="contact_us"),

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
    path("policy/profile/", views.policy_profile_view, name="policy_profile"),
    path("policy/policies/", views.policy_policies_view, name="policy_policies"),
    path("policy/payment-history/", views.policy_payment_history_view, name="policy_payment_history"),
    path("policy/payment-history/export/", views.policy_payment_history_export, name="policy_payment_history_export"),
    path("policy/payment-history/receipt/", views.policy_payment_receipt_download, name="policy_payment_receipt_download"),
    path("policy/renewal-pending/", views.policy_renewal_pending_view, name="policy_renewal_pending"),
    path("policy/payment/", views.policy_payment_view, name="policy_payment"),
    path("policy/loan-repayment/", views.policy_loan_repayment_view, name="policy_loan_repayment"),
    path("policy/loan-details/", views.policy_loan_details_view, name="policy_loan_details"),
    path("policy/foreign-policy/", views.policy_foreign_policy_view, name="policy_foreign_policy"),
    path("policy/claim-process/", views.policy_claim_process_view, name="policy_claim_process"),
    path("policy/online-file-claim/", views.policy_online_file_claim_view, name="policy_online_file_claim"),
    path("claim-status/", views.policy_claim_status_view, name="claim_status"),
    path("policy/claim-status/", views.policy_claim_status_view, name="policy_claim_status"),
    path("policy/rastra-sewak/", views.policy_rastra_sewak_view, name="policy_rastra_sewak"),

    # -------------------------------
    # AGENT WORKFLOW
    # -------------------------------
    path("agent-dashboard/", views.agent_dashboard_view, name="agent_dashboard"),
    path("agent-profile/", views.agent_profile_view, name="agent_profile"),
    path("business-report/", views.business_report, name="business_report"),
    path("due-report/", views.due_report, name="due_report"),
    path("commission-report/", views.commission_report, name="commission_report"),
    path("agent-hierarchy/", views.agent_hierarchy, name="agent_hierarchy"),
    path("downline-business-report/", views.downline_business_report, name="downline_business_report"),
    path("maturity-forecasting/", views.agent_maturity_forecasting, name="agent_maturity_forecasting"),
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

    # -------------------------------
    # API ENDPOINTS
    path("api/agent/summary/", AgentSummaryAPIView.as_view()),
    path("api/agent/profile/", AgentProfileAPIView.as_view()),
    path("api/agent/business-report/", AgentBusinessReportAPIView.as_view(), name="agent_business_report"),
    path("api/agent/due-report/", AgentDueReportAPIView.as_view(), name="agent_due_report"),
    path("api/agent/commission-report/", AgentCommissionReportAPIView.as_view(), name="agent_commission_report"),
    path("api/agent/hierarchy/", AgentHierarchyAPIView.as_view(), name="agent_hierarchy_api"),
    path("api/agent/downline-business-report/", AgentDownlineBusinessReportAPIView.as_view(), name="agent_downline_business_report_api"),
    path("api/policy/summary/", PolicySummaryAPIView.as_view(), name="policy_summary_api"),
    path("api/policy/profile/", PolicyProfileAPIView.as_view(), name="policy_profile_api"),
    path("api/policy/policies/", PolicyPoliciesAPIView.as_view(), name="policy_policies_api"),
    path("api/policy/payment-history/", PolicyPaymentHistoryAPIView.as_view(), name="policy_payment_history_api"),
    path("api/policy/renewal-pending/", PolicyRenewalPendingAPIView.as_view(), name="policy_renewal_pending_api"),
    path("api/policy/rastra-sewak/", PolicyRastraSewakAPIView.as_view(), name="policy_rastra_sewak_api"),
    path("api/policy/loan-details/", PolicyLoanDetailsAPIView.as_view(), name="policy_loan_details_api"),
    path("api/policy/payment-options/", PolicyPaymentOptionsAPIView.as_view(), name="policy_payment_options_api"),
    path("api/policy/foreign-employment/", PolicyForeignEmploymentAPIView.as_view(), name="policy_foreign_employment_api"),
    path("api/agent/maturity-forecasting/", AgentMaturityForecastingAPIView.as_view(), name="agent_maturity_forecasting_api"),
    path("api/claim-status/history/", ClaimStatusHistoryAPIView.as_view(), name="claim_status_history_api"),
    path("api/policy/claim-status/history/", ClaimStatusHistoryAPIView.as_view(), name="policy_claim_status_history_api"),
]

