from django.shortcuts import render


def login_policyholder(request):
    return render(request, 'policyholder/login.html')


def forget_password(request):
    return render(request, 'policyholder/forget_password.html')

def register_policy(request):
    return render(request, 'policyholder/register_policy.html')