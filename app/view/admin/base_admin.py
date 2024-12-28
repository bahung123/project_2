from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView
from app.models import Employee, Branch, AuthUser, Guest, RoomType, Image, Room, Service ,Reservation
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator


# Đảm bảo rằng chỉ người dùng đã đăng nhập mới có thể truy cập trang quản trị
@login_required
def base_admin(request):
    # Get statistics for dashboard
    context = {
        'active' : 'base_admin',
        'total_rooms': Room.objects.count(),
        'active_reservations': Reservation.objects.filter(status='active').count(),
        'total_guests': Guest.objects.count(),
        'total_employees': Employee.objects.count(),
        'recent_reservations': Reservation.objects.order_by('-book_date')[:5],
        'available_rooms': Room.objects.filter(status='available').count(),
    }
    return render(request, 'admin/base_admin.html', context)