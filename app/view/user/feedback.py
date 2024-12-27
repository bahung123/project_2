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
def feedback_view(request, reservation_id):
    try:
        guest = Guest.objects.get(user_id=request.user.id)
        
        reservation = get_object_or_404(
            Reservation.objects.select_related('guest'), 
            id=reservation_id,
            guest=guest,
            status='checked_out'
        )

        # Get existing feedback if any
        feedback = Feedback.objects.filter(reservation=reservation).first()

        if request.method == 'POST':
            rating = request.POST.get('rating')
            comment = request.POST.get('comment')

            if not rating or not comment:
                messages.error(request, 'Please provide both rating and comment')
                return render(request, 'user/feedback.html', {
                    'reservation': reservation,
                    'feedback': feedback
                })

            if feedback:
                # Update existing feedback
                feedback.rating = rating
                feedback.comment = comment
                feedback.save()
                messages.success(request, 'Feedback updated successfully!')
            else:
                # Create new feedback with created_at
                Feedback.objects.create(
                    guest=guest,
                    reservation=reservation,
                    rating=rating,
                    comment=comment,
                    created_at=now()  # Add this line to set created_at
                )
                messages.success(request, 'Thank you for your feedback!')

            return redirect('booking_history')

        return render(request, 'user/feedback.html', {
            'reservation': reservation,
            'feedback': feedback
        })

    except Exception as e:
        print(f"Feedback error: {str(e)}")
        messages.error(request, 'Unable to process feedback')
        return redirect('booking_history')