# kycform/views.py
import json
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.core.exceptions import ValidationError
import traceback

from .models import KycUserInfo, KycAgentInfo, KycPolicy, KycAdmin, KycSubmission, KycDocument
from kycform.services.kyc_submit_service import process_kyc_submission


# ============================================================
# UTILITIES
# ============================================================

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


# ============================================================
# AUTHENTICATION (POLICYHOLDER)
# ============================================================

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
    except:
        messages.error(request, "Invalid policy number or user not found.")
        return redirect_login_tab("policy")

    if password != (user.password or ""):
        messages.error(request, "Incorrect password!")
        return redirect_login_tab("policy")

    kyc_status = normalize_status(user.kyc_status)

    # Decide where to go
    if kyc_status in ["NOT_INITIATED", "INCOMPLETE", "REJECTED", ""]:
        return redirect(f"/kyc-form/?policy_no={policy_no}")

    if kyc_status in ["PENDING", "VERIFIED"]:
        return redirect(f"/dashboard/?policy_no={policy_no}")

    return redirect(f"/kyc-form/?policy_no={policy_no}")


# ============================================================
# AUTHENTICATION (AGENT)
# ============================================================

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
    except:
        messages.error(request, "Agent code not found!")
        return redirect_login_tab("agent")

    if password != (agent.password or ""):
        messages.error(request, "Incorrect password!")
        return redirect_login_tab("agent")

    return redirect(f"/agent-dashboard/?agent_code={agent_code}")


# ============================================================
# KYC FORMS
# ============================================================

def kyc_form_view(request):
    return render(request, "kyc_form_update.html", {
        "policy_no": request.GET.get("policy_no")
    })


def dashboard_view(request):
    return render(request, "dashboard.html", {
        "policy_no": request.GET.get("policy_no")
    })


def agent_dashboard_view(request):
    return render(request, "dashboard.html", {
        "agent_code": request.GET.get("agent_code")
    })


# ============================================================
# KYC FORM SUBMISSION
# ============================================================

def kyc_form_submit(request):
    if request.method != "POST":
        messages.error(request, "Invalid request!")
        return redirect("/")

    policy_no = request.POST.get("policy_no")

    try:
        # PROCESS FULL KYC
        user = process_kyc_submission(request)

        messages.success(request, "Your KYC form has been successfully submitted.")
        return redirect(f"/dashboard/?policy_no={policy_no}")

    except Exception as e:
        print("\n============== KYC SUBMISSION ERROR ===============")
        print("Error:", e)
        traceback.print_exc()
        print("===================================================\n")

        messages.error(request, f"KYC submission failed: {e}")
        return redirect(f"/kyc-form/?policy_no={policy_no}")



# ============================================================================
# REGISTRATION (POLICYHOLDER & AGENT)
# ============================================================================

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

    if not user.user_email:
        user.user_email = email
    elif user.user_email.lower() != email.lower():
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


# ============================================================================
# FORGOT PASSWORD (Common for Agent + Policyholders)
# ============================================================================

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


# ============================================================================
# RESET PASSWORD (Common Handler)
# ============================================================================

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


# ============================================================================
# KYC + DASHBOARD
# ============================================================================

