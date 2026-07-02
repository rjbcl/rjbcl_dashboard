import requests
from requests import RequestException

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from kycform.services.claim_status import fetch_claim_status


def verify_recaptcha(token):
    if settings.DEBUG:
        return bool(token)

    if not getattr(settings, "RECAPTCHA_SECRET_KEY", ""):
        return False

    try:
        response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": settings.RECAPTCHA_SECRET_KEY,
                "response": token,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("success", False)
    except (RequestException, ValueError):
        return False


class ClaimStatusHistoryAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        policy_no = str(request.data.get("policy_no", "")).strip()
        token = str(request.data.get("g-recaptcha-response", "")).strip()
        if not policy_no:
            return Response({"ok": False, "message": "Policy number is required."}, status=400)

        if not token:
            return Response({"ok": False, "message": "Please complete the reCAPTCHA verification."}, status=400)

        if not verify_recaptcha(token):
            return Response({"ok": False, "message": "reCAPTCHA verification failed."}, status=400)

        history_data = fetch_claim_status(policy_no)
        if not history_data.get("claims"):
            return Response({"ok": False, "message": "No claim status records found for this policy."}, status=404)

        return Response(
            {
                "ok": True,
                "holder": history_data.get("holder", {}),
                "claims": history_data.get("claims", []),
            }
        )
