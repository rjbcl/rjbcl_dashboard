from fastapi import APIRouter, HTTPException, Request
from .utils import generate_otp
from .sms import send_sms

# THIS NAME MUST BE EXACTLY "router"
router = APIRouter(prefix="/otp", tags=["OTP"])


@router.post("/send")
async def send_otp(request: Request, mobile: str = ""):
    payload = {}
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            payload = {}
    except Exception:
        payload = {}

    resolved_mobile = (payload.get("mobile") or mobile or "").strip()
    custom_message = (payload.get("message") or "").strip()

    if not resolved_mobile:
        raise HTTPException(status_code=400, detail="mobile is required")

    if custom_message:
        message = custom_message
        otp = None
    else:
        otp = generate_otp()
        message = f"Your RJBCL KYC OTP is {otp}. Valid for 2 minutes."

    status, response = send_sms(resolved_mobile, message)

    if status != 200:
        raise HTTPException(status_code=502, detail=response)

    response_body = {
        "success": True,
        "message": "SMS sent successfully",
    }
    if otp is not None:
        response_body["otp"] = otp

    return response_body