def kyc_form_view(request):
    policy_no = request.GET.get("policy_no")

    if not policy_no:
        messages.error(request, "Missing policy number.")
        return redirect("/")

    # 1. POLICY
    try:
        policy = KycPolicy.objects.get(policy_number=policy_no)
    except KycPolicy.DoesNotExist:
        messages.error(request, "Invalid policy number.")
        return redirect("/")

    # 2. USER
    try:
        user = KycUserInfo.objects.get(user_id=policy.user_id)
    except KycUserInfo.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("/")

    # 3. BLOCK ALREADY DONE
    if user.kyc_status in ["PENDING", "VERIFIED"]:
        return redirect(f"/dashboard/?policy_no={policy_no}")

    # 4. BASIC USER INFO
    user_info = model_to_dict(user, exclude=["password"])

    # 5. SUBMISSION (if exists)
    try:
        submission = KycSubmission.objects.get(user=user)
        submission_data = model_to_dict(
            submission,
            exclude=["id", "submitted_at", "user"]
        )
    except KycSubmission.DoesNotExist:
        submission_data = {}

    # 6. MERGE
    merged = {**user_info, **submission_data}

    # ==================================================================
    # 7. FULL FIELD-NAME MAPPING (HTML ← MODEL EXACT MATCH)
    # ==================================================================

    fixed = {}

    # --------------------------
    # PERSONAL DETAILS
    # --------------------------
    fixed["first_name"] = merged.get("first_name")
    fixed["middle_name"] = merged.get("middle_name")
    fixed["last_name"] = merged.get("last_name")
    fixed["full_name_nep"] = merged.get("full_name_nep")
    fixed["email"] = merged.get("email")

    # Phone number
    fixed["mobile"] = merged.get("phone_number")

    # Gender / Marital / Salutation
    fixed["gender"] = merged.get("gender")
    fixed["marital_status"] = merged.get("marital_status")
    fixed["salutation"] = merged.get("salutation")
    fixed["nationality"] = merged.get("nationality")

    # DOB AD → HTML field name
    if merged.get("dob"):
        fixed["dob_ad"] = merged["dob"].isoformat()
        fixed["dob_bs_auto"] = fixed["dob_ad"]  # JS converts to BS

    # --------------------------
    # FAMILY DETAILS
    # --------------------------
    fixed["spouse_name"] = merged.get("spouse_name")
    fixed["father_name"] = merged.get("father_name")
    fixed["mother_name"] = merged.get("mother_name")
    fixed["grand_father_name"] = merged.get("grand_father_name")
    fixed["father_in_law_name"] = merged.get("father_in_law_name")
    fixed["son_name"] = merged.get("son_name")
    fixed["daughter_name"] = merged.get("daughter_name")
    fixed["daughter_in_law_name"] = merged.get("daughter_in_law_name")

    # --------------------------
    # CITIZENSHIP / DOCUMENTS
    # --------------------------
    fixed["citizenship_no"] = merged.get("citizenship_no")
    fixed["citizen_bs"] = merged.get("citizen_bs")

    if merged.get("citizen_ad"):
        fixed["citizen_ad"] = merged["citizen_ad"].isoformat()

    fixed["citizenship_place"] = merged.get("citizenship_issued_place")
    fixed["passport_no"] = merged.get("passport_no")
    fixed["nid_no"] = merged.get("nid_no")

    # --------------------------
    # PERMANENT ADDRESS
    # --------------------------
    fixed["perm_province"] = merged.get("perm_province")
    fixed["perm_district"] = merged.get("perm_district")
    fixed["perm_municipality"] = merged.get("perm_municipality")
    fixed["perm_ward"] = merged.get("perm_ward")
    fixed["perm_address"] = merged.get("perm_address")
    fixed["perm_house_number"] = merged.get("perm_house_number")

    # --------------------------
    # TEMPORARY ADDRESS
    # --------------------------
    fixed["temp_province"] = merged.get("temp_province")
    fixed["temp_district"] = merged.get("temp_district")
    fixed["temp_municipality"] = merged.get("temp_municipality")
    fixed["temp_ward"] = merged.get("temp_ward")
    fixed["temp_address"] = merged.get("temp_address")
    fixed["temp_house_number"] = merged.get("temp_house_number")

    # --------------------------
    # BANK DETAILS
    # --------------------------
    fixed["bank_name"] = merged.get("bank_name")
    fixed["branch_name"] = merged.get("bank_branch")
    fixed["account_number"] = merged.get("bank_account_number")
    fixed["account_type"] = merged.get("bank_account_type")

    # --------------------------
    # OCCUPATION
    # --------------------------
    fixed["occupation"] = merged.get("occupation")
    fixed["occupation_description"] = merged.get("occupation_description")
    fixed["income_mode"] = merged.get("income_mode")
    fixed["annual_income"] = merged.get("annual_income")
    fixed["income_source"] = merged.get("income_source")
    fixed["pan_number"] = merged.get("pan_number")
    fixed["qualification"] = merged.get("qualification")
    fixed["employer_name"] = merged.get("employer_name")
    fixed["office_address"] = merged.get("office_address")

    # --------------------------
    # NOMINEE
    # --------------------------
    fixed["nominee_name"] = merged.get("nominee_name")
    fixed["nominee_relation"] = merged.get("nominee_relation")

    if merged.get("nominee_dob_ad"):
        fixed["nominee_dob_ad"] = merged["nominee_dob_ad"].isoformat()
        fixed["nominee_dob_bs_auto"] = fixed["nominee_dob_ad"]

    fixed["nominee_contact"] = merged.get("nominee_contact")
    fixed["guardian_name"] = merged.get("guardian_name")
    fixed["guardian_relation"] = merged.get("guardian_relation")

    # --------------------------
    # PEP / AML
    # --------------------------
    fixed["is_pep"] = merged.get("is_pep")
    fixed["is_aml"] = merged.get("is_aml")

    # ==================================================================
    # 8. JSON OUTPUT
    # ==================================================================
    prefill_json = json.dumps(fixed, ensure_ascii=False)

    return render(request, "kyc_form_update.html", {
        "policy_no": policy_no,
        "prefill_json": prefill_json
    })


