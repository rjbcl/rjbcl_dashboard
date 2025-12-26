from fastapi import APIRouter, HTTPException
from .utils import generate_otp
from .sms import send_sms

# THIS NAME MUST BE EXACTLY "router"
router = APIRouter(prefix="/otp", tags=["OTP"])


@router.post("/send")
def send_otp(mobile: str):
    otp = generate_otp()

    message = f"Your RJBCL KYC OTP is {otp}. Valid for 2 minutes."

    status, response = send_sms(mobile, message)

    if status != 200:
        raise HTTPException(status_code=502, detail=response)

    return {
        "success": True,
        "otp": otp
    }
