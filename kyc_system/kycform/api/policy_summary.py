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

        root_policy = KycPolicy.objects.filter(policy_number=policy_no).first()
        if not root_policy or not root_policy.user_id:
            return Response({"detail": "Policy mapping not found"}, status=404)

        policy_numbers = list(
            KycPolicy.objects.filter(user_id=root_policy.user_id).values_list(
                "policy_number", flat=True
            )
        )

        data = get_policy_dashboard_data(policy_numbers or [policy_no])
        return Response(data)
