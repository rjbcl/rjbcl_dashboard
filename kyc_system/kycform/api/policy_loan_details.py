from rest_framework.response import Response

from kycform.api.policy_base import PolicySessionBaseAPIView
from kycform.services.policy_client import PolicyClientService
from kycform.services.policy_loan_details import PolicyLoanDetailsService


class PolicyLoanDetailsAPIView(PolicySessionBaseAPIView):
    def get(self, request):
        user_id, _, error = self._session_user_context(request)
        if error:
            return error

        page_raw = request.GET.get("page")
        page_size_raw = request.GET.get("page_size")
        try:
            page = int(page_raw or 1)
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(page_size_raw or 10)
        except (TypeError, ValueError):
            page_size = 10

        policy_numbers = PolicyClientService.user_policy_numbers(user_id)
        data = PolicyLoanDetailsService.get_loan_details(
            policy_numbers=policy_numbers,
            page=page,
            page_size=page_size,
        )

        if data.get("detail") == "CORE_DB_UNAVAILABLE":
            return Response({"detail": "CORE_DB_UNAVAILABLE"}, status=503)

        if data.get("detail") == "LOAN_TABLE_NOT_FOUND":
            return Response({"detail": "LOAN_TABLE_NOT_FOUND"}, status=404)

        if data.get("detail") == "LOAN_POLICY_COLUMN_NOT_FOUND":
            return Response({"detail": "LOAN_POLICY_COLUMN_NOT_FOUND"}, status=400)

        return Response(data)
