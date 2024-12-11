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


# Đảm bảo rằng chỉ người dùng đã đăng nhập mới có thể truy cập trang quản trị
@login_required
def base_admin(request):
    return render(request, 'admin/base_admin.html')