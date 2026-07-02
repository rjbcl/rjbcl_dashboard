import requests
from urllib.parse import urljoin

from django.conf import settings
from django.utils import timezone

from kycform.models import KycSmsNotification


VERIFIED_SMS_MESSAGE = "RJBCL KYC: तपाईंको KYC सफलतापूर्वक प्रमाणीकरण गरिएको छ। राष्ट्रिय जीवन बीमा कम्पनी लिमिटेडप्रति विश्वासका लागि धन्यवाद।"


def _get_sms_gateway_url():
    base_url = (getattr(settings, "API_SERVICE_BASE_URL", "") or "").strip()
    if base_url:
        return urljoin(base_url.rstrip("/") + "/", "otp/send")
    return (getattr(settings, "SMS_GATEWAY_URL", "") or "").strip()


def send_kyc_verified_sms(user, mobile=None, actor_identifier="ADMIN", source="ADMIN"):
    """
    Create a persistent notification row and try to deliver the SMS.

    The database record is always saved so the verification message is
    auditable even if the downstream SMS gateway is unavailable.
    """
    resolved_mobile = (mobile or user.phone_number or "").strip()

    notification = KycSmsNotification.objects.create(
        user=user,
        mobile=resolved_mobile,
        message=VERIFIED_SMS_MESSAGE,
        template_name="kyc_verified",
        source=source,
        delivery_status="PENDING",
    )

    if not resolved_mobile:
        notification.delivery_status = "SKIPPED"
        notification.error_message = "No mobile number available for SMS delivery."
        notification.save(update_fields=["delivery_status", "error_message", "updated_at"])
        return notification

    gateway_url = _get_sms_gateway_url()
    if not gateway_url:
        notification.delivery_status = "SKIPPED"
        notification.error_message = "API service is not configured."
        notification.save(update_fields=["delivery_status", "error_message", "updated_at"])
        return notification

    payload = {
        "mobile": resolved_mobile,
        "message": VERIFIED_SMS_MESSAGE,
    }

    try:
        response = requests.post(
            gateway_url,
            json=payload,
            timeout=getattr(settings, "SMS_GATEWAY_TIMEOUT", 15),
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        notification.delivery_status = "FAILED"
        notification.error_message = str(exc)
        notification.save(update_fields=["delivery_status", "error_message", "updated_at"])
        return notification

    provider_reference = None
    try:
        data = response.json()
        provider_reference = data.get("message_id") or data.get("reference") or data.get("id") or data.get("uuid")
    except ValueError:
        provider_reference = None

    notification.delivery_status = "SENT"
    notification.provider_reference = provider_reference
    notification.sent_at = timezone.now()
    notification.save(
        update_fields=[
            "delivery_status",
            "provider_reference",
            "sent_at",
            "updated_at",
        ]
    )
    return notification
