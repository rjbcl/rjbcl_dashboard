from pydantic import BaseModel

# Request body model
class RegistrationRequest(BaseModel):
    policy_no: str
    dob: str   # YYYY-MM-DD
