# kycform/views.py
"""
Full views.py for KYC form handling.

- Prefill pipeline (kyc_form_view) merges KycUserInfo, KycSubmission, KYCTemporary
  and returns "prefill_json" that the front-end JS expects.
- save_kyc_progress: multipart endpoint -> saves files to MEDIA and stores URLs
  in KYCTemporary.data_json; returns saved file URLs.
- process_kyc_submission: finalizes KYC -> writes KycSubmission, saves files,
  attaches NID as KycDocument (doc_type="NID"), deletes temp draft.
"""

import json
import os
import uuid
import traceback
import urllib.request
import requests

from datetime import datetime, date

from django.conf import settings
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db import transaction, connection
from django.core.files import File
from django.utils.text import get_valid_filename
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.text import get_valid_filename
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from kycform.utils import log_kyc_change
from django.db import models
from django.db import transaction
from django.views.decorators.http import require_POST
from .models import KycMobileOTP
from .utils import hash_otp



from kycform.services.policy_identity import resolve_policy_identity
from django.conf import settings

import logging
from django.apps import apps

from .utils import generate_user_id  # from kycform/utils.py

from .models import (
    KycChangeLog, KycUserInfo, KycAgentInfo, KycPolicy, KycAdmin,
    KycSubmission, KycDocument, KYCTemporary
)
from .storage_utils import save_uploaded_file_to_storage 


FASTAPI_BASE = "http://127.0.0.1:9000"   # your FastAPI server
API_USER = "rjbcl_api"
API_PASS = "your_api_password"   # stored in .env ideally

IGNORED_USER_AUDIT_FIELDS = {
    "submitted_at",
    "version",
    "data_json",
    "additional_docs",
}

# --------------------------------------------------
# Fields that must NEVER be auto-populated by loops
# --------------------------------------------------
EXCLUDED_FIELDS = {
    "id",
    "user",
    "submitted_at",
    "version",
    "is_lock",
}


def get_fastapi_token():
    url = f"{FASTAPI_BASE}/auth/login"
    resp = requests.post(url, json={"username": API_USER, "password": API_PASS})
    resp.raise_for_status()
    return resp.json()["access_token"]

# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------
MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB default per-file check

def resolve_session_policy_no(request):
    """
    Returns the authoritative policy number from session.
    Never trust GET/POST for authorization.
    """
    if request.session.get("authenticated"):
        return request.session.get("policy_no")

    if request.session.get("kyc_access_mode") == "DIRECT_KYC":
        return request.session.get("kyc_policy_no")

    return None

def normalize_status(value):
    """Normalize KYC status."""
    if not value:
        return ""
    return str(value).strip().upper().replace(" ", "_")


def redirect_login_tab(user_type):
    """Return to login tab."""
    return redirect(f"/auth/{user_type}/?tab={user_type}")


def missing_fields(*fields):
    """Check if required fields are missing."""
    return not all(fields)


def safe_model_dict(obj):
    """Convert model_to_dict values, casting date/datetime to isoformat strings."""
    safe = {}
    for k, v in obj.items():
        if isinstance(v, (date, datetime)):
            safe[k] = v.isoformat()
        else:
            safe[k] = v
    return safe


def save_uploaded_file_to_storage(file_obj, dest_folder):
    """
    Save uploaded file_obj to default_storage under dest_folder and
    return (saved_path, url). Raises ValidationError if too large.
    """
    if not file_obj:
        return None, None

    if file_obj.size > MAX_UPLOAD_BYTES:
        raise ValidationError(f"{file_obj.name} too large (>{MAX_UPLOAD_BYTES} bytes).")

    safe_name = get_valid_filename(file_obj.name)
    # Ensure unique filename (timestamp prefix)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    filename = f"{timestamp}_{safe_name}"
    rel_path = os.path.join(dest_folder, filename)
    saved_path = default_storage.save(rel_path, file_obj)
    try:
        url = default_storage.url(saved_path)
    except Exception:
        # Fallback build
        url = os.path.join(settings.MEDIA_URL.rstrip("/"), saved_path)
    return saved_path, url


def download_url_to_filefield(instance, file_field_name, url):
    """
    Download the file at `url` and save into instance.<file_field_name> (FileField).
    Works with local or remote urls; ignores failures (safe).
    """
    if not url:
        return False
    try:
        resp = urllib.request.urlopen(url)
        data = resp.read()
        fname = url.split("/")[-1] or f"file_{datetime.utcnow().timestamp()}"
        content = ContentFile(data)
        # use save(False) to avoid immediate DB write
        getattr(instance, file_field_name).save(fname, content, save=False)
        return True
    except Exception:
        return False


# -----------------------------------------------------------------------------
# AUTHENTICATION: Policyholder & Agent
# -----------------------------------------------------------------------------

def policyholder_login(request):
    if request.method == "GET":
        return render(request, "kyc_auth.html", {"active_tab": "policy"})

    policy_no = request.POST.get("policy_no")
    password = request.POST.get("password")

    if missing_fields(policy_no, password):
        messages.error(request, "Policy number and password are required.")
        return redirect_login_tab("policy")

    # --------------------------------------
    # Validate policy + user
    # --------------------------------------
    try:
        policy = KycPolicy.objects.get(policy_number__iexact=policy_no)
        user = KycUserInfo.objects.get(user_id=policy.user_id)
    except Exception:
        messages.error(request, "Invalid policy number or user not found.")
        return redirect_login_tab("policy")

    # --------------------------------------
    # Check if password is even set (user registered or not)
    # --------------------------------------
    if not user.password or user.password.strip() == "":
        messages.error(request, "You are not registered. Please create an account.")
        return redirect_login_tab("policy")

    # --------------------------------------
    # Validate password using Django hashing
    # --------------------------------------
    if not check_password(password, user.password):
        messages.error(request, "Incorrect password!")
        return redirect_login_tab("policy")
    # SUCCESSFUL LOGIN → SET SESSION
    request.session.flush()          # prevent cross-flow contamination
    request.session["authenticated"] = True
    request.session["policy_no"] = policy_no
    # --------------------------------------
    # KYC routing logic remains same
    # --------------------------------------
    kyc_status = normalize_status(user.kyc_status)

    if kyc_status in ["NOT_INITIATED", "INCOMPLETE", "REJECTED", ""]:
        return redirect(f"/kyc-form/?policy_no={policy_no}")

    if kyc_status in ["PENDING", "VERIFIED"]:
        return redirect(f"/dashboard/?policy_no={policy_no}")

    return redirect(f"/kyc-form/?policy_no={policy_no}")

def agent_login(request):
    if request.method == "GET":
        return render(request, "kyc_auth.html", {"active_tab": "agent"})

    agent_code = request.POST.get("agent_code")
    password = request.POST.get("password")

    if missing_fields(agent_code, password):
        messages.error(request, "Agent code and password are required.")
        return redirect_login_tab("agent")

    try:
        agent = KycAgentInfo.objects.get(agent_code__iexact=agent_code)
    except Exception:
        messages.error(request, "Agent code not found!")
        return redirect_login_tab("agent")

    if password != (agent.password or ""):
        messages.error(request, "Incorrect password!")
        return redirect_login_tab("agent")

    return redirect(f"/agent-dashboard/?agent_code={agent_code}")


