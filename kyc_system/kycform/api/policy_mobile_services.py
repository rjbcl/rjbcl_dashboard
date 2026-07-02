from django.conf import settings
from rest_framework.response import Response

from kycform.api.policy_base import PolicySessionBaseAPIView


class PolicyPaymentOptionsAPIView(PolicySessionBaseAPIView):
    def get(self, request):
        _, _, error = self._session_user_context(request)
        if error:
            return error

        type_code = (request.GET.get("type_code") or "").strip().lower()
        all_types = [
            {
                "id": 1,
                "title": "Premium Payment",
                "code": "premium-payment",
                "description": "Continue to the official premium payment portal.",
                "items": [
                    {
                        "id": 1,
                        "title": "Premium Payment Portal",
                        "subtitle": "Pay your premium online in a new tab.",
                        "icon_url": None,
                        "action_url": settings.PREMIUM_PAYMENT_URL,
                        "metadata": {},
                    }
                ],
            },
            {
                "id": 2,
                "title": "Loan Payment",
                "code": "loan-payment",
                "description": "Continue to the official policy loan repayment portal.",
                "items": [
                    {
                        "id": 2,
                        "title": "Loan Repayment Portal",
                        "subtitle": "Repay your policy loan online in a new tab.",
                        "icon_url": None,
                        "action_url": settings.LOAN_REPAYMENT_URL,
                        "metadata": {},
                    }
                ],
            },
        ]

        if type_code:
            all_types = [item for item in all_types if item["code"] == type_code]
            if not all_types:
                return Response({"detail": "PAYMENT_TYPE_NOT_FOUND"}, status=404)

        payload = {
            "service_id": 1,
            "service_title": "Payments",
            "config_version": "local-v1",
            "screen_title": "Payment",
            "payment_section": {
                "title": "Payment Options",
                "subtitle": "Use the available official links below.",
                "logo_url": None,
                "types": all_types,
            },
            "help_support": {
                "title": "Help & Support",
                "subtitle": "Contact RJBCL support if you have trouble opening any payment link.",
            },
        }
        return Response(payload)


class PolicyForeignEmploymentAPIView(PolicySessionBaseAPIView):
    def get(self, request):
        _, _, error = self._session_user_context(request)
        if error:
            return error

        payload = {
            "service_id": 1,
            "service_title": "Foreign Employment",
            "config_version": "local-v1",
            "screen_title": "Foreign Policy",
            "policy_section": {
                "title": "Foreign Employment Policies",
                "subtitle": "Access the official foreign policy information.",
                "logo_url": None,
                "types": [
                    {
                        "id": 1,
                        "title": "Foreign Policy",
                        "code": "foreign-policy",
                        "description": "Official foreign policy resources and information.",
                        "icon_url": None,
                        "action_label": "Open",
                        "action_url": settings.FOREIGN_POLICY_URL,
                        "items": [
                            {
                                "id": 1,
                                "title": "Foreign Policy Portal",
                                "subtitle": "Open the official foreign policy page in a new tab.",
                                "icon_url": None,
                                "action_url": settings.FOREIGN_POLICY_URL,
                                "metadata": {},
                            }
                        ],
                    }
                ],
            },
            "help_support": {
                "title": "Help & Support",
                "subtitle": "Contact RJBCL support if you need assistance with foreign policy information.",
            },
        }
        return Response(payload)
