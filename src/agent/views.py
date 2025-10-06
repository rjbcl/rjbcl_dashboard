from django.shortcuts import render

# Create your views here.
def register_agent(request):
    return render(request, 'agent/register_agent.html')

def login_agent(request):
    return render(request, 'agent/login.html')

def forget_password(request):
    return render(request, 'agent/forget_password.html')


