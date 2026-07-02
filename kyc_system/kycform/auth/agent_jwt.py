from rest_framework_simplejwt.tokens import AccessToken
from datetime import timedelta

def generate_agent_access_token(agent_code: str):
    token = AccessToken()
    token["agent_code"] = agent_code
    token["role"] = "agent"
    token.set_exp(lifetime=timedelta(hours=8))
    return str(token)
