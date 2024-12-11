from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView
from app.models import Employee, Branch, AuthUser, Guest, RoomType, Image, Room, Service
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator

@login_required
def dashboard(request):
    context = {
        'total_revenue': 50000,
        'total_reservations': 120,
        'total_rooms': 30,
        'total_employees': 15,
        'active': 'dashboard',  # Để sidebar hiển thị đúng menu đang active
    }
    return render(request, 'admin/dashboard.html', context)