# -----------------------------------------------------------------------------
# Simple render views
# -----------------------------------------------------------------------------
def dashboard_view(request):

    if request.session.get("kyc_access_mode") == "DIRECT_KYC":
        return HttpResponse("Unauthorized dashboard access", status=403)

    # ✅ Only policy-login users allowed
    if not request.session.get("authenticated"):
        return redirect("/auth/policy/?tab=policy")

    policy_no = request.session.get("policy_no")
    if not policy_no:
        return redirect("/auth/policy/?tab=policy")

    try:
        policy = KycPolicy.objects.get(policy_number=policy_no)
        user = KycUserInfo.objects.get(user_id=policy.user_id)
    except Exception:
        return redirect("/auth/policy/?tab=policy")

    # 🔒 KYC submitted → dashboard is final
    if user.kyc_status in ["PENDING", "VERIFIED"]:
        return render(request, "dashboard.html", {
            "policy_no": policy_no,
            "user": user,
        })
    # Editable states → form
    return redirect("/kyc-form/")

    # ✅ PENDING / VERIFIED → dashboard
    return render(request, "dashboard.html", {
        "policy_no": policy_no,
        "user": user,
    })


def agent_dashboard_view(request):
    return render(request, "dashboard.html", {
        "agent_code": request.GET.get("agent_code")
    })


# -----------------------------------------------------------------------------
# Registration / Forgot / Reset
# -----------------------------------------------------------------------------

import logging
logger = logging.getLogger(__name__)


def policyholder_register_view(request):
    """Registration logic using tblinsureddetail (dummy core) and
       deterministic hashed user_id generation.
    """
    if request.method == "GET":
        return render(request, "register.html")

    # ----------------------------------------------------------
    # 1) COLLECT INPUTS
    # ----------------------------------------------------------
    policy_no = (request.POST.get("policy_number") or "").strip()
    mobile = (request.POST.get("mobile") or "").strip()
    dob_ad = (request.POST.get("dob_ad") or "").strip()   # YYYY-MM-DD
    first_name = (request.POST.get("first_name") or "").strip()
    last_name = (request.POST.get("last_name") or "").strip()

    # Your form does not collect email (None for now)
    email = None

    if not (policy_no and mobile and dob_ad and first_name and last_name):
        messages.error(request, "All fields are required.", extra_tags="error")
        return redirect("kyc:policy_register")

    # ----------------------------------------------------------
    # 2) FAST PATH: CHECK LOCAL KycPolicy TABLE
    # ----------------------------------------------------------
    kp = KycPolicy.objects.filter(policy_number__iexact=policy_no).first()

    if kp and kp.user_id:
        messages.error(
            request, "This policy is already registered. Please login.",
            extra_tags="error"
        )
        return redirect_login_tab("policy")

   # ----------------------------------------------------------
   # 3) LOOKUP IN CORE VIA FASTAPI (secure + centralized)
   # ----------------------------------------------------------
    try:
        api_url = f"{settings.API_BASE_URL}/mssql/newpolicies"
        headers = {"Authorization": f"Bearer {settings.API_TOKEN}"}

        response = requests.get(api_url, params={
            "policy_no": policy_no,
            "dob": dob_ad
        }, headers=headers)

        if response.status_code == 404:
            messages.error(request, "Policy not found in core system.", extra_tags="error")
            return redirect("kyc:policy_register")

        if response.status_code != 200:
            messages.error(request, "Server error during policy lookup.", extra_tags="error")
            return redirect("kyc:policy_register")
        # API returns a list → extract first item
        data = response.json()[0]

        # Match keys returned by FastAPI
        core_policy_no = data["PolicyNo"]
        core_first = data["FirstName"]
        core_last = data["LastName"]
        core_dob = data["DOB"]
        core_mobile = data["Mobile"]
    except Exception as e:
        print("API LOOKUP ERROR:", e)
        messages.error(request, "Could not connect to policy lookup API.")
        return redirect("kyc:policy_register")


    # ----------------------------------------------------------
    # 4) VALIDATE DOB + MOBILE
    # ----------------------------------------------------------
    if str(core_dob) != str(dob_ad):
        messages.error(request, "DOB does not match our records.", extra_tags="error")
        return redirect("kyc:policy_register")

    if str(core_mobile).strip() != mobile.strip():
        messages.error(request, "Mobile number does not match our records.", extra_tags="error")
        return redirect("kyc:policy_register")

    # ----------------------------------------------------------
    # 5) FIND ALL RELATED POLICIES FROM MSSQL (via FastAPI)
    # ----------------------------------------------------------
    try:
        api_url = f"{settings.API_BASE_URL}/mssql/related-policies"
        headers = {"Authorization": f"Bearer {settings.API_TOKEN}"}

        resp = requests.get(api_url, params={
            "firstname": core_first,
            "lastname": core_last,
            "dob": core_dob,
            "mobile": core_mobile
        }, headers=headers)

        resp.raise_for_status()
        related = resp.json()

    except Exception as e:
        print("RELATED POLICY LOOKUP ERROR:", e)
        messages.error(request, "Could not fetch related policies.", extra_tags="error")
        return redirect("kyc:policy_register")

    related_policy_numbers = set(related)
    related_policy_numbers.add(policy_no)


    # ----------------------------------------------------------
    # 6) CHECK IF ANY OF THESE POLICIES ALREADY HAVE user_id
    # ----------------------------------------------------------
    existing = (
        KycPolicy.objects
        .filter(policy_number__in=list(related_policy_numbers), user_id__isnull=False)
        .exclude(user_id="")
        .first()
    )

    if existing:
        user_id = existing.user_id
    else:
        # ---- Option A: Deterministic hash ID ----
        user_id = generate_user_id(core_first, core_last, core_dob, core_mobile)

    # ----------------------------------------------------------
    # 7) CREATE / UPDATE KycUserInfo
    # ----------------------------------------------------------
    try:
        with transaction.atomic():

            user_obj, created = KycUserInfo.objects.get_or_create(
                user_id=user_id,
                defaults={
                    "first_name": first_name or core_first,
                    "last_name": last_name or core_last,
                    "dob": core_dob,
                    "email": email,
                    "phone_number": mobile,
                }
            )

            if not created:
                # check consistent mobile
                if user_obj.phone_number and user_obj.phone_number != mobile:
                    messages.error(request, "Mobile does not match existing account.", extra_tags="error")
                    raise ValueError("mobile mismatch")

                updated = False
                if not user_obj.first_name:
                    user_obj.first_name = first_name or core_first; updated = True
                if not user_obj.last_name:
                    user_obj.last_name = last_name or core_last; updated = True
                if not user_obj.phone_number:
                    user_obj.phone_number = mobile; updated = True

                if updated:
                    user_obj.save()

            # ------------------------------------------------------
            # 8) ASSIGN SAME user_id TO ALL RELATED POLICIES
            # ------------------------------------------------------
            for pn in related_policy_numbers:
                loc = KycPolicy.objects.filter(policy_number__iexact=pn).first()
                if loc:
                    if loc.user_id != user_id:
                        loc.user_id = user_id
                        loc.save()
                else:
                    # create new entry if policy wasn't present
                    KycPolicy.objects.create(
                        policy_number=pn,
                        user_id=user_id,
                        created_at=timezone.now().date()
                    )

            # ------------------------------------------------------
            # 9) SET PASSWORD = DOB (YYYYMMDD) — NOW HASHED SECURELY
            # ------------------------------------------------------
            if not user_obj.password:
                raw_default = str(core_dob).replace("-", "")  # 19800120
                user_obj.password = make_password(raw_default)
                user_obj.save()

    except ValueError:
        return redirect("kyc:policy_register")
    except Exception as e:
        logger.exception("Registration error: %s", e)
        messages.error(request, "Server error during registration.", extra_tags="error")
        return redirect("kyc:policy_register")

    # ----------------------------------------------------------
    # SUCCESS
    # ----------------------------------------------------------
    messages.success(
        request,
        "Registration successful. Please login. Password = DOB (YYYYMMDD).",
        extra_tags="success"
    )
    return redirect_login_tab("policy")

def agent_register_view(request):
    messages.error(request, "Agent registration not implemented.", extra_tags="error")
    return redirect("kyc:policy_register")

