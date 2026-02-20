from rest_framework_simplejwt.tokens import AccessToken

def generate_agent_access_token(agent_code: str) -> str:
    token = AccessToken()
    token["agent_code"] = agent_code
    token["role"] = "agent"
    return str(token)
