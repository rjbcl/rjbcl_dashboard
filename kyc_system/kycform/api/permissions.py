from rest_framework.permissions import BasePermission


class IsAgentSessionAuthenticated(BasePermission):
    """
    Session-based permission for agent APIs
    """

    def has_permission(self, request, view):
        return (
            request.session.get("agent_authenticated") is True
            and request.session.get("agent_code") is not None
        )
