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

def contact(request):
    context = {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    }
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Validate form data
        if not all([name, email, subject, message]):
            messages.error(request, 'Please fill in all fields.')
            return redirect('contact')
        
        try:
            # Send email notification
            send_mail(
                subject=f"Contact Form: {subject}",
                message=f"From: {name}\nEmail: {email}\n\nMessage:\n{message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Thank you for your message! We will contact you soon.')
            return redirect('contact')
            
        except Exception as e:
            messages.error(request, 'Sorry, there was an error sending your message. Please try again later.')
            return redirect('contact')
            
    return render(request, 'user/contact.html', context)