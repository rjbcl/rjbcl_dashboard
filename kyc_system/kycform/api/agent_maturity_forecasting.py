from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView

from kycform.services.agent_maturity_forecasting import AgentMaturityForecastingService


def _get_pagination_params(request):
    try:
        page = int(request.GET.get("page", 1))
    except (TypeError, ValueError):
        page = 1

    try:
        page_size = int(request.GET.get("page_size", 10))
    except (TypeError, ValueError):
        page_size = 10

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10
    if page_size > 100:
        page_size = 100

    return page, page_size


def _attach_pagination(data, page, page_size):
    rows = data.get("rows") if isinstance(data, dict) else []
    total_items = int(data.get("total_items", len(rows)) or 0)
    total_pages = (total_items + page_size - 1) // page_size if total_items else 0
    payload = dict(data)
    payload.pop("total_items", None)
    payload["pagination"] = {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": bool(total_pages and page < total_pages),
        "has_previous": bool(total_pages and page > 1),
    }
    return payload


class AgentMaturityForecastingAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        page, page_size = _get_pagination_params(request)

        if not request.session.get("agent_authenticated"):
            raise AuthenticationFailed("AGENT_NOT_AUTHENTICATED")

        agent_code = request.session.get("agent_code")
        if not agent_code:
            raise AuthenticationFailed("INVALID_AGENT_SESSION")

        policy_no = request.GET.get("policy_no", "").strip()

        data = AgentMaturityForecastingService.get_maturity_forecasting(
            agent_code=agent_code,
            policy_no=policy_no,
            page=page,
            page_size=page_size,
        )

        return Response(_attach_pagination(data, page, page_size))
