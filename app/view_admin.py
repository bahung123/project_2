from django.shortcuts import render
from django.http import HttpResponse

def base_admin(request):
    return render(request, 'admin/base_admin.html')