def forgot_password(request):
    user_type = request.GET.get("type", "policy")

    if request.method == "GET":
        return render(request, "forgot_password.html", {"user_type": user_type})

    identifier = request.POST.get("identifier")
    dob = request.POST.get("dob")

    if missing_fields(identifier, dob):
        messages.error(request, "All fields are required.", extra_tags="error")
        return redirect(f"/forgot-password/?type={user_type}")

    try:
        # --------------------------------------
        # Identify user (policyholder or agent)
        # --------------------------------------
        if user_type == "agent":
            user = KycAgentInfo.objects.get(agent_code__iexact=identifier)
        else:
            policy = KycPolicy.objects.get(policy_number__iexact=identifier)
            user = KycUserInfo.objects.get(user_id=policy.user_id)

        # --------------------------------------
        # If no password yet → user never registered
        # (make_password() ALWAYS returns a non-empty string)
        # --------------------------------------
        if not user.password or user.password.strip() == "":
            messages.error(request, "You are not registered.", extra_tags="error")
            return redirect_login_tab(user_type)

        # --------------------------------------
        # Validate DOB
        # --------------------------------------
        if str(user.dob) != dob:
            messages.error(request, "DOB does not match!", extra_tags="error")
            return redirect(f"/forgot-password/?type={user_type}")

        # --------------------------------------
        # Proceed to reset password page
        # --------------------------------------
        return redirect(f"/reset-password/?type={user_type}&identifier={identifier}")

    except Exception as e:
        print("FORGOT ERROR:", e)
        messages.error(request, "Record not found!", extra_tags="error")
        return redirect(f"/forgot-password/?type={user_type}")


def reset_password(request):
    user_type = request.GET.get("type", "policy")
    identifier = request.GET.get("identifier")

    if request.method == "GET":
        return render(
            request,
            "reset_password.html",
            {"user_type": user_type, "identifier": identifier}
        )

    # POST request
    new_pass = request.POST.get("new_password")
    confirm = request.POST.get("confirm_password")
    identifier = request.POST.get("identifier") or identifier

    if missing_fields(new_pass, confirm, identifier):
        messages.error(request, "All fields are required.", extra_tags="error")
        return redirect(f"/reset-password/?type={user_type}&identifier={identifier}")

    if new_pass != confirm:
        messages.error(request, "Passwords do not match!", extra_tags="error")
        return redirect(f"/reset-password/?type={user_type}&identifier={identifier}")

    try:
        # Resolve USER based on type
        if user_type == "agent":
            user = KycAgentInfo.objects.get(agent_code__iexact=identifier)
        else:
            policy = KycPolicy.objects.get(policy_number__iexact=identifier)
            user = KycUserInfo.objects.get(user_id=policy.user_id)

        # ---------------------------
        # SECURE PASSWORD HASHING
        # ---------------------------
        user.password = make_password(new_pass)
        user.save()

        messages.success(request, "Password updated successfully!", extra_tags="success")
        return redirect_login_tab(user_type)

    except Exception as e:
        print("RESET ERROR:", e)
        messages.error(request, "Something went wrong!", extra_tags="error")
        return redirect(f"/reset-password/?type={user_type}&identifier={identifier}")
# -----------------------------------------------------------------------------
# KYC Form view (prefill) — single endpoint returning the template + prefill JSON
# -----------------------------------------------------------------------------

from django.core.cache import cache

@csrf_exempt
@never_cache
def kyc_form_view(request):
    # -------------------------
    # CHECK FOR ONE-TIME TOKEN (for React login redirect)
    # -------------------------
    token = request.GET.get('token')
    if token:
        token_data = cache.get(f'login_token_{token}')
        if token_data:
            # Set session from token
            request.session['authenticated'] = token_data['authenticated']
            request.session['policy_no'] = token_data['policy_no']
            request.session.save()
            
            # Delete the token (one-time use)
            cache.delete(f'login_token_{token}')
            
            # Redirect without token to clean URL
            policy_no = token_data['policy_no']
            return redirect(f"/kyc-form/?policy_no={policy_no}")
    # -------------------------
    # AUTH & POLICY RESOLUTION
    # -------------------------
    is_login_flow = request.session.get("authenticated") is True
    is_direct_kyc = request.session.get("kyc_access_mode") == "DIRECT_KYC"

    if is_login_flow:
        policy_no = request.session.get("policy_no")

    elif is_direct_kyc:
        policy_no = request.session.get("kyc_policy_no")

    else:
        return redirect("/auth/policy/?tab=policy")

    if not policy_no:
        return HttpResponse("Unauthorized access", status=403)

    # -------------------------
    # POLICY OWNERSHIP CHECK
    # -------------------------
    try:
        policy = KycPolicy.objects.get(policy_number=policy_no)
        user = KycUserInfo.objects.get(user_id=policy.user_id)
    except KycPolicy.DoesNotExist:
        return HttpResponse("Invalid policy", status=403)
    except KycUserInfo.DoesNotExist:
        return HttpResponse("Invalid user", status=403)
    # -------------------------
    # MOBILE OTP STATE (DB → SESSION → TEMPLATE)
    # -------------------------
    mobile_otp_verified = False

    if hasattr(user, "mobile_verified"):
        mobile_otp_verified = bool(user.mobile_verified)

    # keep session in sync (helper only)
    request.session["mobile_otp_verified"] = mobile_otp_verified

    # 🔒 Direct KYC policy binding check
    if request.session.get("kyc_access_mode") == "DIRECT_KYC":
        if request.session.get("kyc_policy_no") != policy.policy_number:
            return HttpResponse("Unauthorized access", status=403)

    # -------------------------
    # STOP ACCESS AFTER SUBMIT
    # -------------------------
    if user.kyc_status in ["PENDING", "VERIFIED"]:

        # 🚫 Direct KYC must NOT see dashboard
        if request.session.get("kyc_access_mode") == "DIRECT_KYC":
            return HttpResponse(
                "KYC already submitted. Please contact your branch.",
                status=403
            )
        # ✅ Normal login → dashboard
        return redirect(f"/dashboard/?policy_no={policy_no}")


    # ---------------------------------
    # REJECTION MESSAGE FOR FRONTEND
    # ---------------------------------
    rejection_message = None
    if user.kyc_status in ["REJECTED", "INCOMPLETE"]:
        try:
            sub = KycSubmission.objects.get(user=user)
            rejection_message = sub.rejection_comment or "Your KYC was rejected. Please review and resubmit."
        except KycSubmission.DoesNotExist:
            rejection_message = "Your KYC was rejected. Please review and resubmit."

    # ---------------------------------
    # LOAD THREE SOURCES
    # ---------------------------------
    user_info = safe_model_dict(model_to_dict(user, exclude=["password"]))

    try:
        submission = KycSubmission.objects.get(user=user)
        submission_data = safe_model_dict(
            model_to_dict(submission, exclude=["id", "user", "submitted_at"])
        )
    except KycSubmission.DoesNotExist:
        submission = None
        submission_data = {}
    
    # ---------------------------------
    # LOAD ADDITIONAL DOCUMENTS (DB SOURCE OF TRUTH)
    # ---------------------------------
    if submission:
        additional_docs = KycDocument.objects.filter(
            user=user,
            submission=submission,
            doc_type="ADDITIONAL",
            is_current=True
        ).order_by("uploaded_at")
    else:
        additional_docs = []

    try:
        temp = KYCTemporary.objects.get(user=user)
        temp_data = safe_model_dict(temp.data_json)
    except KYCTemporary.DoesNotExist:
        temp_data = {}

    # ---------------------------------
    # MERGE PRIORITY (temp > submission > user)
    # ---------------------------------
    merged = user_info.copy()

    # apply submission second
    for k, v in submission_data.items():
        if v not in [None, "", [], {}]:
            merged[k] = v

    # apply temp highest priority
    for k, v in temp_data.items():
        if v not in [None, "", [], {}]:
            merged[k] = v

    # SAFE Fix: do NOT read marital_status from user (it doesn't exist in model)
    # Only temp > submission determines marital_status
    if merged.get("marital_status") in [None, "", "null", "None"]:
        merged["marital_status"] = None


    # ---------------------------------
    # START FINAL PREFILL OUTPUT
    # ---------------------------------
    fixed = {}
    simple_fields = [
        "salutation", "first_name", "middle_name", "last_name", "full_name_nep",
        "email", "mobile", "gender", "nationality", "marital_status",
        "dob_ad", "dob_bs", "dob_bs_auto",

        "spouse_name", "father_name", "mother_name", "grand_father_name",
        "father_in_law_name", "son_name", "daughter_name", "daughter_in_law_name",

        "citizenship_no", "citizen_bs", "citizen_ad", "citizenship_place",
        "passport_no", "nid_no",

        "perm_province", "perm_district", "perm_municipality", "perm_ward",
        "perm_address", "perm_house_number",

        "temp_province", "temp_district", "temp_municipality", "temp_ward",
        "temp_address", "temp_house_number",

        "bank_name", "bank_branch", "account_number", "account_type", "branch_name",

        "occupation", "occupation_description", "income_mode", "annual_income",
        "income_source", "pan_number", "qualification", "employer_name", "office_address",

        "nominee_name", "nominee_relation", "nominee_dob_ad", "nominee_dob_bs",
        "nominee_contact", "guardian_name", "guardian_relation",

        "is_pep", "is_aml", "_current_step"
    ]

    # Apply fields
    for f in simple_fields:
        fixed[f] = merged.get(f)

    # ---------------------------------
    # FINAL CLEAN NORMALIZATION OF marital_status
    # ---------------------------------
    ms = merged.get("marital_status")

    if ms:
        s = str(ms).strip().lower()
        if s in ["married", "m", "1", "yes", "true", "विवाहित"]:
            fixed["marital_status"] = "Married"
        elif s in ["unmarried", "single", "u", "0", "no", "false", "अविवाहित"]:
            fixed["marital_status"] = "Unmarried"
        else:
            fixed["marital_status"] = None
    else:
        fixed["marital_status"] = None

    # ---------------------------------
    # FILE URL MAPPING
    # ---------------------------------
    if submission:
        fixed["photo_url"] = submission.photo.url if submission.photo else None
        fixed["citizenship_front_url"] = submission.citizenship_front.url if submission.citizenship_front else None
        fixed["citizenship_back_url"] = submission.citizenship_back.url if submission.citizenship_back else None
        fixed["signature_url"] = submission.signature.url if submission.signature else None
        fixed["passport_doc_url"] = submission.passport_doc.url if submission.passport_doc else None
        fixed["nid_url"] = merged.get("nid_url")
    else:
        fixed["photo_url"] = None
        fixed["citizenship_front_url"] = None
        fixed["citizenship_back_url"] = None
        fixed["signature_url"] = None
        fixed["passport_doc_url"] = None
        fixed["nid_url"] = merged.get("nid_url")

    # ---------------------------------
    # LOCK CHECK
    # ---------------------------------
    if submission and submission.is_lock and not request.user.is_superuser:
        messages.error(request, "This KYC is locked after verification. Only super admin can modify.")
        return redirect(f"/dashboard/?policy_no={policy_no}")

    # ---------------------------------
    # SEND DATA TO FRONTEND
    # ---------------------------------
    prefill_json = json.dumps(fixed, ensure_ascii=False)

    # Build full name from user info
    full_name_parts = [user.first_name]
    if user.middle_name:
        full_name_parts.append(user.middle_name)
    full_name_parts.append(user.last_name)
    full_name = " ".join(full_name_parts)

    return render(request, "kyc_form_update.html", {
        "policy_no": policy_no,
        "prefill_json": prefill_json,
        "rejection_message": rejection_message,
        "additional_docs": additional_docs, 
        "user_name": full_name,  # Changed from "Test Name" to actual full name
        "mobile_otp_verified": request.session.get("mobile_otp_verified", False),
    })


