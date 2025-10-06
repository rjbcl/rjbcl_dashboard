from django.shortcuts import render

# Create your views here.
def register_agent(request):
    return render(request, 'agent/register.html')