def dashboard_view(request):
    return render(request, "dashboard.html", {
        "policy_no": request.GET.get("policy_no")
    })


def agent_dashboard_view(request):
    return render(request, "dashboard.html", {
        "agent_code": request.GET.get("agent_code")
    })


def kyc_form_submit(request):
    if request.method != "POST":
        messages.error(request, "Invalid request!", extra_tags="error")
        return redirect("/")

    policy_no = request.POST.get("policy_no")
    messages.success(request, "Your KYC form has been submitted.", extra_tags="success")
    return redirect(f"/dashboard/?policy_no={policy_no}")

# ------------------------------------------------------------------
# ADMIN LOGIN
# ------------------------------------------------------------------
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

    # Validate password
    if admin.password != password:
        messages.error(request, "Incorrect password!", extra_tags="error")
        return redirect("/auth/admin/")

    # Store login session
    request.session["admin_logged_in"] = True
    request.session["admin_id"] = admin.id
    request.session["admin_username"] = admin.username

    messages.success(request, "Login successful!", extra_tags="success")
    return redirect("/rjbcl-admin/dashboard/")



# ------------------------------------------------------------------
# ADMIN DASHBOARD
# ------------------------------------------------------------------
def admin_dashboard(request):
    if not request.session.get("admin_id"):
        messages.error(request, "Please login as admin.", extra_tags="error")
        return redirect("/rjbcl-admin/login/")

    # Stats
    total_kyc = KycUserInfo.objects.count()
    pending_kyc = KycUserInfo.objects.filter(kyc_status="PENDING").count()
    approved_kyc = KycUserInfo.objects.filter(kyc_status="VERIFIED").count()

    # FIXED: order by user_id, not id
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



# ------------------------------------------------------------------
# ADMIN LOGOUT
# ------------------------------------------------------------------
def admin_logout(request):
    request.session.flush()   # Clears all session data
    messages.success(request, "You have been logged out.", extra_tags="success")
    return redirect("/rjbcl-admin/login/")

# ------------------------------------------------------------------
# POLICYHOLDER LOGOUT
# ------------------------------------------------------------------
def policy_logout(request):
    request.session.flush()   # Clear all session data (safe)
    messages.success(request, "You have been logged out.", extra_tags="success")

    # Redirect to the active policy login tab
    return redirect("/auth/policy/?tab=policy")


# ------------------------------------------------------------------
# KYC FORM SUBMISSION HANDLER
# ------------------------------------------------------------------

import traceback

def kyc_form_submit(request):
    if request.method != "POST":
        messages.error(request, "Invalid request!", extra_tags="error")
        return redirect("/")

    try:
        user = process_kyc_submission(request)
        policy_no = request.POST.get("policy_no")

        messages.success(request, "Your KYC form has been successfully submitted.", extra_tags="success")
        return redirect(f"/dashboard/?policy_no={policy_no}")

    except Exception as e:
        print("\n============== KYC SUBMISSION ERROR ===============")
        print("Error:", e)
        traceback.print_exc()
        print("===================================================\n")

        messages.error(request, f"KYC submission failed: {e}", extra_tags="error")
        return redirect(f"/kyc-form/?policy_no={request.POST.get('policy_no')}")
