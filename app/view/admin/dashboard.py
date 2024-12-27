from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView
from app.models import Employee, Branch, AuthUser, Guest, RoomType, Image, Room, Service, Reservation, Feedback, Bill
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.db import transaction
from django.core.paginator import Paginator
from datetime import datetime, timedelta

@login_required 
def dashboard(request):
    # Revenue statistics
    total_revenue = Bill.objects.filter(paid_status='paid').aggregate(
        total=Sum('total_amount'))['total'] or 0
    
    # Get today's date and last month's date
    today = timezone.now()
    last_month = today - timedelta(days=30)
    
    # Monthly revenue
    monthly_revenue = Bill.objects.filter(
        paid_status='paid',
        date_issued__gte=last_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Reservation statistics
    total_reservations = Reservation.objects.count()
    pending_reservations = Reservation.objects.filter(status='pending').count()
    active_reservations = Reservation.objects.filter(status='checked_in').count()
    completed_reservations = Reservation.objects.filter(status='checked_out').count()
    
    # Room statistics
    total_rooms = Room.objects.count()
    available_rooms = Room.objects.filter(status='available').count()
    occupied_rooms = Room.objects.filter(status='occupied').count()
    maintenance_rooms = Room.objects.filter(status='maintenance').count()
    
    # Guest and employee counts
    total_guests = Guest.objects.count()
    total_employees = Employee.objects.count()
    
    # Recent reservations with guest info and bill details
    recent_reservations = Reservation.objects.select_related(
        'guest'
    ).prefetch_related(
        'bill_set'
    ).order_by('-book_date')[:5]

    # Room type occupancy with pre-calculated rates
    room_type_stats = []
    for stat in Room.objects.values('room_type__name').annotate(
        total=Count('id'),
        occupied=Count('id', filter=Q(status='occupied'))
    ):
        occupancy_rate = (stat['occupied'] / stat['total'] * 100) if stat['total'] > 0 else 0
        room_type_stats.append({
            'name': stat['room_type__name'],
            'total': stat['total'],
            'occupied': stat['occupied'],
            'occupancy_rate': occupancy_rate
        })

    context = {
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'total_reservations': total_reservations,
        'pending_reservations': pending_reservations,
        'active_reservations': active_reservations,
        'completed_reservations': completed_reservations,
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupied_rooms': occupied_rooms,
        'maintenance_rooms': maintenance_rooms,
        'total_guests': total_guests,
        'total_employees': total_employees,
        'recent_reservations': recent_reservations,
        'room_type_stats': room_type_stats,
        'occupancy_rate': (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0,
        'active': 'dashboard'
    }
    
    return render(request, 'admin/dashboard.html', context)