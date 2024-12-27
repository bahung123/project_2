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
def booking_history(request):
    try:
        # Get guest by user_id
        guest = Guest.objects.get(user_id=request.user.id)
        
        # Get status filter
        status = request.GET.get('status', '')
        
        # Get reservations
        reservations = Reservation.objects.filter(
            guest=guest
        ).order_by('-book_date')
        
        if status:
            reservations = reservations.filter(status=status)
        
        # Get related data
        for reservation in reservations:
            reservation.rooms = ReservationRoom.objects.filter(
                reservation=reservation
            ).select_related('room', 'room__room_type')
            
            reservation.bill = Bill.objects.filter(
                reservation=reservation
            ).first()
            
            reservation.services = ServiceUsage.objects.filter(
                reservation=reservation
            ).select_related('service')

            # Check if feedback exists
            reservation.has_feedback = Feedback.objects.filter(
                reservation=reservation
            ).exists()
        
        context = {
            'reservations': reservations,
            'status_filter': status
        }
        
        return render(request, 'user/booking_history.html', context)

    except Exception as e:
        print(f"Booking history error: {str(e)}")
        messages.error(request, "Error loading booking history")
        return redirect('index')