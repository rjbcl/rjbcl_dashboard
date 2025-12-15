# utils.py
import hashlib

def generate_user_id(first_name, last_name, dob, mobile):
    """
    Generate stable deterministic user_id for the same insured.

    Based on core-available fields:
    - first_name
    - last_name
    - dob (YYYY-MM-DD)
    - mobile

    This ensures:
    - Same customer → same user_id
    - Multiple policies of same person do NOT create duplicate accounts
    - No dependency on policy number or citizenship (which may change/not exist)
    """

    base = f"{first_name.strip().lower()}|{last_name.strip().lower()}|{dob}|{mobile.strip()}"

    # SHA-256 → 12 chars → prefix "CUS"
    uid_hash = hashlib.sha256(base.encode()).hexdigest()
    return "CUS" + uid_hash[:12]

from kycform.models import KycChangeLog

def log_kyc_change(
    submission,
    action,
    actor_type,
    actor_identifier=None,
    field_name=None,
    old_value=None,
    new_value=None,
    comment=None,
):
    """
    Centralized audit logger for KYC changes.
    """
    KycChangeLog.objects.create(
        submission=submission,
        action=action,
        actor_type=actor_type,
        actor_identifier=actor_identifier,
        field_name=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        comment=comment,
    )
