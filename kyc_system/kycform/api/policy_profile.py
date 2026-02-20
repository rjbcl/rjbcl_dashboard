from rest_framework.response import Response

from kycform.api.policy_base import PolicySessionBaseAPIView
from kycform.services.policy_profile import PolicyProfileService


class PolicyProfileAPIView(PolicySessionBaseAPIView):
    def get(self, request):
        user_id, _, error = self._session_user_context(request)
        if error:
            return error

        data = PolicyProfileService.get_profile(user_id)
        if not data:
            return Response({"detail": "POLICY_HOLDER_NOT_FOUND"}, status=404)
        return Response(data)
