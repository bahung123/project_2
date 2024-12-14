from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from app.models import Reservation
from datetime import datetime
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect

@login_required
def reservation_list(request):
    try:
        # Get search and filter parameters
        search_query = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '').strip()
        
        # Base queryset with newest first
        reservations = Reservation.objects.all().order_by('-book_date', '-id')
        
        # Apply search filter
        if search_query:
            reservations = reservations.filter(
            Q(guest__full_name__icontains=search_query) |
            Q(guest__email__icontains=search_query) |
            Q(guest__phone_number__icontains=search_query) |
            Q(reservationroom__room__room_number__icontains=search_query) 
            ).distinct()
        
        # Apply status filter
        if status_filter:
            reservations = reservations.filter(status=status_filter)
        
        # Pagination
        page_size = 10  # Items per page
        paginator = Paginator(reservations, page_size)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Context data
        context = {
            'reservations': page_obj,
            'page_obj': page_obj,
            'search_query': search_query,
            'status': status_filter,
            'active': 'reservations',
            'status_choices': [
                ('pending', 'Pending'),
                ('confirmed', 'Confirmed'),
                ('cancelled', 'Cancelled'),
                ('checked_in', 'Checked In'),
                ('checked_out', 'Checked Out'),
            ],
            'total_reservations': reservations.count(),
            'filtered_count': page_obj.paginator.count,
            'title': 'Reservation List'
        }
        
        return render(request, 'admin/reservation_list.html', context)
        
    except Exception as e:
        print(f"Error in reservation_list: {str(e)}")  # Debug print
        messages.error(request, f'Error loading reservations: {str(e)}')
        return render(request, 'admin/reservation_list.html', {
            'active': 'reservations',
            'error': str(e)
        })

@login_required
def reservation_delete(request, reservation_id):
    try:
        if request.method == 'POST':
            reservation = get_object_or_404(Reservation, id=reservation_id)
            reservation.delete()
            messages.success(request, 'Reservation deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting reservation: {str(e)}')
    return redirect('reservation_list')

@login_required
def reservation_edit(request, reservation_id):
    try:
        reservation = get_object_or_404(Reservation, id=reservation_id)
        if request.method == 'POST':
            new_status = request.POST.get('status')
            if new_status:
                reservation.status = new_status
                reservation.save()
                messages.success(request, 'Reservation status updated successfully.')
            return redirect('reservation_list')
    except Exception as e:
        messages.error(request, f'Error updating reservation: {str(e)}')
    return redirect('reservation_list')

@login_required
def reservation_detail(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    context = {
        'reservation': reservation,
        'active': 'reservations'
    }
    return render(request, 'admin/reservation_detail.html', context)