# -----------------------------------------------------------------------------
# Final submission handler (exposed for form POST)
# -----------------------------------------------------------------------------
@csrf_exempt
def kyc_form_submit(request):
    print(">>> ENTERED kyc_form_submit <<<")

    print("SUBMIT SESSION:", dict(request.session))
    print("POST policy_no:", request.POST.get("policy_no"))


    if request.method != "POST":
        messages.error(request, "Invalid request method!")
        return redirect("/")

      # 🔐 OTP LOCK
    if not request.session.get("mobile_otp_verified"):

        # Message for popup
        messages.error(
            request,
            "Please verify your mobile number using OTP before submitting the KYC form."
        )

        # Flag so frontend knows OTP is required (optional but useful)
        request.session["otp_required"] = True

        return redirect("/kyc-form/")
    # -------------------------
    # AUTH CHECK (LOGIN + DIRECT KYC)
    # -------------------------
    is_login_flow = request.session.get("authenticated") is True

    is_direct_kyc = (
        request.session.get("kyc_access_mode") == "DIRECT_KYC"
        and request.session.get("kyc_user_id")
        and request.session.get("kyc_policy_no")
    )

    if not (is_login_flow or is_direct_kyc):
        return HttpResponseForbidden("Unauthorized access")


    # Resolve policy_no
    if is_login_flow:
        policy_no = request.session.get("policy_no")

    else:
        policy_no = request.session.get("kyc_policy_no")

    if not policy_no:
        messages.error(request, "Missing policy number.")
        return redirect("/")

    # ... (unchanged logic above)

    # POLICY BINDING CHECK (DIRECT KYC ONLY)
    if request.session.get("kyc_access_mode") == "DIRECT_KYC":
        session_policy = request.session.get("kyc_policy_no")
        if session_policy != policy_no:
            return HttpResponse("Unauthorized access", status=403)

    try:
        process_kyc_submission(request)
        # 🔒 Clear OTP verification after successful submission
        request.session.pop("mobile_otp_verified", None)

        messages.success(request, "Your KYC form has been successfully submitted.")

        # -------------------------
        # REDIRECT BASED ON ACCESS MODE
        # -------------------------
        if request.session.get("authenticated"):
            return redirect("/dashboard/")

        if request.session.get("kyc_access_mode") == "DIRECT_KYC":
            request.session.flush()
            return redirect("/kyc-submitted/")

        return redirect("/")

    except Exception as e:
        traceback.print_exc()
        messages.error(request, f"KYC submission failed: {e}")

        if request.session.get("authenticated"):
            return redirect(f"/dashboard/?policy_no={policy_no}")


        return redirect(f"/kyc-form/?policy_no={policy_no}")

    # ------------------------------------------------------------------
    # Helper: save files and create KycDocument audit rows (single source)
    # ------------------------------------------------------------------

# Adjust these according to policy/regulator requirements
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "application/pdf"}

def _validate_uploaded_file(uploaded_file):
    """
    Raise ValidationError if the file is not allowed.
    Checks content_type and extension and size.
    """
    # size
    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"File too large: {uploaded_file.size} bytes (max {MAX_FILE_SIZE_BYTES})")

    # content type
    ctype = getattr(uploaded_file, "content_type", None)
    if ctype and ctype not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(f"Disallowed content type: {ctype}")

    # extension
    __, ext = os.path.splitext(uploaded_file.name or "")
    ext = ext.lower()

    # Treat .jfif as .jpeg
    if ext == ".jfif":
        ext = ".jpeg"

    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Disallowed file extension: {ext}")

def _safe_uuid_filename(original_name):
    """
    Build a sanitized filename: <uuid4><ext>
    Keeps extension for content-type mapping.
    """
    _, ext = os.path.splitext(original_name or "")
    ext = ext.lower()
    return f"{uuid.uuid4().hex}{ext or ''}"

