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

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Xác thực người dùng
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)

            # Kiểm tra nếu người dùng là admin (is_superuser)
            if user.is_superuser:
                role = 'Admin'
            # Kiểm tra nếu người dùng là employee (is_staff) nhưng không phải admin
            elif user.is_staff:
                role = 'Employee'
            else:
                # Kiểm tra nếu người dùng là khách hàng trong bảng Guest dựa vào user_id
                guest = Guest.objects.filter(user_id=user.id).first()  # Dùng user_id thay vì email
                if guest:
                    role = 'Guest'
                else:
                    role = 'Unknown'  # Nếu không phải là employee hay guest

            # Lưu thông tin role vào session
            request.session['role'] = role
            print(f"User {user.username} logged in as {role}")

            # Redirect người dùng đến trang phù hợp tùy theo role
            if role in ['Admin', 'Employee']:
                return redirect('base_admin')  # Trang base_admin dành cho admin và employee
            else:
                return redirect('index')  # Trang index dành cho guest

        else:
            print(f"DEBUG: User {username} authentication failed.")
            messages.error(request, 'Invalid username or password')

    return render(request, 'user/login.html')





def logout_view(request):
    logout(request)
    return redirect('login')