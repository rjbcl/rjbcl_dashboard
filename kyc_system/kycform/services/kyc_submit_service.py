# kycform/services/kyc_submit_service.py
import os
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import datetime
from django.core.files.storage import default_storage
from django.utils.dateparse import parse_date

from kycform.models import (
    KycUserInfo,
    KycPolicy,
    KycSubmission,
    KycDocument,
)

DOC_MAP = {
    "photo": "PHOTO",
    "citizenship-front": "CITIZENSHIP_FRONT",
    "citizenship-back": "CITIZENSHIP_BACK",
    "signature": "SIGNATURE",
    "nid": "NID",
}


def _safe_int(val, field_name, default=None):
    """
    Convert to int if possible; raise ValidationError if required and invalid.
    """
    if val is None or val == "":
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid integer for {field_name}: {val}")


@transaction.atomic
def process_kyc_submission(request):
    """
    KYC submission handler with correct field mapping for your HTML.
    """

    print("===== DEBUG: RAW POST KEYS =====")
    print(list(request.POST.keys()))
    print("================================")

    # ----------------------------------------------------
    # 1. POLICY → USER LOOKUP
    # ----------------------------------------------------
    policy_no = request.POST.get("policy_no")
    if not policy_no:
        raise ValidationError("policy_no missing in form submission.")

    try:
        policy = KycPolicy.objects.get(policy_number=policy_no)
    except KycPolicy.DoesNotExist:
        raise ValidationError(f"Policy '{policy_no}' not found.")

    try:
        user = KycUserInfo.objects.get(user_id=policy.user_id)
    except KycUserInfo.DoesNotExist:
        raise ValidationError(f"User '{policy.user_id}' not found.")

    # ----------------------------------------------------
    # 2. UPDATE BASIC USER INFO
    # ----------------------------------------------------
    user.first_name = request.POST.get("first_name") or user.first_name
    user.middle_name = request.POST.get("middle_name") or None
    user.last_name = request.POST.get("last_name") or user.last_name
    user.full_name_nep = request.POST.get("full_name_nep") or user.full_name_nep

    user.email = request.POST.get("email") or user.email
    user.phone_number = request.POST.get("mobile") or user.phone_number

    # DOB (AD)
    dob_raw = request.POST.get("dob_ad")
    dob_parsed = parse_date(dob_raw)
    if not dob_parsed:
        raise ValidationError(f"Invalid DOB (dob_ad): {dob_raw}")
    user.dob = dob_parsed

    # set KYC status to pending
    user.kyc_status = "PENDING"
    user.save()

    # ----------------------------------------------------
    # 3. LOAD EXISTING SUBMISSION or CREATE NEW ONE
    # ----------------------------------------------------
    try:
        submission = KycSubmission.objects.get(user=user)
    except KycSubmission.DoesNotExist:
        submission = KycSubmission(user=user)

    # ----------------------------------------------------
    # PERSONAL DETAILS
    # ----------------------------------------------------
    submission.salutation = request.POST.get("salutation") or None
    submission.gender = request.POST.get("gender") or ""
    submission.nationality = request.POST.get("nationality") or ""

    submission.marital_status = request.POST.get("marital_status") or ""
    submission.spouse_name = request.POST.get("spouse_name") or None

    submission.father_name = request.POST.get("father_name") or ""
    submission.mother_name = request.POST.get("mother_name") or ""
    submission.grand_father_name = request.POST.get("grand_father_name") or ""
    submission.father_in_law_name = request.POST.get("father_in_law_name") or None

    submission.son_name = request.POST.get("son_name") or None
    submission.daughter_name = request.POST.get("daughter_name") or None
    submission.daughter_in_law_name = request.POST.get("daughter_in_law_name") or None

    # MISSING FIELD (fix)
    submission.proposer_name = request.POST.get("proposer_name") or None

    # ----------------------------------------------------
    # CITIZENSHIP
    # ----------------------------------------------------
    submission.citizenship_no = request.POST.get("citizenship_no") or ""
    submission.citizenship_issued_place = request.POST.get("citizenship_place") or ""
    submission.citizen_bs = request.POST.get("citizen_bs") or ""

    citizen_ad_raw = request.POST.get("citizen_ad")
    citizen_ad_parsed = parse_date(citizen_ad_raw)
    if not citizen_ad_parsed:
        raise ValidationError(f"Invalid citizen_ad: {citizen_ad_raw}")
    submission.citizen_ad = citizen_ad_parsed

    submission.passport_no = request.POST.get("passport_no") or None
    submission.nid_no = request.POST.get("nid_no") or None

    # ----------------------------------------------------
    # ADDRESS
    # ----------------------------------------------------
    submission.perm_province = request.POST.get("perm_province") or ""
    submission.perm_district = request.POST.get("perm_district") or ""
    submission.perm_municipality = request.POST.get("perm_municipality") or ""
    submission.perm_ward = _safe_int(request.POST.get("perm_ward"), "perm_ward")
    submission.perm_address = request.POST.get("perm_address") or ""
    submission.perm_house_number = request.POST.get("perm_house_number") or None

    submission.temp_province = request.POST.get("temp_province") or ""
    submission.temp_district = request.POST.get("temp_district") or ""
    submission.temp_municipality = request.POST.get("temp_municipality") or ""
    submission.temp_ward = _safe_int(request.POST.get("temp_ward"), "temp_ward")
    submission.temp_address = request.POST.get("temp_address") or ""
    submission.temp_house_number = request.POST.get("temp_house_number") or None

    # ----------------------------------------------------
    # BANK & PROFESSIONAL
    # ----------------------------------------------------
    submission.bank_name = request.POST.get("bank_name") or ""
    submission.bank_branch = request.POST.get("branch_name") or ""
    submission.bank_account_number = request.POST.get("account_number") or ""
    submission.bank_account_type = request.POST.get("account_type") or ""

    submission.occupation = request.POST.get("occupation") or ""
    submission.occupation_description = request.POST.get("occupation_description") or None
    submission.income_mode = request.POST.get("income_mode") or "Monthly"
    submission.income_source = request.POST.get("income_source") or ""

    # Annual income integer
    try:
        submission.annual_income = int(request.POST.get("annual_income") or 0)
    except:
        raise ValidationError("Invalid annual_income")

    submission.pan_number = request.POST.get("pan_number") or ""
    submission.qualification = request.POST.get("qualification") or ""
    submission.employer_name = request.POST.get("employer_name") or None
    submission.office_address = request.POST.get("office_address") or None

    # ----------------------------------------------------
    # NOMINEE
    # ----------------------------------------------------
    submission.nominee_name = request.POST.get("nominee_name") or ""
    submission.nominee_relation = request.POST.get("nominee_relation") or ""
    submission.nominee_dob_bs = request.POST.get("nominee_dob_bs") or ""

    nominee_dob_ad_raw = request.POST.get("nominee_dob_ad")
    nominee_dob_ad_parsed = parse_date(nominee_dob_ad_raw)
    if not nominee_dob_ad_parsed:
        raise ValidationError(f"Invalid nominee_dob_ad: {nominee_dob_ad_raw}")
    submission.nominee_dob_ad = nominee_dob_ad_parsed

    submission.nominee_contact = request.POST.get("nominee_contact") or ""
    submission.guardian_name = request.POST.get("guardian_name") or None
    submission.guardian_relation = request.POST.get("guardian_relation") or None

    # ----------------------------------------------------
    # AML / PEP
    # ----------------------------------------------------
    submission.is_pep = request.POST.get("is_pep") == "yes"
    submission.is_aml = request.POST.get("is_aml") == "yes"

    submission.submitted_at = timezone.now()
    submission.save()

    # ----------------------------------------------------
    # DOCUMENTS
    # ----------------------------------------------------
    for field, doc_type in DOC_MAP.items():
        file = request.FILES.get(field)
        if file:
            KycDocument.objects.filter(user=user, doc_type=doc_type).delete()
            KycDocument.objects.create(
                user=user,
                doc_type=doc_type,
                file_path=file,
                file_name=file.name,
            )

    for i in range(1, 6):
        file = request.FILES.get(f"additional_doc_{i}")
        name = request.POST.get(f"additional_doc_name_{i}")
        if file:
            KycDocument.objects.create(
                user=user,
                doc_type="ADDITIONAL",
                file_path=file,
                file_name=name or file.name,
            )

    print("========= KYC SUBMISSION COMPLETED =========")
    return user
