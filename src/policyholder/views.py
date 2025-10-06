from django.shortcuts import render

def register_policyholder(request):
    return render(request, 'policyholder/register.html')