# kycform/services/policy_identity.py

import requests
from datetime import datetime, date

from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from kycform.models import KycUserInfo, KycPolicy
from kycform.utils import generate_user_id


# ------------------------------------------------------
# INTERNAL: Normalize DOB to python date
# ------------------------------------------------------
def _normalize_dob(value):
    """
    CORE may return DOB as:
    - datetime.date
    - datetime.datetime
    - string (YYYY-MM-DD)

    Always normalize to datetime.date
    """
    if not value:
        return None

    if isinstance(value, date):
        return value

    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except Exception:
        raise ValidationError("Invalid DOB format received from core system.")


# ------------------------------------------------------
# MAIN IDENTITY RESOLVER
# ------------------------------------------------------
def resolve_policy_identity(*, policy_no, dob_ad, mobile=None):
    """
    Core policy identity resolver.

    Responsibilities:
    - Validate policy against CORE (via FastAPI)
    - STRICTLY verify DOB (+ mobile if provided)
    - Resolve or generate deterministic user_id
    - Link all related policies to same user_id
    - Create KycUserInfo if missing

    IMPORTANT:
    - DOB is ALWAYS validated (no bypass)
    - DOB is stored as DATE (not string)
    - DOB is used as DEFAULT PASSWORD (hashed)
    """

    # ------------------------------------------------------
    # 0) BASIC INPUT VALIDATION
    # ------------------------------------------------------
    if not policy_no or not dob_ad:
        raise ValidationError("Policy number and DOB are required.")

    policy_no = policy_no.strip()
    input_dob = _normalize_dob(dob_ad)

    headers = {
        "Authorization": f"Bearer {settings.API_TOKEN}"
    }

    # ------------------------------------------------------
    # 1) FAST PATH — LOCALLY REGISTERED POLICY (WITH DOB CHECK)
    # ------------------------------------------------------
    existing_policy = (
        KycPolicy.objects
        .filter(policy_number__iexact=policy_no)
        .exclude(user_id__isnull=True)
        .exclude(user_id="")
        .first()
    )

    if existing_policy:
        try:
            user = KycUserInfo.objects.get(user_id=existing_policy.user_id)
        except KycUserInfo.DoesNotExist:
            raise ValidationError("User record not found.")

        if not user.dob:
            raise ValidationError("DOB not available for verification.")

        # 🔒 STRICT DOB VALIDATION
        if user.dob != input_dob:
            raise ValidationError("DOB does not match our records.")

        # Optional mobile validation
        if mobile and user.phone_number:
            if mobile.strip() != user.phone_number.strip():
                raise ValidationError("Mobile number does not match our records.")

        return user, user.user_id

    # ------------------------------------------------------
    # 2) LOOKUP POLICY IN CORE SYSTEM (FastAPI → MSSQL)
    # ------------------------------------------------------
    try:
        response = requests.get(
            f"{settings.API_BASE_URL}/mssql/newpolicies",
            params={
                "policy_no": policy_no,
                "dob": input_dob.isoformat(),
            },
            headers=headers,
            timeout=10,
        )
    except requests.RequestException:
        raise ValidationError("Core policy service unavailable.")

    if response.status_code == 404:
        raise ValidationError("Policy not found in core system.")

    if response.status_code != 200:
        raise ValidationError("Error during policy verification.")

    payload = response.json()
    if not payload:
        raise ValidationError("Invalid response from core system.")

    data = payload[0]

    core_first = data.get("FirstName")
    core_last = data.get("LastName")
    core_dob = _normalize_dob(data.get("DOB"))
    core_mobile = str(data.get("Mobile", "")).strip()

    # ------------------------------------------------------
    # 3) CORE DATA VALIDATION (MANDATORY)
    # ------------------------------------------------------
    if input_dob != core_dob:
        raise ValidationError("DOB does not match our records.")

    if mobile and core_mobile:
        if mobile.strip() != core_mobile:
            raise ValidationError("Mobile number does not match our records.")

    # ------------------------------------------------------
    # 4) FETCH RELATED POLICIES (CORE)
    # ------------------------------------------------------
    try:
        response = requests.get(
            f"{settings.API_BASE_URL}/mssql/related-policies",
            params={
                "firstname": core_first,
                "lastname": core_last,
                "dob": core_dob.isoformat(),
                "mobile": core_mobile,
            },
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        related_policies = set(response.json())
    except Exception:
        raise ValidationError("Could not resolve related policies.")

    related_policies.add(policy_no)

    # ------------------------------------------------------
    # 5) RESOLVE OR GENERATE user_id
    # ------------------------------------------------------
    linked = (
        KycPolicy.objects
        .filter(policy_number__in=related_policies)
        .exclude(user_id__isnull=True)
        .exclude(user_id="")
        .first()
    )

    if linked:
        user_id = linked.user_id
    else:
        user_id = generate_user_id(
            core_first,
            core_last,
            core_dob.isoformat(),
            core_mobile
        )

    # ------------------------------------------------------
    # 6) PERSIST ATOMICALLY (LOCAL DB)
    # ------------------------------------------------------
    with transaction.atomic():

        user, created = KycUserInfo.objects.get_or_create(
            user_id=user_id,
            defaults={
                "first_name": core_first,
                "last_name": core_last,
                "dob": core_dob,  # ✅ ALWAYS date
                "phone_number": core_mobile,
                # 🔐 RESTORE ORIGINAL BEHAVIOR
                # Default password = DOB (YYYYMMDD), hashed
                "password": make_password(core_dob.strftime("%Y%m%d")),
            }
        )

        for pn in related_policies:
            KycPolicy.objects.update_or_create(
                policy_number=pn,
                defaults={
                    "user_id": user_id,
                    "created_at": timezone.now().date(),
                }
            )

    return user, user_id
