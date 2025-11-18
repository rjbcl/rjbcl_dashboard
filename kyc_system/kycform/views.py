from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Policy
from .models import KycUserInfo, KycAgentInfo


def auth_view(request):
    # First load the login page
    if request.method == "GET":
        return render(request, 'kyc_auth.html')

    # POST login request
    if request.method == "POST":
        policy_no = request.POST.get("policy_no")
        password = request.POST.get("password")  # DOB (YYYY-MM-DD)

        try:
            policy = Policy.objects.select_related("customer").get(policy_no=policy_no)
            customer = policy.customer

            # Validate DOB (password)
            if str(customer.dob) == password:
                # Login success → redirect to KYC form
                return redirect(f"/kyc-form/?policy_no={policy_no}")
            else:
                return render(request, "kyc_auth.html", {
                    "error": "Invalid password! Please use DOB (YYYY-MM-DD)."
                })
        except Policy.DoesNotExist:
            return render(request, "kyc_auth.html", {
                "error": "Policy number not found!"
            })
        
def kyc_form_view(request):
    policy_no = request.GET.get("policy_no")

    if request.method == "POST":
        print("DEBUG: KYC POST received policy:", policy_no)
        return redirect(f"/dashboard/?policy_no={policy_no}")

    return render(request, "kyc_form_update.html", {"policy_no": policy_no})

def dashboard_view(request):
    policy_no = request.GET.get("policy_no")
    return render(request, "dashboard.html", {"policy_no": policy_no})


def policyholder_login(request):
    if request.method == "POST":
        policy_no = request.POST.get("policy_no")
        password = request.POST.get("password")

        try:
            user = KycUserInfo.objects.get(policy_number=policy_no)

            if user.password == password:
                # SUCCESS → redirect to KYC form
                return redirect(f"/kyc-form/?policy_no={policy_no}")

            return render(request, "kyc_auth.html", {
                "error": "Incorrect password for policyholder!"
            })

        except KycUserInfo.DoesNotExist:
            return render(request, "kyc_auth.html", {
                "error": "Policy number not found!"
            })


# -------------------------
# AGENT LOGIN
# -------------------------
def agent_login(request):
    if request.method == "POST":
        agent_code = request.POST.get("agent_code")
        password = request.POST.get("password")

        try:
            agent = KycAgentInfo.objects.get(agent_code=agent_code)

            if agent.password == password:
                # SUCCESS → redirect to agent dashboard
                return redirect(f"/agent-dashboard/?agent_code={agent_code}")

            return render(request, "kyc_auth.html", {
                "error": "Incorrect password for agent!"
            })

        except KycAgentInfo.DoesNotExist:
            return render(request, "kyc_auth.html", {
                "error": "Agent code not found!"
            })

def register_view(request):
    return render(request, "register.html")


def agent_dashboard_view(request):
    agent_code = request.GET.get("agent_code")
    return HttpResponse(f"Welcome Agent {agent_code} — Dashboard coming soon!")