@transaction.atomic
def _save_files_and_submission(request, user, submission=None, actor=None):
    """
    Save uploaded files to disk (via FileField.save), create KycDocument audit rows,
    maintain submission.additional_docs JSON, and return (submission, urls, additional_struct).

    actor: optional dict or string to include in metadata (e.g., {"actor":"agent","id":...}) for audit logs.
    """
    print("DEBUG additional_docs LIST =", request.FILES.getlist("additional_docs"))

    if not submission:
        submission, _ = KycSubmission.objects.get_or_create(user=user)

    # Prepare return structures
    urls = {}

    # mapping: form-field-name -> (submission_attr_name, doc_type, url_key)
    single_file_map = {
        "photo": ("photo", "PHOTO", "photo_url"),
        "citizenship-front": ("citizenship_front", "CITIZENSHIP_FRONT", "citizenship_front_url"),
        "citizenship-back": ("citizenship_back", "CITIZENSHIP_BACK", "citizenship_back_url"),
        "signature": ("signature", "SIGNATURE", "signature_url"),
        "nid": ("nid_file", "NID", "nid_url"),
    }

    existing_additional_docs = KycDocument.objects.filter(
    user=user,
        submission=submission,
        doc_type="ADDITIONAL",
        is_current=True
    ).order_by("uploaded_at")
    additional_struct = [
        {
            "doc_id": d.id,
            "file_name": d.file_name,
            "file_url": d.file.url if d.file else None,
            "display_name": (d.metadata or {}).get("display_name", ""),
            "type": "ADDITIONAL",
            "is_current": d.is_current,
        }
        for d in existing_additional_docs
    ]


    # Helper to persist file into a KycDocument and link to submission
    def _create_kyc_document(uploaded_file, doc_type, submission, user, original_filename):
        """
        Validates, saves file to storage using FileField.save(), creates KycDocument row,
        returns doc instance (saved).
        """

        # Validate file
        _validate_uploaded_file(uploaded_file)

        # Build safe filename
        safe_name = _safe_uuid_filename(original_filename)

        # Create KycDocument instance without file so we can call file.save() correctly
        doc = KycDocument(
            user=user,
            submission=submission,
            doc_type=doc_type,
            file_name=get_valid_filename(original_filename),
            metadata={"ingested_at": timezone.now().isoformat()}
        )
        # Save object to get an id (optional but helpful for metadata)
        doc.save()

        # Save file into the FileField using Django storage & upload_to rules
        # Use uploaded_file (UploadedFile) directly; FileField.save handles backend naming & storage
        doc.file.save(safe_name, uploaded_file, save=True)

        # Ensure this doc is current and mark others of same type as non-current
        if doc_type != "ADDITIONAL":
            KycDocument.objects.filter(
                user=user,
                doc_type=doc_type,
                is_current=True
            ).exclude(id=doc.id).update(is_current=False)
            
        # attach audit metadata (who/when)
        meta = doc.metadata or {}
        meta.update({
            "uploaded_by": actor or getattr(user, "user_id", str(user)),
            "uploaded_at": timezone.now().isoformat()
        })
        doc.metadata = meta
        doc.save(update_fields=["metadata"])

        return doc

    # -------------------------
    # Single-file fields loop
    # -------------------------
    for form_field, (sub_field, doc_type, url_key) in single_file_map.items():
        f = request.FILES.get(form_field)
        if not f:
            # expose existing url if present on submission
            existing_file = getattr(submission, sub_field, None)
            try:
                if existing_file and getattr(existing_file, "url", None):
                    urls[url_key] = existing_file.url
            except Exception:
                # ignore storage errors
                urls[url_key] = None
            continue

        # Validate, save into submission FileField using .save() so upload_to applies
        try:
            _validate_uploaded_file(f)
        except ValidationError as e:
            # Re-raise or attach to submission errors depending on your error handling pattern
            raise

        # sanitize original name for file_name field
        original_filename = get_valid_filename(f.name)
        safe_name = _safe_uuid_filename(original_filename)

        # Save to submission FileField (ensures consistent storage path)
        # We call save(False) first to set the field on the submission instance
        getattr(submission, sub_field).save(safe_name, f, save=False)

        # 🔐 USER FILE CHANGE AUDIT
        log_kyc_change(
        submission=submission,
        action="DOCUMENT_CHANGE",
        actor_type="USER",
        actor_identifier=user.user_id,
        field_name=sub_field,
        old_value="",
        new_value=f.name,
        )


        # Create KycDocument audit row using the file saved on submission's FileField
        # Note: Many storages require that the file is saved on the model instance itself.
        # To ensure consistency, flush submission so the file exists in storage and url is available.
        submission.save(update_fields=[sub_field])  # persist the file to storage

        # Now create audit doc by opening the file from submission field
        # Re-open using storage to get a File object
        saved_file_field = getattr(submission, sub_field)
        # saved_file_field is a FieldFile instance; pass it into doc.file.save() via File wrapper or use existing file
        # We'll create doc and then copy file from saved_file_field to preserve storage path
        # Easiest: instantiate a File wrapper around storage.open() (works for default storages)
        try:
            with saved_file_field.open("rb") as fh:
                django_file = File(fh, name=os.path.basename(saved_file_field.name))
                doc = KycDocument.objects.create(
                    user=user,
                    submission=submission,
                    doc_type=doc_type,
                    file_name=original_filename
                )
                # save file into doc.file (this will copy or reference depending on storage backend)
                doc.file.save(django_file.name, django_file, save=True)
        except Exception:
            # Fallback: if storage doesn't allow open, create doc and point file to same name (may depend on storage)
            doc = KycDocument.objects.create(
                user=user,
                submission=submission,
                doc_type=doc_type,
                file_name=original_filename,
                file=saved_file_field  # FieldFile should be assignable in many cases
            )
            doc.save()

        # Mark previous docs of same type as non-current
        if doc_type != "ADDITIONAL":
            KycDocument.objects.filter(
                user=user,
                doc_type=doc_type,
                is_current=True
            ).exclude(id=doc.id).update(is_current=False)
        doc.is_current = True
        doc.metadata = (doc.metadata or {})
        doc.metadata.update({"linked_to_submission": submission.id, "linked_at": timezone.now().isoformat(), "uploaded_by": actor or getattr(user, "user_id", str(user))})
        doc.save(update_fields=["is_current", "metadata"])

        # build url (now available)
        urls[url_key] = getattr(doc.file, "url", None)

        # Update additional_struct for UI: remove any existing entry for same field and append new
        entry = {
            "doc_id": doc.id,
            "file_name": doc.file_name,
            "file_url": getattr(doc.file, "url", None),
            "type": doc_type,
            "field": form_field,
            "is_current": doc.is_current,
        }
        additional_struct = [d for d in additional_struct if d.get("field") != form_field]
        additional_struct.append(entry)

    # -------------------------
    # Multi-file additional_docs (REPLACE-ALL LOGIC)
    # -------------------------
    multi_files = request.FILES.getlist("additional_docs")
    doc_names = request.POST.getlist("additional_doc_names[]")

    if multi_files:
        # 🔴 HARD GUARANTEE: deactivate ALL previous additional docs
        KycDocument.objects.filter(
            user=user,
            submission=submission,
            doc_type="ADDITIONAL",
                is_current=True
        ).update(is_current=False)

    for idx, uploaded in enumerate(multi_files):
        try:
            doc = _create_kyc_document(
                uploaded,
                "ADDITIONAL",
                submission,
                user,
                original_filename=uploaded.name
            )
        except ValidationError:
            raise

        display_name = ""
        if idx < len(doc_names):
            display_name = doc_names[idx].strip()

        if display_name:
            meta = doc.metadata or {}
            meta["display_name"] = display_name
            doc.metadata = meta
            doc.save(update_fields=["metadata"])

        # ✅ AUDIT LOG — ADD / REUPLOAD DOCUMENT
        log_kyc_change(
            submission=submission,
            action="DOCUMENT",
            actor_type="USER",
            actor_identifier=user.user_id,
            field_name="additional_document",
            new_value=doc.file_name,
            comment=display_name or None,
        )
        additional_struct.append({
            "doc_id": doc.id,
            "file_name": doc.file_name,
            "file_url": getattr(doc.file, "url", None),
            "display_name": display_name,
            "type": "ADDITIONAL",
            "is_current": True,
        })


    # -------------------------
    # Handle removal of additional docs (frontend posted remove_additional_doc_ids)
    # -------------------------
    remove_ids = request.POST.getlist("remove_additional_doc_ids")
    if remove_ids:
        # convert to ints safely
        try:
            remove_ids_int = [int(x) for x in remove_ids]
        except ValueError:
            remove_ids_int = []

        # For audit & compliance we prefer to unlink from submission and mark not-current,
        # instead of hard-deleting rows and media files. If policy requires actual deletion,
        # swap the update() to delete() and also remove storage files.
        docs_to_unlink = KycDocument.objects.filter(id__in=remove_ids_int, user=user, submission=submission)
        # record metadata before unlinking
        now_iso = timezone.now().isoformat()
        for d in docs_to_unlink:
             # ✅ AUDIT LOG — DOCUMENT REMOVAL
            log_kyc_change(
                submission=submission,
                action="DOCUMENT",
                actor_type="ADMIN",
                actor_identifier=request.user.username if request.user.is_authenticated else "system",
                field_name="additional_document",
                old_value=d.file_name,
                comment="Document marked inactive / removed",
            )
            meta = d.metadata or {}
            meta.update({"archived_by": actor or getattr(user, "user_id", str(user)), "archived_at": now_iso})
            d.metadata = meta
            d.is_current = False
            d.submission = None  # unlink from submission; FK is SET_NULL on model
            d.save(update_fields=["metadata", "is_current", "submission"])

        # Remove from additional_struct used for UI
        additional_struct = [d for d in additional_struct if str(d.get("doc_id")) not in set(map(str, remove_ids_int))]

    # -------------------------
    # Merge frontend posted additional_docs metadata (if provided)
    # -------------------------
    # posted_additional = request.POST.get("additional_docs")
    # if posted_additional:
    #     try:
    #         posted_list = json.loads(posted_additional)
    #         merged_add = []
    #         for p in posted_list:
    #             match = next((d for d in additional_struct if d.get("file_name") == p.get("file_name") or str(d.get("doc_id")) == str(p.get("doc_id"))), None)
    #             if match:
    #                 match.update(p)
    #                 merged_add.append(match)
    #             else:
    #                 merged_add.append(p)
    #         additional_struct = merged_add
    #     except Exception:
    #         # ignore parse errors
    #         pass

    # Save additional_struct on submission (no file data here, only metadata)
    submission.additional_docs = additional_struct

    # Persist submission (ensure any changes to submission FileFields and additional_docs are saved)
    submission.save()

    # Build guaranteed urls map (recompute to ensure storage url is present)
    for key, val in list(urls.items()):
        if not val:
            # attempt to find doc by type for submission
            mapped = {v[1]: k for k, v in single_file_map.items()}  # doc_type -> form_field
            # not necessary but kept for completeness

    return submission, urls, additional_struct


