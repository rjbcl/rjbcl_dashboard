from django.core.cache import cache
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

        session_user_id = request.session.get("policy_user_id")
        if session_user_id:
            return session_user_id, policy_no, None

        cache_key = f"policy:session_user_id:{policy_no}"
        user_id = cache.get(cache_key)

        if user_id is None:
            policy = KycPolicy.objects.filter(policy_number=policy_no).values("user_id").first()
            user_id = policy.get("user_id") if policy else None
            if not user_id:
                return None, None, Response({"detail": "Policy mapping not found"}, status=404)
            cache.set(cache_key, user_id, 300)

        request.session["policy_user_id"] = user_id
        return user_id, policy_no, None
