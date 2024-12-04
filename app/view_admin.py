from django.shortcuts import render
from django.http import HttpResponse
from django.urls import path
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.contrib.admin import AdminSite
from .models import Bill, Room, Reservation, Service, Employee
from django.db import models


def base_admin(request):
    return render(request, 'admin/base_admin.html')

# Custom admin site để hiển thị dashboard
class CustomAdminSite(AdminSite):
    site_header = "Hotel Management Dashboard"
    site_title = "Hotel Admin"
    index_title = "Welcome to Hotel Dashboard"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        # Fetch data từ database
        total_revenue = Bill.objects.filter(paid_status='paid').aggregate(total=models.Sum('total_amount'))['total'] or 0
        total_reservations = Reservation.objects.count()
        total_rooms = Room.objects.count()
        total_services = Service.objects.count()
        total_employees = Employee.objects.count()

        context = {
            'total_revenue': total_revenue,
            'total_reservations': total_reservations,
            'total_rooms': total_rooms,
            'total_services': total_services,
            'total_employees': total_employees,
        }
        return TemplateResponse(request, 'admin/dashboard.html', context)

# Khởi tạo admin site mới
custom_admin_site = CustomAdminSite(name='custom_admin')
