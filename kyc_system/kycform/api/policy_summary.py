from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView

from kycform.models import KycPolicy
from kycform.services.policy_dashboard import get_policy_dashboard_data


class PolicySummaryAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        if not request.session.get("authenticated"):
            return Response({"detail": "Policy holder not authenticated"}, status=401)

        policy_no = request.session.get("policy_no")
        if not policy_no:
            return Response({"detail": "Policy holder session invalid"}, status=401)

        session_user_id = request.session.get("policy_user_id")
        if session_user_id:
            user_id = session_user_id
        else:
            root_policy = KycPolicy.objects.filter(policy_number=policy_no).values("user_id").first()
            user_id = root_policy.get("user_id") if root_policy else None
            if not user_id:
                return Response({"detail": "Policy mapping not found"}, status=404)
            request.session["policy_user_id"] = user_id

        cache_key = f"policy:summary:{user_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        policy_numbers_key = f"policy:user_policies:{user_id}"
        policy_numbers = cache.get(policy_numbers_key)
        if policy_numbers is None:
            policy_numbers = list(
                KycPolicy.objects.filter(user_id=user_id).values_list("policy_number", flat=True)
            )
            cache.set(policy_numbers_key, policy_numbers, 300)

        data = get_policy_dashboard_data(policy_numbers or [policy_no])
        cache.set(cache_key, data, 60)
        return Response(data)
