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

@login_required
def account_info(request):
    user = request.user
    try:
        guest = Guest.objects.get(user_id=user.id)
    except Guest.DoesNotExist:
        guest = None

    return render(request, 'include/account_info.html', {
        'user': user,
        'guest': guest,
    })


@login_required
def update_account_info(request):
    if request.method == 'POST':
        user = request.user
        guest = Guest.objects.get(user_id=user.id)

        # Cập nhật thông tin của người dùng
        guest.full_name = request.POST['full_name']
        user.email = request.POST['email']
        guest.phone_number = request.POST['phone_number']
        guest.address = request.POST['address']
        guest.id_card = request.POST['id_card']  # Cập nhật id_card từ form

        # Lưu thông tin
        user.save()
        guest.save()

        messages.success(request, 'Your account information has been updated successfully.')
        return redirect('account_info')

    return render(request, 'account_info.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        user = request.user
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_new_password = request.POST['confirm_new_password']

        if user.check_password(old_password):
            if new_password == confirm_new_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Your password has been changed successfully.')
                return redirect('login')
            else:
                messages.error(request, 'New passwords do not match.')
        else:
            messages.error(request, 'Incorrect old password.')
    return redirect('account_info')