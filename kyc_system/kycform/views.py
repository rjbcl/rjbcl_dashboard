from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from .models import KycUserInfo, KycAgentInfo, KycPolicy


# ============================================================
#  UTIL: BUILD URL WITH QUERY PARAMETERS
# ============================================================

def url_with_query(name, **params):
    base = reverse(name)
    if not params:
        return base
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{base}?{query}"


# ============================================================
#  POLICYHOLDER LOGIN
# ============================================================

def policyholder_login(request):

    if request.method == "GET":
        return render(request, "kyc_auth.html", {"active_tab": "policy"})

    policy_no = request.POST.get("policy_no")
    password = request.POST.get("password")

    print("POLICY ENTERED:", repr(policy_no))
    print("ALL DB POLICIES:", list(KycPolicy.objects.values_list("policy_number", flat=True)))

    try:
        policy = KycPolicy.objects.get(policy_number__iexact=policy_no)

        print("policy.user_id =", policy.user_id)
        print("ALL USER IDS:", list(KycUserInfo.objects.values_list("user_id", flat=True)))

    except KycPolicy.DoesNotExist:
        print("DEBUG: Policy not found in DB")
        messages.error(request, "Policy number not found!", extra_tags="error")
        return redirect("/auth/policy/")

    try:
        user = KycUserInfo.objects.get(user_id=policy.user_id)
    except KycUserInfo.DoesNotExist:
        print("DEBUG: User record NOT FOUND for policy.user_id =", policy.user_id)
        messages.error(request, "Customer record missing for this policy!", extra_tags="error")
        return redirect("/auth/policy/")

    # PASSWORD CHECK
    expected_password = user.dob.strftime("%Y%m%d")
    if password != expected_password:
        messages.error(request, "Incorrect password!", extra_tags="error")
        return redirect("/auth/policy/")

    # =============== FIX: Normalize STATUS ==================
    kyc_status = (user.kyc_status or "").upper().replace(" ", "_")
    print("DEBUG: NORMALIZED KYC STATUS =", kyc_status)

    # =============== CORRECT ROUTING ========================
    if kyc_status in ["NOT_INITIATED", "INCOMPLETE", "REJECTED"]:
        return redirect(f"/kyc-form/?policy_no={policy_no}")

    if kyc_status in ["PENDING", "VERIFIED"]:
        return redirect(f"/dashboard/?policy_no={policy_no}")

    # Default fallback
    return redirect(f"/kyc-form/?policy_no={policy_no}")




# ============================================================
#  AGENT LOGIN
# ============================================================

def agent_login(request):

    if request.method == "GET":
        return render(request, "kyc_auth.html", {"active_tab": "agent"})

    agent_code = request.POST.get("agent_code")
    password = request.POST.get("password")

    if not agent_code or not password:
        messages.error(request, "Both fields are required.", extra_tags="error")
        return redirect("kyc:agent_login")

    try:
        agent = KycAgentInfo.objects.get(agent_code=agent_code)

        expected_password = agent.dob.strftime("%Y%m%d")

        if password != expected_password:
            messages.error(request, "Incorrect password!", extra_tags="error")
            return redirect("kyc:agent_login")

        return redirect(url_with_query("kyc:agent_dashboard", agent_code=agent_code))

    except KycAgentInfo.DoesNotExist:
        messages.error(request, "Agent code not found!", extra_tags="error")
        return redirect("kyc:agent_login")


# ============================================================
#  POLICYHOLDER REGISTRATION
# ============================================================

