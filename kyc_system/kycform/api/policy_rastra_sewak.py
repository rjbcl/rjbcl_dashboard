from rest_framework.response import Response

from kycform.api.policy_base import PolicySessionBaseAPIView
from kycform.services.policy_rastra_sewak import PolicyRastraSewakService


class PolicyRastraSewakAPIView(PolicySessionBaseAPIView):
    def post(self, request):
        _, _, error = self._session_user_context(request)
        if error:
            return error

        policy_no = str(request.data.get("policy_no", "")).strip()
        dob = request.data.get("dob")
        try:
            page = int(request.data.get("page", 1) or 1)
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(request.data.get("page_size", 10) or 10)
        except (TypeError, ValueError):
            page_size = 10

        if not policy_no or not dob:
            return Response({"detail": "POLICY_NO_AND_DOB_REQUIRED"}, status=400)

        data = PolicyRastraSewakService.get_details(
            policy_no=policy_no,
            dob=dob,
            page=page,
            page_size=page_size,
        )

        if data.get("detail") == "CORE_DB_UNAVAILABLE":
            return Response({"detail": "CORE_DB_UNAVAILABLE"}, status=503)

        if data.get("detail") == "NO_ALLOWED_GROUP_CONFIGURED":
            return Response({"detail": "NO_ALLOWED_GROUP_CONFIGURED"}, status=400)

        if data["total"] == 0:
            return Response({"detail": "NO_RECORD_FOUND"}, status=404)

        return Response(data)
