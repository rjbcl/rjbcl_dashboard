from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import KycUserInfo, KycAgentInfo


# ============================
# POLICYHOLDER LOGIN
# ============================
def policyholder_login(request):
    if request.method == "GET":
        return render(request, "kyc_auth.html", {
            "error": None,
            "agent_error": None,
            "active_tab": "policy"
        })

    policy_no = request.POST.get("policy_no")
    password = request.POST.get("password")

    try:
        user = KycUserInfo.objects.get(policy_number=policy_no)

        if user.password == password:
            return redirect(f"/kyc-form/?policy_no={policy_no}")

        return render(request, "kyc_auth.html", {
            "error": "Incorrect password for policyholder!",
            "agent_error": None,
            "active_tab": "policy"
        })

    except KycUserInfo.DoesNotExist:
        return render(request, "kyc_auth.html", {
            "error": "Policy number not found!",
            "agent_error": None,
            "active_tab": "policy"
        })



# ============================
# AGENT LOGIN
# ============================
def agent_login(request):
    if request.method == "GET":
        return render(request, "kyc_auth.html", {
            "error": None,
            "agent_error": None,
            "active_tab": "agent"
        })

    agent_code = request.POST.get("agent_code")
    password = request.POST.get("password")

    try:
        agent = KycAgentInfo.objects.get(agent_code=agent_code)

        if agent.password == password:
            return redirect("/agent-dashboard/")

        return render(request, "kyc_auth.html", {
            "error": None,
            "agent_error": "Incorrect agent password!",
            "active_tab": "agent"
        })

    except KycAgentInfo.DoesNotExist:
        return render(request, "kyc_auth.html", {
            "error": None,
            "agent_error": "Agent code not found!",
            "active_tab": "agent"
        })



# ============================
# POLICYHOLDER REGISTRATION
# ============================
def policyholder_register_view(request):
    if request.method == "POST":

        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")
        policy_number = request.POST.get("policy_number")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        full_name = f"{first_name} {last_name}"

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, "register.html")

        if KycUserInfo.objects.filter(policy_number=policy_number).exists():
            messages.error(request, "This policy number is already registered!")
            return render(request, "register.html")

        KycUserInfo.objects.create(
            policy_number=policy_number,
            Name=full_name,
            User_email=email,
            Phone_number=mobile,
            password=password
        )

        messages.success(request, "Account created successfully! Please login.")
        return redirect("/auth/policy/")

    return render(request, "register.html")


# ============================
# AGENT REGISTRATION
# ============================
def agent_register_view(request):
    if request.method == "POST":
        agent_code = request.POST.get("agent_code")
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        dob = request.POST.get("dob")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, "agent_register.html")

        if KycAgentInfo.objects.filter(agent_code=agent_code).exists():
            messages.error(request, "Agent Code already exists!")
            return render(request, "agent_register.html")

        KycAgentInfo.objects.create(
            agent_code=agent_code,
            name=name,
            phone_number=phone,
            DOB=dob,
            password=password
        )

        messages.success(request, "Agent account created successfully!")
        return redirect("/auth/agent/")

    return render(request, "agent_register.html")


# ============================
# KYC FORM VIEW
# ============================
def kyc_form_view(request):
    policy_no = request.GET.get("policy_no")
    return render(request, "kyc_form_update.html", {"policy_no": policy_no})


# ============================
# POLICYHOLDER DASHBOARD
# ============================
def dashboard_view(request):
    policy_no = request.GET.get("policy_no")
    return render(request, "dashboard.html", {"policy_no": policy_no})


# ============================
# AGENT DASHBOARD
# ============================
def agent_dashboard_view(request):
    agent_code = request.GET.get("agent_code")
    return HttpResponse(f"Welcome Agent {agent_code} — Dashboard coming soon!")
