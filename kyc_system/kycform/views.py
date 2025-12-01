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
import traceback
import urllib.request
from datetime import datetime, date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.text import get_valid_filename
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import (
    KycUserInfo, KycAgentInfo, KycPolicy, KycAdmin,
    KycSubmission, KycDocument, KYCTemporary
)

# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------
MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB default per-file check


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

    try:
        policy = KycPolicy.objects.get(policy_number__iexact=policy_no)
        user = KycUserInfo.objects.get(user_id=policy.user_id)
    except Exception:
        messages.error(request, "Invalid policy number or user not found.")
        return redirect_login_tab("policy")

    if password != (user.password or ""):
        messages.error(request, "Incorrect password!")
        return redirect_login_tab("policy")

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
    return render(request, "dashboard.html", {
        "policy_no": request.GET.get("policy_no")
    })


def agent_dashboard_view(request):
    return render(request, "dashboard.html", {
        "agent_code": request.GET.get("agent_code")
    })


# -----------------------------------------------------------------------------
# Registration / Forgot / Reset
# -----------------------------------------------------------------------------
def policyholder_register_view(request):
    if request.method == "GET":
        return render(request, "register.html")

    policy_no = request.POST.get("policy_number")
    email = request.POST.get("email")
    mobile = request.POST.get("mobile")

    if missing_fields(policy_no, email, mobile):
        messages.error(request, "All fields are required.", extra_tags="error")
        return redirect("kyc:policy_register")

    try:
        policy = KycPolicy.objects.get(policy_number__iexact=policy_no)
        user = KycUserInfo.objects.get(user_id=policy.user_id)
    except (KycPolicy.DoesNotExist, KycUserInfo.DoesNotExist):
        messages.error(request, "Policy not found!", extra_tags="error")
        return redirect("kyc:policy_register")

    if user.password:
        messages.error(request, "You are already registered. Please log in.", extra_tags="error")
        return redirect_login_tab("policy")

    # Keep the field names consistent with your model
    if not user.email:
        user.email = email
    elif user.email.lower() != email.lower():
        messages.error(request, "Email does not match our records!", extra_tags="error")
        return redirect("kyc:policy_register")

    if not user.phone_number:
        user.phone_number = mobile
    elif user.phone_number != mobile:
        messages.error(request, "Mobile number does not match!", extra_tags="error")
        return redirect("kyc:policy_register")

    user.password = user.dob.strftime("%Y%m%d")
    user.save()

    messages.success(request, "Password sent to your email/mobile.", extra_tags="success")
    return redirect_login_tab("policy")


def agent_register_view(request):
    if request.method == "GET":
        return render(request, "agent_register.html")

    agent_code = request.POST.get("agent_code")
    first_name = request.POST.get("first_name")
    last_name = request.POST.get("last_name")
    phone = request.POST.get("phone_number")
    email = request.POST.get("email")

    if missing_fields(agent_code, first_name, last_name, phone, email):
        messages.error(request, "All fields are required.", extra_tags="error")
        return redirect("kyc:agent_register")

    try:
        agent = KycAgentInfo.objects.get(agent_code__iexact=agent_code)
    except KycAgentInfo.DoesNotExist:
        messages.error(request, "Agent code not found!", extra_tags="error")
        return redirect("kyc:agent_register")

    if agent.password:
        messages.error(request, "You are already registered.", extra_tags="error")
        return redirect_login_tab("agent")

    if agent.first_name.lower() != first_name.lower():
        messages.error(request, "First name mismatch!", extra_tags="error")
        return redirect("kyc:agent_register")

    if agent.last_name.lower() != last_name.lower():
        messages.error(request, "Last name mismatch!", extra_tags="error")
        return redirect("kyc:agent_register")

    if agent.phone_number != phone:
        messages.error(request, "Phone number mismatch!", extra_tags="error")
        return redirect("kyc:agent_register")

    if agent.email.lower() != email.lower():
        messages.error(request, "Email mismatch!", extra_tags="error")
        return redirect("kyc:agent_register")

    agent.password = agent.dob.strftime("%Y%m%d")
    agent.save()

    messages.success(request, "Password sent to your email/mobile.", extra_tags="success")
    return redirect_login_tab("agent")


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
        if user_type == "agent":
            user = KycAgentInfo.objects.get(agent_code__iexact=identifier)
        else:
            policy = KycPolicy.objects.get(policy_number__iexact=identifier)
            user = KycUserInfo.objects.get(user_id=policy.user_id)

        if not user.password:
            messages.error(request, "You are not registered.", extra_tags="error")
            return redirect_login_tab(user_type)

        if str(user.dob) != dob:
            messages.error(request, "DOB does not match!", extra_tags="error")
            return redirect(f"/forgot-password/?type={user_type}")

        return redirect(f"/reset-password/?type={user_type}&identifier={identifier}")

    except Exception:
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
        if user_type == "agent":
            user = KycAgentInfo.objects.get(agent_code__iexact=identifier)
        else:
            policy = KycPolicy.objects.get(policy_number__iexact=identifier)
            user = KycUserInfo.objects.get(user_id=policy.user_id)

        user.password = new_pass
        user.save()

        messages.success(request, "Password updated successfully!", extra_tags="success")
        return redirect_login_tab(user_type)

    except Exception:
        messages.error(request, "Something went wrong!", extra_tags="error")
        return redirect(f"/reset-password/?type={user_type}&identifier={identifier}")