# ------------------------------------------------------------------
# Main: process_kyc_submission using helper (unified flow)
# ------------------------------------------------------------------
def process_kyc_submission(request):

    # -------------------------
    # AUTH CHECK (LOGIN + DIRECT KYC)
    # -------------------------
    if request.session.get("authenticated") is True:
        policy_no = request.POST.get("policy_no") or request.session.get("policy_no")

    elif request.session.get("kyc_access_mode") == "DIRECT_KYC":
        policy_no = request.session.get("kyc_policy_no")

    else:
        raise Exception("Not authenticated")
    if not policy_no:
        raise Exception("Missing policy number.")

    raw_json = request.POST.get("kyc_data")

    try:
        parsed = json.loads(raw_json) if raw_json else {}
    except Exception:
        parsed = {}
    
    # 🔧 CRITICAL FIX
    if not parsed.get("branch_name"):
        parsed["branch_name"] = request.POST.get("branch_name")

    # Track only user-intended changes
    user_changed_fields = set(parsed.keys())
    if "photo" in request.FILES:
        user_changed_fields.add("photo")

    # Load draft (Save & Continue)
    try:
        temp = KYCTemporary.objects.get(policy_no=policy_no)
        temp_data = temp.data_json or {}
    except KYCTemporary.DoesNotExist:
        temp = None
        temp_data = {}

    # 🔒 REMOVE ALIAS FIELDS FROM TEMP DATA
    temp_data.pop("bank_branch", None)
    temp_data.pop("branch_name", None)

    # Merge priority: temp > parsed
    merged = {**parsed}
    for k, v in temp_data.items():
        if v not in [None, "", [], {}]:
            merged[k] = v

    # --------------------------------------------------
    # ATOMIC BLOCK (THIS IS THE FIX)
    # --------------------------------------------------
    with transaction.atomic():

        # Load user & policy
        try:
            policy = KycPolicy.objects.get(policy_number=policy_no)
            user = KycUserInfo.objects.get(user_id=policy.user_id)
        except Exception:
            raise Exception("User or policy not found.")

        # Load or create submission FIRST
        submission, created = KycSubmission.objects.get_or_create(user=user)
        is_first_submission = created or submission.version == 1


        # -------------------------
        # CAPTURE OLD VALUES (BEFORE CHANGE)
        # -------------------------
        old_values = {}
        for f in submission._meta.fields:
            old_values[f.name] = getattr(submission, f.name)

        # -------------------------
        # Update base user fields
        # -------------------------
        if merged.get("first_name"):
            user.first_name = merged.get("first_name")
        if "middle_name" in parsed:
            user.middle_name = parsed.get("middle_name")
        if merged.get("last_name"):
            user.last_name = merged.get("last_name")
        if merged.get("full_name_nep"):
            user.full_name_nep = merged.get("full_name_nep")
        if merged.get("email"):
            user.email = merged.get("email")
        if merged.get("mobile"):
            user.phone_number = merged.get("mobile")
        if merged.get("dob_ad"):
            try:
                user.dob = datetime.strptime(merged["dob_ad"], "%Y-%m-%d").date()
            except Exception:
                pass

        user.kyc_status = "PENDING"
        user.save()

        # -------------------------
        # Populate submission fields
        # -------------------------
        for field in submission._meta.fields:
            name = field.name

            if name in EXCLUDED_FIELDS:
                continue

            if name in temp_data:
                value = temp_data.get(name)
            elif name in parsed:
                value = parsed.get(name)
            else:
                continue

            if value in [None, "", [], {}]:
                continue

            if isinstance(field, models.DateField):
                try:
                    value = datetime.strptime(value, "%Y-%m-%d").date()
                except Exception:
                    continue

            setattr(submission, name, value)


        # Explicit mapped fields (ONLY current submit)
        mapped_fields = [
            "salutation","first_name","middle_name","last_name","full_name_nep",
            "gender","marital_status","nationality","dob_ad","dob_bs","email","mobile",
            "spouse_name","father_name","mother_name","grand_father_name",
            "father_in_law_name","son_name","daughter_name","daughter_in_law_name",
            "citizenship_no","citizen_bs","citizen_ad","citizenship_place",
            "passport_no","nid_no","perm_province","perm_district","perm_municipality",
            "perm_ward","perm_address","perm_house_number",
            "temp_province","temp_district","temp_municipality","temp_ward","temp_address","temp_house_number",
            "bank_name","account_number","account_type",
            "occupation","occupation_description","income_mode","annual_income","income_source",
            "pan_number","qualification","employer_name","office_address",
            "nominee_name","nominee_relation","nominee_dob_ad","nominee_dob_bs","nominee_contact",
            "guardian_name","guardian_relation",
        ]

        for f in mapped_fields:
            if f in parsed:
                setattr(submission, f, parsed[f])

        # Boolean normalization
        def _norm_bool(v):
            return str(v).strip().lower() in ("1", "true", "yes", "y")

        if "is_pep" in parsed:
            submission.is_pep = _norm_bool(parsed.get("is_pep"))

        if "is_aml" in parsed:
            submission.is_aml = _norm_bool(parsed.get("is_aml"))

        # -------------------------
        # FILE HANDLING (single place)
        # -------------------------
        submission, urls, additional_struct = _save_files_and_submission(
            request, user, submission=submission
        )

        submission.additional_docs = additional_struct

        merged.update(urls)
        merged["additional_docs"] = additional_struct

        submission.data_json = merged
        submission.version = (submission.version or 1) + 1
        submission.submitted_at = timezone.now()

        # 🔒 RE-APPLY branch AFTER helper (helper overwrites fields)
        if parsed.get("branch_name"):
            submission.bank_branch = parsed["branch_name"]

        print(
        "DEBUG FINAL bank_branch:",
            submission.bank_branch,
            "JSON:",
            submission.data_json.get("branch_name")
        )
        submission.save()

        # Cleanup temp
        if temp:
            temp.delete()


