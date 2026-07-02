from rest_framework.response import Response

from kycform.api.policy_base import PolicySessionBaseAPIView
from kycform.services.policy_client import PolicyClientService
from kycform.services.policy_payment_history import PolicyPaymentHistoryService


class PolicyPaymentHistoryAPIView(PolicySessionBaseAPIView):
    def get(self, request):
        user_id, _, error = self._session_user_context(request)
        if error:
            return error

        policy_no = (request.GET.get("policy_no") or "").strip()
        page_raw = request.GET.get("page")
        page_size_raw = request.GET.get("page_size")
        paginated = page_raw is not None or page_size_raw is not None
        try:
            page = int(page_raw or 1)
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(page_size_raw or 10)
        except (TypeError, ValueError):
            page_size = 10

        client_id = PolicyClientService.get_client_no(user_id)
        data = PolicyPaymentHistoryService.get_payment_history(
            client_id=client_id,
            policy_no=policy_no,
            page=page,
            page_size=page_size,
            paginated=paginated,
        )
        return Response(data)