# -----------------------------------------------------------------------------
# KYC Form view (prefill) — single endpoint returning the template + prefill JSON
# -----------------------------------------------------------------------------
@csrf_exempt
def kyc_form_view(request):
    """
    Loads KYC update form with full prefill data.
    Priority order:
       1) KYCTemporary (Save & Continue)
       2) KycSubmission (Final Saved Data)
       3) KycUserInfo (Base Policyholder Info)
    Always forces file URLs from model FileFields (submission.*.url)
    """

    policy_no = request.GET.get("policy_no")
    if not policy_no:
        messages.error(request, "Missing policy number.")
        return redirect("/")

    # Policy
    try:
        policy = KycPolicy.objects.get(policy_number=policy_no)
    except KycPolicy.DoesNotExist:
        messages.error(request, "Invalid policy number.")
        return redirect("/")

    # User
    try:
        user = KycUserInfo.objects.get(user_id=policy.user_id)
    except KycUserInfo.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("/")

    # Redirect verified/pending
    if user.kyc_status in ["PENDING", "VERIFIED"]:
        return redirect(f"/dashboard/?policy_no={policy_no}")

    # 1) User info
    user_info = safe_model_dict(model_to_dict(user, exclude=["password"]))

    # 2) Submission data
    try:
        submission = KycSubmission.objects.get(user=user)
        submission_data = safe_model_dict(
            model_to_dict(submission, exclude=["id", "user", "submitted_at"])
        )
    except KycSubmission.DoesNotExist:
        submission = None
        submission_data = {}

    # 3) Temp draft
    try:
        temp = KYCTemporary.objects.get(policy_no=policy_no)
        temp_data = safe_model_dict(temp.data_json)
    except KYCTemporary.DoesNotExist:
        temp_data = {}

    # Merge priority: temp > submission > user
    merged = {**user_info, **submission_data, **temp_data}

    # Start final prefill output
    fixed = {}

    # Copy simple fields directly
    simple_fields = [
        # Personal
        "salutation", "first_name", "middle_name", "last_name", "full_name_nep",
        "email", "mobile", "gender", "nationality", "marital_status",
        "dob_ad", "dob_bs", "dob_bs_auto",

        # Family
        "spouse_name", "father_name", "mother_name", "grand_father_name",
        "father_in_law_name", "son_name", "daughter_name", "daughter_in_law_name",

        # Documents (text info)
        "citizenship_no", "citizen_bs", "citizen_ad", "citizenship_place",
        "passport_no", "nid_no",

        # Permanent Address
        "perm_province", "perm_district", "perm_municipality", "perm_ward",
        "perm_address", "perm_house_number",

        # Temporary Address
        "temp_province", "temp_district", "temp_municipality", "temp_ward",
        "temp_address", "temp_house_number",

        # Bank
        "bank_name", "bank_branch", "account_number", "account_type", "branch_name",

        # Occupation
        "occupation", "occupation_description", "income_mode", "annual_income",
        "income_source", "pan_number", "qualification", "employer_name", "office_address",

        # Nominee
        "nominee_name", "nominee_relation", "nominee_dob_ad", "nominee_dob_bs",
        "nominee_contact", "guardian_name", "guardian_relation",

        # AML / PEP
        "is_pep", "is_aml",

        "_current_step"
    ]

    for f in simple_fields:
        fixed[f] = merged.get(f)

    # --------------------------------------------
    # Normalize marital_status (fix radio prefill)
    # --------------------------------------------
    ms = merged.get("marital_status")

    if ms:
        # Convert: married → Married, unmarried → Unmarried
        ms = str(ms).strip().title()
    else:
        ms = None
    fixed["marital_status"] = ms

    # ---------------------------------------------------------------
    # FORCE FILE URLs FROM MODEL (NOT JSON)
    # ---------------------------------------------------------------
    if submission:
        fixed["photo_url"] = submission.photo.url if submission.photo else None
        fixed["citizenship_front_url"] = submission.citizenship_front.url if submission.citizenship_front else None
        fixed["citizenship_back_url"] = submission.citizenship_back.url if submission.citizenship_back else None
        fixed["signature_url"] = submission.signature.url if submission.signature else None
        fixed["passport_doc_url"] = submission.passport_doc.url if submission.passport_doc else None

        # Additional docs
        fixed["additional_docs"] = submission.additional_docs or []

        # NID (stored separately)
        fixed["nid_url"] = merged.get("nid_url")
    else:
        # No submission yet
        fixed["photo_url"] = None
        fixed["citizenship_front_url"] = None
        fixed["citizenship_back_url"] = None
        fixed["signature_url"] = None
        fixed["passport_doc_url"] = None
        fixed["additional_docs"] = merged.get("additional_docs", [])
        fixed["nid_url"] = merged.get("nid_url")

    # ---------------------------------------------------------------
    # Return final prefill
    # ---------------------------------------------------------------
    prefill_json = json.dumps(fixed, ensure_ascii=False)

    return render(request, "kyc_form_update.html", {
        "policy_no": policy_no,
        "prefill_json": prefill_json
    })