# -----------------------------------------------------------------------------
# Admin views
# -----------------------------------------------------------------------------
def admin_login(request):
    if request.method == "GET":
        return render(request, "admin_login.html")

    username = request.POST.get("username")
    password = request.POST.get("password")

    if not username or not password:
        messages.error(request, "Username and password are required.", extra_tags="error")
        return redirect("/auth/admin/")

    try:
        admin = KycAdmin.objects.get(username__iexact=username)
    except KycAdmin.DoesNotExist:
        messages.error(request, "Admin user not found!", extra_tags="error")
        return redirect("/auth/admin/")

    if admin.password != password:
        messages.error(request, "Incorrect password!", extra_tags="error")
        return redirect("/auth/admin/")

    request.session["admin_logged_in"] = True
    request.session["admin_id"] = admin.id
    request.session["admin_username"] = admin.username

    messages.success(request, "Login successful!", extra_tags="success")
    return redirect("/rjbcl-admin/dashboard/")


def admin_dashboard(request):
    if not request.session.get("admin_id"):
        messages.error(request, "Please login as admin.", extra_tags="error")
        return redirect("/rjbcl-admin/login/")

    total_kyc = KycUserInfo.objects.count()
    pending_kyc = KycUserInfo.objects.filter(kyc_status="PENDING").count()
    approved_kyc = KycUserInfo.objects.filter(kyc_status="VERIFIED").count()

    recent = KycUserInfo.objects.order_by("-user_id")[:10]
    data = [{
        "policy_no": u.user_id,
        "name": f"{u.first_name} {u.last_name}",
        "status": u.kyc_status,
        "submitted": "N/A",
    } for u in recent]

    return render(request, "admin_dashboard.html", {
        "admin_user": request.session.get("admin_username"),
        "total_kyc": total_kyc,
        "pending_kyc": pending_kyc,
        "approved_kyc": approved_kyc,
        "recent_kyc": data,
    })


def admin_logout(request):
    request.session.flush()
    messages.success(request, "You have been logged out.", extra_tags="success")
    return redirect("/rjbcl-admin/login/")


def policy_logout(request):
    request.session.flush()
    messages.success(request, "You have been logged out.", extra_tags="success")
    return redirect("/auth/policy/?tab=policy")


# -----------------------------------------------------------------------------
# Save KYC progress endpoint (AJAX multipart)
# -----------------------------------------------------------------------------
@csrf_exempt
def save_kyc_progress(request):

    # -------------------------
    # AUTH CHECK (LOGIN OR DIRECT KYC)
    # -------------------------
    is_login_flow = request.session.get("authenticated") is True

    is_direct_kyc = (
        request.session.get("kyc_access_mode") == "DIRECT_KYC"
        and request.session.get("kyc_user_id")
        and request.session.get("kyc_policy_no")
    )

    if not (is_login_flow or is_direct_kyc):
        return JsonResponse({"error": "Not authenticated"}, status=403)

    # -------------------------
    # POLICY RESOLUTION
    # -------------------------
    if is_login_flow:
        policy_no = request.POST.get("policy_no")

    elif is_direct_kyc:
        policy_no = request.session.get("kyc_policy_no")

    else:
        return JsonResponse({"error": "Not authenticated"}, status=403)

    if not policy_no:
        return JsonResponse({"error": "Missing policy number"}, status=400)


    """
    Endpoint for Save & Continue (AJAX).
    Accepts multipart/form-data and returns JSON with saved file URLs and counts.
    """
    raw_json = request.POST.get("kyc_data")

    if not policy_no:
        return JsonResponse({"error": "Missing policy number"}, status=400)

    try:
        parsed = json.loads(raw_json) if raw_json else {}
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    # Ensure marital_status is preserved from form POST (radio button)
    if "marital_status" in request.POST:
        parsed["marital_status"] = request.POST.get("marital_status")

    if not isinstance(parsed, dict):
        parsed = {}

    # Make folder path for temporary files
    safe_folder = f"kyc/temp/{policy_no}"
    saved_files = {}

    # helper to save and return url
    def _save(field_name, file_obj):
        if not file_obj:
            return None
        saved_path, url = save_uploaded_file_to_storage(file_obj, safe_folder)
        return saved_path, url

    # mapping known files to keys returned in JSON
    single_file_map = {
        "photo": "photo_url",
        "citizenship-front": "citizenship_front_url",
        "citizenship-back": "citizenship_back_url",
        "signature": "signature_url",
        "passport_doc": "passport_doc_url",
    }

    for field_name, json_key in single_file_map.items():
        fobj = request.FILES.get(field_name)
        if fobj:
            try:
                saved_path, url = _save(field_name, fobj)
                if url:
                    parsed[json_key] = url
                    saved_files[json_key] = url
            except ValidationError as e:
                return JsonResponse({"error": str(e)}, status=400)
            except Exception as e:
                return JsonResponse({"error": f"Failed to save {field_name}: {e}"}, status=500)

    # Handle NID upload (store as KycDocument and include nid_url in parsed)
    nid_file = request.FILES.get("nid")
    if nid_file:
        try:
            # save to temp folder
            saved_path, url = _save("nid", nid_file)
            if url:
                parsed["nid_url"] = url
                saved_files["nid_url"] = url
            # create KycDocument if user exists
            try:
                policy = KycPolicy.objects.get(policy_number=policy_no)
                user = KycUserInfo.objects.get(user_id=policy.user_id)
                KycDocument.objects.create(
                    user=user,
                    doc_type="NID",
                    file=saved_path,
                    file_name=get_valid_filename(nid_file.name)
                )
            except Exception:
                # don't fail the whole save if doc creation fails
                pass
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Failed to save nid: {e}"}, status=500)

    # Additional docs dynamic handling (additional_doc_1, additional_doc_2, ...)
    additional_docs_in_payload = parsed.get("additional_docs", [])
    collected_additional = []

    MAX_ADD_DOCS = 12
    for i in range(1, MAX_ADD_DOCS + 1):
        name_key = f"additional_doc_name_{i}"
        file_field = f"additional_doc_{i}"
        name_val = request.POST.get(name_key) or None
        file_obj = request.FILES.get(file_field)

        if name_val or file_obj:
            entry = {"index": i, "doc_name": name_val or ""}
            if file_obj:
                try:
                    spath, url = _save(file_field, file_obj)
                    entry["file_url"] = url
                except ValidationError as e:
                    return JsonResponse({"error": str(e)}, status=400)
                except Exception as e:
                    return JsonResponse({"error": f"Failed to save {file_field}: {e}"}, status=500)
            else:
                # preserve existing file_url from parsed(payload) if present
                existing = next((x for x in additional_docs_in_payload if x.get("index") == i), None)
                entry["file_url"] = existing.get("file_url") if existing else ""
            collected_additional.append(entry)

    if collected_additional:
        parsed["additional_docs"] = collected_additional

    # Normalize _current_step if present
    try:
        if "_current_step" in parsed:
            parsed["_current_step"] = int(parsed["_current_step"])
    except Exception:
        parsed["_current_step"] = parsed.get("_current_step", 1)

    # Persist or update KYCTemporary
    policy = KycPolicy.objects.get(policy_number=policy_no)
    user = KycUserInfo.objects.get(user_id=policy.user_id)

    KYCTemporary.objects.update_or_create(
        user=user,
        defaults={
            "policy_no": policy_no,
            "data_json": parsed
        }
    )


    return JsonResponse({
        "status": "saved",
        "policy": policy_no,
        "saved_files": saved_files,
        "additional_docs_count": len(parsed.get("additional_docs", []))
    })