def policyholder_register_view(request):

    if request.method == "GET":
        return render(request, "register.html")

    # FIXED: Your register form uses name="policy_number"
    policy_no = request.POST.get("policy_number")
    email = request.POST.get("email")
    mobile = request.POST.get("mobile")

    if not policy_no or not email or not mobile:
        messages.error(request, "All fields are required.", extra_tags="error")
        return redirect("kyc:policy_register")

    try:
        policy = KycPolicy.objects.get(policy_number=policy_no)
        user = KycUserInfo.objects.get(user_id=policy.user_id)

        # ----------------------------------------------------
        # UPDATE EMAIL IF NULL
        # ----------------------------------------------------
        if not user.user_email:
            user.user_email = email
        elif user.user_email.lower() != email.lower():
            messages.error(request, "Email does not match our records!", extra_tags="error")
            return redirect("kyc:policy_register")

        # ----------------------------------------------------
        # UPDATE MOBILE IF NULL
        # ----------------------------------------------------
        if not user.phone_number:
            user.phone_number = mobile
        elif user.phone_number != mobile:
            messages.error(request, "Mobile number does not match our records!", extra_tags="error")
            return redirect("kyc:policy_register")

        # ----------------------------------------------------
        # SET PASSWORD = DOB
        # ----------------------------------------------------
        user.password = user.dob.strftime("%Y%m%d")
        user.save()

        messages.success(
            request,
            "Password has been sent to your mobile number and email. Please login.",
            extra_tags="success"
        )

        return redirect("/auth/policy/?tab=policy")

    except (KycPolicy.DoesNotExist, KycUserInfo.DoesNotExist):
        messages.error(request, "Policy not found!", extra_tags="error")
        return redirect("kyc:policy_register")


# ============================================================
#  AGENT REGISTRATION
# ============================================================

def agent_register_view(request):

    if request.method == "GET":
        return render(request, "agent_register.html")

    agent_code = request.POST.get("agent_code")
    first_name = request.POST.get("first_name")
    last_name = request.POST.get("last_name")
    phone = request.POST.get("phone_number")
    email = request.POST.get("email")

    if not all([agent_code, first_name, last_name, phone, email]):
        messages.error(request, "All fields are required.", extra_tags="error")
        return redirect("kyc:agent_register")

    try:
        agent = KycAgentInfo.objects.get(agent_code=agent_code)

        # VALIDATE FIELDS
        if agent.first_name.lower() != first_name.lower():
            messages.error(request, "First name does not match!", extra_tags="error")
            return redirect("kyc:agent_register")

        if agent.last_name.lower() != last_name.lower():
            messages.error(request, "Last name does not match!", extra_tags="error")
            return redirect("kyc:agent_register")

        if agent.phone_number != phone:
            messages.error(request, "Phone number does not match!", extra_tags="error")
            return redirect("kyc:agent_register")

        if agent.email.lower() != email.lower():
            messages.error(request, "Email does not match our records!", extra_tags="error")
            return redirect("kyc:agent_register")

        # SET PASSWORD
        agent.password = agent.dob.strftime("%Y%m%d")
        agent.save()

        messages.success(
            request,
            "Password has been sent to your mobile number and email. Please login.",
            extra_tags="success"
        )

        return redirect("/auth/agent/?tab=agent")

    except KycAgentInfo.DoesNotExist:
        messages.error(request, "Agent code not found!", extra_tags="error")
        return redirect("kyc:agent_register")


# ============================================================
#  KYC FORM + DASHBOARD VIEWS
# ============================================================

def kyc_form_view(request):
    return render(request, "kyc_form_update.html", {"policy_no": request.GET.get("policy_no")})


def dashboard_view(request):
    return render(request, "dashboard.html", {"policy_no": request.GET.get("policy_no")})


def agent_dashboard_view(request):
    return render(request, "dashboard.html", {"agent_code": request.GET.get("agent_code")})

def kyc_form_submit(request):
    if request.method != "POST":
        messages.error(request, "Invalid request!", extra_tags="error")
        return redirect("/")

    policy_no = request.POST.get("policy_no")

    # TODO: Save form data later

    messages.success(request, "Your KYC form has been submitted.", extra_tags="success")
    return redirect(f"/dashboard/?policy_no={policy_no}")
