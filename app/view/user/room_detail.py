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

def room_detail_user(request, room_type_id):
    room_type = get_object_or_404(RoomType, pk=room_type_id)
    room_type.images = Image.objects.filter(room_type_id=room_type.id)
    
    context = {
        'room_type': room_type
    }
    return render(request, 'user/room_detail.html', context)