def view_additional_doc(request, doc_id):
    """
    Securely stream an additional KYC document.
    """
    if not request.session.get("authenticated"):
        return redirect("/auth/policy/?tab=policy")

    doc = get_object_or_404(
        KycDocument,
        id=doc_id,
        doc_type="ADDITIONAL",
        is_current=True
    )

    return FileResponse(
        doc.file.open("rb"),
        as_attachment=False,
        filename=doc.file_name
    )
# -----------------------------------------------------------------------------
# Direct KYC entry view (no login)

def direct_kyc_entry_view(request):
    """
    Direct KYC entry without login.
    Inputs:
      - policy_no
      - dob_ad
    """

    if request.method == "GET":
        return render(request, "kyc/direct_entry.html")

    policy_no = (request.POST.get("policy_no") or "").strip()
    dob_ad = (request.POST.get("dob_ad") or "").strip()

    if not policy_no or not dob_ad:
        messages.error(request, "Policy number and DOB are required.")
        return redirect("kyc:direct_kyc_entry")

    # -------------------------------------------------
    # VALIDATE POLICY + DOB (single source of truth)
    # -------------------------------------------------
    try:
        user, user_id = resolve_policy_identity(
            policy_no=policy_no,
            dob_ad=dob_ad,
        )
    except ValidationError:
        messages.error(
            request,
            "Invalid policy number or date of birth. Please check and try again."
        )
        return redirect("kyc:direct_kyc_entry")

    # -------------------------------------------------
    # 🚫 BLOCK DIRECT KYC FOR NON-EDITABLE STATUS
    # -------------------------------------------------
    if user.kyc_status in ["PENDING", "VERIFIED"]:
        messages.error(
            request,
            "KYC already submitted. Please contact your branch for further assistance."
        )
        return redirect("/auth/policy/?tab=policy")

    # -------------------------------------------------
    # 🔐 CLEAN SESSION (CRITICAL)
    # -------------------------------------------------
    request.session.flush()      # remove any old login session
    request.session.cycle_key()  # prevent fixation

    # -------------------------------------------------
    # SESSION BINDING (STRICT)
    # -------------------------------------------------
    request.session["kyc_access_mode"] = "DIRECT_KYC"
    request.session["kyc_policy_no"] = policy_no
    request.session["kyc_user_id"] = user_id
    request.session["kyc_dob"] = user.dob.isoformat()

    # -------------------------------------------------
    # AUDIT LOG (OPTIONAL BUT GOOD)
    # -------------------------------------------------
    submission = KycSubmission.objects.filter(user=user).first()
    if submission:
        KycChangeLog.objects.create(
            submission=submission,
            action="CREATE",
            actor_type="SYSTEM",
            actor_identifier="DIRECT_KYC",
            comment=f"Direct KYC access granted for policy {policy_no}",
        )

    return redirect("/kyc-form/")


def kyc_submitted_view(request):
   return redirect("/auth/policy/?tab=policy")


@require_POST
def send_mobile_otp(request):
    """
    Sends OTP to policyholder mobile number via FastAPI gateway.
    Works for BOTH:
      - Normal login
      - Direct KYC
    """

    mobile = request.POST.get("mobile")

    if not mobile or len(mobile) != 10:
        return JsonResponse({"error": "Invalid mobile number"}, status=400)

    # -------------------------------------------------
    # 🔐 RESOLVE KYC USER (LOGIN OR DIRECT KYC)
    # -------------------------------------------------
    user = None

    if request.session.get("authenticated"):
        policy_no = request.session.get("policy_no")
        policy = KycPolicy.objects.filter(policy_number=policy_no).first()
        if not policy:
            return JsonResponse({"error": "User not found"}, status=403)
        user = KycUserInfo.objects.filter(user_id=policy.user_id).first()

    elif request.session.get("kyc_access_mode") == "DIRECT_KYC":
        user_id = request.session.get("kyc_user_id")
        user = KycUserInfo.objects.filter(user_id=user_id).first()

    if not user:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    # -------------------------------------------------
    # 📡 CALL FASTAPI OTP GATEWAY
    # -------------------------------------------------
    try:
        resp = requests.post(
            f"{settings.FASTAPI_BASE_URL}/otp/send",
            params={"mobile": mobile},
            timeout=10
        )
    except requests.RequestException:
        return JsonResponse({"error": "OTP service unavailable"}, status=503)

    if resp.status_code != 200:
        return JsonResponse({"error": "Failed to send OTP"}, status=400)

    otp = resp.json().get("otp")
    if not otp:
        return JsonResponse({"error": "OTP generation failed"}, status=500)

    # -------------------------------------------------
    # 🔁 OTP DB HANDLING (SECURE)
    # -------------------------------------------------
    KycMobileOTP.objects.filter(
        kyc_user=user,
        is_verified=False
    ).delete()

    KycMobileOTP.objects.create(
        kyc_user=user,
        mobile=mobile,
        otp_hash=make_password(otp),  # ✅ FIX
        expires_at=timezone.now() + timedelta(minutes=2)
    )

    return JsonResponse({
        "success": True,
        "message": "OTP sent successfully"
    })


@require_POST
def verify_mobile_otp(request):

    otp_input = (request.POST.get("otp") or "").strip()

    if not otp_input or len(otp_input) != 6:
        return JsonResponse({"error": "Invalid OTP format"}, status=400)

    # Resolve user
    user = None

    if request.session.get("authenticated"):
        policy_no = request.session.get("policy_no")
        policy = KycPolicy.objects.filter(policy_number=policy_no).first()
        if not policy:
            return JsonResponse({"error": "Unauthorized"}, status=403)
        user = KycUserInfo.objects.filter(user_id=policy.user_id).first()

    elif request.session.get("kyc_access_mode") == "DIRECT_KYC":
        user_id = request.session.get("kyc_user_id")
        user = KycUserInfo.objects.filter(user_id=user_id).first()

    if not user:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    otp_obj = (
        KycMobileOTP.objects
        .filter(
            kyc_user=user,
            is_verified=False,
            expires_at__gt=timezone.now()
        )
        .order_by("-id")
        .first()
    )

    if not otp_obj:
        return JsonResponse({"error": "OTP expired or not found"}, status=400)

    if not check_password(otp_input, otp_obj.otp_hash):
        return JsonResponse({"error": "Incorrect OTP"}, status=400)

    # ✅ SUCCESS PATH ONLY
    otp_obj.is_verified = True
    otp_obj.save(update_fields=["is_verified"])

    user.mobile_verified = True
    user.save(update_fields=["mobile_verified"])

    request.session["mobile_otp_verified"] = True
    request.session.pop("otp_required", None)

    return JsonResponse({
        "success": True,
        "message": "Mobile number verified successfully"
    })
