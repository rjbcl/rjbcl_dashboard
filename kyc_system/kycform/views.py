from django.shortcuts import render, redirect

def auth_view(request):
    return render(request, 'kyc_auth.html')

def kyc_form_view(request):
    if request.method == "POST":
        policy_no = request.POST.get("policy_no")
        print("DEBUG: KYC POST received policy:", policy_no)

        return redirect(f"/dashboard/?policy_no={policy_no}")

    return render(request, "kyc_form_update.html")


def dashboard_view(request):
    policy_no = request.GET.get("policy_no")
    return render(request, "dashboard.html", {"policy_no": policy_no})