# -----------------------------------------------------------------------------
# Final submission handler (exposed for form POST)
# -----------------------------------------------------------------------------
@csrf_exempt
def kyc_form_submit(request):
    """
    Final KYC submission endpoint used by the regular form POST.
    It delegates to process_kyc_submission (same logic).
    """
    if request.method != "POST":
        messages.error(request, "Invalid request!")
        return redirect("/")

    policy_no = request.POST.get("policy_no")
    try:
        user = process_kyc_submission(request)
        messages.success(request, "Your KYC form has been successfully submitted.")
        return redirect(f"/dashboard/?policy_no={policy_no}")
    except Exception as e:
        traceback.print_exc()
        messages.error(request, f"KYC submission failed: {e}")
        return redirect(f"/kyc-form/?policy_no={policy_no}")


# -----------------------------------------------------------------------------
# process_kyc_submission  (callable by view + possible service re-use)
# -----------------------------------------------------------------------------
@csrf_exempt
def process_kyc_submission(request):
    """
    Final KYC submission handler.
    - Accepts POST form-data (multipart)
    - Merges saved draft + new data
    - Saves all files (photo, citizenship, passport, signature)
    - Writes BACK file URLs into data_json so frontend can show previews
    - Marks user KYC status as PENDING
    - Returns updated user
    """

    # ---------------------------------------------------------------
    # Basic validation
    # ---------------------------------------------------------------
    raw_json = request.POST.get("kyc_data")
    policy_no = request.POST.get("policy_no")

    if not policy_no:
        raise Exception("Missing policy number.")

    try:
        parsed = json.loads(raw_json) if raw_json else {}
        
    except Exception:
        parsed = {}

    # ---------------------------------------------------------------
    # Merge draft data saved via save-progress
    # ---------------------------------------------------------------
    try:
        temp = KYCTemporary.objects.get(policy_no=policy_no)
        temp_data = temp.data_json or {}
    except KYCTemporary.DoesNotExist:
        temp, temp_data = None, {}

    merged = {**temp_data, **parsed}

    # ---------------------------------------------------------------
    # Load User + Policy
    # ---------------------------------------------------------------
    try:
        policy = KycPolicy.objects.get(policy_number=policy_no)
        user = KycUserInfo.objects.get(user_id=policy.user_id)
    except Exception:
        raise Exception("User or policy not found.")

    # ---------------------------------------------------------------
    # Update user basic fields
    # ---------------------------------------------------------------
    user.first_name = merged.get("first_name") or user.first_name
    user.middle_name = merged.get("middle_name") or user.middle_name
    user.last_name = merged.get("last_name") or user.last_name
    user.full_name_nep = merged.get("full_name_nep") or user.full_name_nep
    user.email = merged.get("email") or user.email
    user.phone_number = merged.get("mobile") or user.phone_number

    if merged.get("dob_ad"):
        try:
            user.dob = datetime.strptime(merged["dob_ad"], "%Y-%m-%d").date()
        except Exception:
            pass

    # When user resubmits, set status back to pending
    user.kyc_status = "PENDING"
    user.save()

    # ---------------------------------------------------------------
    # Load or create submission record
    # ---------------------------------------------------------------
    try:
        submission = KycSubmission.objects.get(user=user)
    except KycSubmission.DoesNotExist:
        submission = KycSubmission(user=user)

    # ---------------------------------------------------------------
    # Normalize boolean helper
    # ---------------------------------------------------------------
    def _norm_bool(v):
        if v is None:
            return False
        s = str(v).strip().lower()
        return s in ("1", "true", "yes", "y")

    # ---------------------------------------------------------------
    # Copy mapped fields
    # ---------------------------------------------------------------
    field_map = [
        # Personal
        "salutation", "first_name", "middle_name", "last_name", "full_name_nep",
        "gender","marital_status", "nationality", "dob_ad", "dob_bs", "email", "mobile",

        # Family
        "spouse_name", "father_name", "mother_name", "grand_father_name",
        "father_in_law_name", "son_name", "daughter_name", "daughter_in_law_name",

        # Documents
        "citizenship_no", "citizen_bs", "citizen_ad", "citizenship_place",
        "passport_no", "nid_no",

        # Permanent
        "perm_province", "perm_district", "perm_municipality", "perm_ward",
        "perm_address", "perm_house_number",

        # Temporary
        "temp_province", "temp_district", "temp_municipality", "temp_ward",
        "temp_address", "temp_house_number",

        # Bank
        "bank_name", "account_number", "account_type", "branch_name",

        # Occupation
        "occupation", "occupation_description",
        "income_mode", "annual_income", "income_source", "pan_number",
        "qualification", "employer_name", "office_address",

        # Nominee
        "nominee_name", "nominee_relation", "nominee_dob_ad", "nominee_dob_bs",
        "nominee_contact", "guardian_name", "guardian_relation",
    ]

    for f in field_map:
        if f in merged:
            setattr(submission, f, merged[f])

    # Map branch_name to bank_branch
    if merged.get("branch_name"):
        submission.bank_branch = merged["branch_name"]

    # Convert AD dates
    for df in ("dob_ad", "citizen_ad", "nominee_dob_ad"):
        if merged.get(df):
            try:
                setattr(submission, df, datetime.strptime(merged[df], "%Y-%m-%d").date())
            except Exception:
                pass

    # AML / PEP
    submission.is_pep = _norm_bool(merged.get("is_pep"))
    submission.is_aml = _norm_bool(merged.get("is_aml"))

    # ---------------------------------------------------------------
    # File Save Helpers
    # ---------------------------------------------------------------
    dest_folder = f"kyc/{user.user_id}"

    def _save_file(request_key, model_field):
        """Save uploaded file and return final URL."""
        file_obj = request.FILES.get(request_key)
        if file_obj:
            saved_path, url = save_uploaded_file_to_storage(file_obj, dest_folder)
            getattr(submission, model_field).save(get_valid_filename(file_obj.name), file_obj, save=False)
            return url
        return None

    # Save each known file field
    photo_url = _save_file("photo", "photo")
    cit_front_url = _save_file("citizenship-front", "citizenship_front")
    cit_back_url = _save_file("citizenship-back", "citizenship_back")
    signature_url = _save_file("signature", "signature")
    passport_doc_url = _save_file("passport_doc", "passport_doc")

    # ---------------------------------------------------------------
    # NID handling (special case)
    # ---------------------------------------------------------------
    nid_url = None
    nid_file = request.FILES.get("nid")

    if nid_file:
        saved_path, nid_url = save_uploaded_file_to_storage(nid_file, dest_folder)
        try:
            KycDocument.objects.create(
                user=user,
                doc_type="NID",
                file_path=saved_path,
                file_name=get_valid_filename(nid_file.name),
            )
        except Exception:
            pass
    else:
        nid_url = merged.get("nid_url") or merged.get("nid")

    # Additional docs
    submission.additional_docs = merged.get("additional_docs", [])

    # ---------------------------------------------------------------
    # WRITE BACK ALL FILE URLs INTO JSON FOR PREFILL
    # ---------------------------------------------------------------
    merged["photo_url"] = photo_url or (submission.photo.url if submission.photo else None)
    merged["citizenship_front_url"] = cit_front_url or (submission.citizenship_front.url if submission.citizenship_front else None)
    merged["citizenship_back_url"] = cit_back_url or (submission.citizenship_back.url if submission.citizenship_back else None)
    merged["signature_url"] = signature_url or (submission.signature.url if submission.signature else None)
    merged["passport_doc_url"] = passport_doc_url or (submission.passport_doc.url if submission.passport_doc else None)
    merged["nid_url"] = nid_url

    # Additional docs returned for frontend
    merged["additional_docs"] = submission.additional_docs

    # Store full JSON
    submission.data_json = merged
    submission.save()

    # Remove draft
    if temp:
        try:
            temp.delete()
        except Exception:
            pass

    return user



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
@require_POST
def save_kyc_progress(request):
    """
    Endpoint for Save & Continue (AJAX).
    Accepts multipart/form-data and returns JSON with saved file URLs and counts.
    """
    policy_no = request.POST.get("policy_no")
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
                    file_path=saved_path,
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
    KYCTemporary.objects.update_or_create(
        policy_no=policy_no,
        defaults={"data_json": parsed}
    )

    return JsonResponse({
        "status": "saved",
        "policy": policy_no,
        "saved_files": saved_files,
        "additional_docs_count": len(parsed.get("additional_docs", []))
    })

