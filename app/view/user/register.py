from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from app.models import RoomType, Image, Guest, Service, Reservation, Room, ReservationRoom,Employee,Branch ,ServiceUsage, Bill, Feedback
from django.contrib.auth.models import User
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.db import transaction
from django.views.decorators.csrf import csrf_protect
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        full_name = request.POST.get('full_name', '')
        phone_number = request.POST.get('phone_number', '')
        address = request.POST.get('address', '')
        id_card = request.POST.get('id_card', '')  # Lấy giá trị id_card

        # Kiểm tra mật khẩu
        if password != confirm_password:
            return render(request, 'user/register.html', {'error': 'Passwords do not match'})

        # Kiểm tra xem username đã tồn tại chưa
        if User.objects.filter(username=username).exists():
            return render(request, 'user/register.html', {'error': 'Username already exists'})

        # Kiểm tra xem email đã tồn tại chưa
        if User.objects.filter(email=email).exists():
            return render(request, 'user/register.html', {'error': 'Email already exists'})

        # Lưu người dùng mới vào bảng auth_user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # Lưu thông tin khách hàng vào bảng Guest với id_card
        guest = Guest(full_name=full_name, phone_number=phone_number, email=email, address=address, id_card=id_card, user_id=user.id)
        guest.save()

        # Chuyển hướng về trang login (hoặc bất kỳ trang nào khác)
        messages.success(request, 'Account created successfully. Please login!')
        return redirect('login')

    return render(request, 'user/register.html')