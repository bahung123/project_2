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
    period = request.GET.get('period', 'month')
    current_year = timezone.now().year
    year = int(request.GET.get('year', current_year))
    branch_id = request.GET.get('branch', '')

    # Get all branches for dropdown
    branches = Branch.objects.all()

    # Base query for bills
    bills_query = Bill.objects.filter(paid_status='paid')

    # Add branch filter using distinct() to avoid duplicates
    if branch_id:
        bills_query = bills_query.filter(
            reservation__reservationroom__room__branch_id=branch_id
        ).distinct()

    # Revenue statistics
    total_revenue = bills_query.aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    # Monthly revenue
    monthly_revenue = bills_query.filter(
        date_issued__year=timezone.now().year,
        date_issued__month=timezone.now().month
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    # Chart data processing
    labels = []
    values = []
    
    if period == 'month':
        months_data = bills_query.filter(
            date_issued__year=year
        ).extra(
            select={'month': 'MONTH(date_issued)'}
        ).values('month').annotate(
            total=Sum('total_amount')
        ).order_by('month')
        
        monthly_totals = {i: 0 for i in range(1, 13)}
        for data in months_data:
            monthly_totals[data['month']] = float(data['total'])
        
        for month in range(1, 13):
            month_name = datetime(2000, month, 1).strftime('%B')
            labels.append(month_name)
            values.append(monthly_totals[month])

    else:  # year
        for y in range(year-4, year+1):
            year_total = bills_query.filter(
                date_issued__year=y
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            labels.append(str(y))
            values.append(float(year_total))

    # Revenue statistics with distinct
    total_revenue = bills_query.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Get today's date and last month's date
    today = timezone.now()
    last_month = today - timedelta(days=30)
    
    # Monthly revenue with distinct
    monthly_revenue = bills_query.filter(
        date_issued__gte=last_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Define reservation_filter
    reservation_filter = {}

    # Define room_filter
    room_filter = {}
    
    # Reservation statistics using reservation_filter
    total_reservations = Reservation.objects.filter(**reservation_filter).count()
    pending_reservations = Reservation.objects.filter(status='pending', **reservation_filter).count()
    active_reservations = Reservation.objects.filter(status='checked_in', **reservation_filter).count()
    completed_reservations = Reservation.objects.filter(status='checked_out', **reservation_filter).count()
    
    # Room statistics using room_filter
    total_rooms = Room.objects.filter(**room_filter).count()
    available_rooms = Room.objects.filter(status='available', **room_filter).count()
    occupied_rooms = Room.objects.filter(status='occupied', **room_filter).count()
    maintenance_rooms = Room.objects.filter(status='maintenance', **room_filter).count()
    
    # Guest and employee counts
    total_guests = Guest.objects.count()
    total_employees = Employee.objects.count()
    
    # Room type occupancy with pre-calculated rates
    room_type_stats = []
    for stat in Room.objects.filter(**room_filter).values('room_type__name').annotate(
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
        'branches': branches,  # Add branches to context
        'selected_branch': branch_id,
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
        'room_type_stats': room_type_stats,
        'occupancy_rate': (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0,
        'active': 'dashboard',
        'chart_labels': labels,
        'chart_values': values,
        'selected_period': period,
        'selected_year': year,
        'years': range(current_year-4, current_year+1),
    }
    
    return render(request, 'admin/dashboard.html', context)