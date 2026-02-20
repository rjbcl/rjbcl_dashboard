from rest_framework.response import Response

from kycform.api.policy_base import PolicySessionBaseAPIView
from kycform.services.policy_client import PolicyClientService
from kycform.services.policy_payment_history import PolicyPaymentHistoryService


class PolicyPaymentHistoryAPIView(PolicySessionBaseAPIView):
    def get(self, request):
        user_id, _, error = self._session_user_context(request)
        if error:
            return error

        client_id = PolicyClientService.get_client_no(user_id)
        data = PolicyPaymentHistoryService.get_payment_history(client_id)
        return Response(data)
