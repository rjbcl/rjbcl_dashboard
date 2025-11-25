# kycform/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from .models import KycUserInfo, KycAgentInfo, KycPolicy, KycAdmin

# ============================================================================
# UTILITIES
# ============================================================================

def normalize_status(value):
    """Normalize KYC status into consistent format."""
    if not value:
        return ""
    return str(value).strip().upper().replace(" ", "_")


def redirect_login_tab(user_type):
    """Send user to correct login tab."""
    if user_type == "agent":
        return redirect("/auth/agent/?tab=agent")
    return redirect("/auth/policy/?tab=policy")


def missing_fields(*fields):
    """Check if any required field is missing."""
    return not all(fields)


# ============================================================================
# LOGIN VIEWS (POLICY & AGENT)
# ============================================================================

def policyholder_login(request):
    if request.method == "GET":
        return render(request, "kyc_auth.html", {"active_tab": "policy"})

    policy_no = request.POST.get("policy_no")
    password = request.POST.get("password")

    if missing_fields(policy_no, password):
        messages.error(request, "Policy number and password are required.", extra_tags="error")
        return redirect_login_tab("policy")

    try:
        policy = KycPolicy.objects.get(policy_number__iexact=policy_no)
        user = KycUserInfo.objects.get(user_id=policy.user_id)
    except (KycPolicy.DoesNotExist, KycUserInfo.DoesNotExist):
        messages.error(request, "Invalid policy number or user not found.", extra_tags="error")
        return redirect_login_tab("policy")

    if password != (user.password or ""):
        messages.error(request, "Incorrect password!", extra_tags="error")
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
        messages.error(request, "Agent code and password are required.", extra_tags="error")
        return redirect_login_tab("agent")

    try:
        agent = KycAgentInfo.objects.get(agent_code__iexact=agent_code)
    except KycAgentInfo.DoesNotExist:
        messages.error(request, "Agent code not found!", extra_tags="error")
        return redirect_login_tab("agent")

    if password != (agent.password or ""):
        messages.error(request, "Incorrect password!", extra_tags="error")
        return redirect_login_tab("agent")

    return redirect(f"/agent-dashboard/?agent_code={agent_code}")


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