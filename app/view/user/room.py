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

def room(request):
    # Lấy tất cả room types
    room_types = RoomType.objects.all().prefetch_related('room_set')
    
    # Xử lý cho mỗi room type
    for room_type in room_types:
        # Lấy ảnh đầu tiên của room type
        room_type.main_image = Image.objects.filter(room_type_id=room_type.id).first()
        # Đếm số phòng còn trống
        room_type.available_count = room_type.room_set.filter(status='available').count()
        # Xử lý amenities từ description
        room_type.amenities = [
            amenity.strip() 
            for amenity in room_type.description.split(',')
        ] if room_type.description else []
    
    context = {
        'room_types': room_types,
    }
    return render(request, 'user/room.html', context)