# kycform/services/policy_identity.py

import requests
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from kycform.models import KycUserInfo, KycPolicy
from kycform.utils import generate_user_id


def resolve_policy_identity(*, policy_no, dob_ad, mobile=None):
    """
    Core policy identity resolver.

    Responsibilities:
    - Validate policy against CORE (via FastAPI)
    - Verify DOB (+ mobile if provided)
    - Resolve or generate deterministic user_id
    - Link all related policies to same user_id
    - Create KycUserInfo if missing

    This function DOES NOT:
    - Handle sessions
    - Handle passwords
    - Redirect users
    """

    if not policy_no or not dob_ad:
        raise ValidationError("Policy number and DOB are required.")

    policy_no = policy_no.strip()

    headers = {
        "Authorization": f"Bearer {settings.API_TOKEN}"
    }

    # ------------------------------------------------------
    # 1) FAST PATH: already registered locally
    # ------------------------------------------------------
    existing_policy = (
        KycPolicy.objects
        .filter(policy_number__iexact=policy_no)
        .exclude(user_id__isnull=True)
        .exclude(user_id="")
        .first()
    )

    if existing_policy:
        user = KycUserInfo.objects.get(user_id=existing_policy.user_id)
        return user, user.user_id

    # ------------------------------------------------------
    # 2) LOOKUP POLICY IN CORE (FastAPI → MSSQL)
    # ------------------------------------------------------
    try:
        response = requests.get(
            f"{settings.API_BASE_URL}/mssql/newpolicies",
            params={"policy_no": policy_no, "dob": dob_ad},
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

    core_first = data["FirstName"]
    core_last = data["LastName"]
    core_dob = str(data["DOB"])
    core_mobile = str(data.get("Mobile", "")).strip()

    # ------------------------------------------------------
    # 3) VALIDATE DOB + MOBILE
    # ------------------------------------------------------
    if str(dob_ad) != core_dob:
        raise ValidationError("DOB does not match our records.")

    if mobile and core_mobile and mobile.strip() != core_mobile:
        raise ValidationError("Mobile number does not match our records.")

    # ------------------------------------------------------
    # 4) FETCH ALL RELATED POLICIES
    # ------------------------------------------------------
    try:
        response = requests.get(
            f"{settings.API_BASE_URL}/mssql/related-policies",
            params={
                "firstname": core_first,
                "lastname": core_last,
                "dob": core_dob,
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
            core_dob,
            core_mobile
        )

    # ------------------------------------------------------
    # 6) PERSIST ATOMICALLY
    # ------------------------------------------------------
    with transaction.atomic():

        user, _ = KycUserInfo.objects.get_or_create(
            user_id=user_id,
            defaults={
                "first_name": core_first,
                "last_name": core_last,
                "dob": core_dob,
                "phone_number": core_mobile,
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
