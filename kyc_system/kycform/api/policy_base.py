from rest_framework.response import Response
from rest_framework.views import APIView

from kycform.models import KycPolicy


class PolicySessionBaseAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def _session_user_context(self, request):
        if not request.session.get("authenticated"):
            return None, None, Response({"detail": "Policy holder not authenticated"}, status=401)

        policy_no = request.session.get("policy_no")
        if not policy_no:
            return None, None, Response({"detail": "Policy holder session invalid"}, status=401)

        policy = KycPolicy.objects.filter(policy_number=policy_no).first()
        if not policy or not policy.user_id:
            return None, None, Response({"detail": "Policy mapping not found"}, status=404)

        return policy.user_id, policy_no, None
