from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Max
from django.contrib.auth.decorators import login_required
from app.models import ServiceUsage, Reservation, Room, Service, Bill
from decimal import Decimal
from .reservation import calculate_total_amount


@login_required
def service_usage_list(request):
    search_query = request.GET.get('search', '')
    
    # Handle delete action from main list
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        usage_id = request.POST.get('usage_id')
        try:
            service_usage = get_object_or_404(ServiceUsage, id=usage_id)
            # Check if reservation is checked in
            if service_usage.reservation.status != 'checked_in':
                reservation = service_usage.reservation
                reservation_id = reservation.id
                
                # Delete service usage
                ServiceUsage.objects.filter(reservation_id=reservation_id).delete()
                
                # Update bill total
                bill = Bill.objects.filter(reservation=reservation).first()
                if bill:
                    # Recalculate amounts using imported function
                    amounts = calculate_total_amount(reservation)
                    bill.total_amount = amounts['total_amount']
                    bill.save()
                
                messages.success(request, 'Service usage deleted successfully')
            else:
                messages.error(request, 'Cannot delete services for checked-in reservations')
        except Exception as e:
            messages.error(request, f'Error deleting service usage: {str(e)}')
    
    # Get unique reservations with their latest service usage
    if search_query:
        service_usages = ServiceUsage.objects.select_related(
            'reservation__guest', 'service', 'reservation'
        ).filter(
            Q(reservation__id__icontains=search_query) |
            Q(reservation__guest__phone_number__icontains=search_query) |
            Q(reservation__guest__full_name__icontains=search_query)
        ).values('reservation_id').annotate(
            last_id=Max('id')
        ).values_list('last_id', flat=True)
    else:
        service_usages = ServiceUsage.objects.select_related(
            'reservation__guest', 'service', 'reservation'
        ).values('reservation_id').annotate(
            last_id=Max('id')
        ).values_list('last_id', flat=True)
    
    service_usages = ServiceUsage.objects.select_related(
        'reservation__guest', 'service', 'reservation'
    ).filter(id__in=service_usages)
    
    paginator = Paginator(service_usages, 10)
    page = request.GET.get('page')
    service_usages = paginator.get_page(page)
    
    context = {
        'active': 'service_usage',
        'service_usages': service_usages,
        'search_query': search_query,
        'action': 'list'
    }
    return render(request, 'admin/service_usage_list.html', context)

@login_required 
def service_usage_detail(request, usage_id):
    action = request.GET.get('action', 'view')
    
    if usage_id == 0:
        # Get all confirmed and checked-in reservations
        available_reservations = Reservation.objects.filter(
            status__in=['confirmed', 'checked_in']
        ).exclude(
            status='checked_out'
        ).select_related('guest').order_by('-id')

        context = {
            'action': 'add',
            'available_reservations': available_reservations,
            'services': Service.objects.all()
        }
        
        if request.method == 'POST':
            try:
                reservation = get_object_or_404(Reservation, id=request.POST.get('reservation'))
                
                # Allow adding services if reservation is confirmed or checked in
                if reservation.status in ['confirmed', 'checked_in']:
                    # Get room from ReservationRoom
                    reservation_room = reservation.reservationroom_set.first()
                    if not reservation_room:
                        raise Exception("No room assigned to this reservation")
                    
                    service = Service.objects.get(id=request.POST.get('service'))
                    quantity = int(request.POST.get('quantity'))
                    date_used = request.POST.get('date_used')
                    
                    # Calculate total
                    total = Decimal(str(service.price)) * Decimal(str(quantity))
                    
                    # Create new service usage
                    ServiceUsage.objects.create(
                        reservation=reservation,
                        room_id=reservation_room.room.id,
                        service=service,
                        quantity=quantity,
                        date_used=date_used,
                        total=total
                    )
                    messages.success(request, 'Service usage added successfully')
                    return redirect('service_usage_list')
                else:
                    messages.error(request, 'Can only add services to confirmed or checked-in reservations')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
                return render(request, 'admin/service_usage_list.html', context)
        
        return render(request, 'admin/service_usage_list.html', context)
    else:
        try:
            service_usage = get_object_or_404(ServiceUsage, id=usage_id)
            
            if request.method == 'POST':
                if request.POST.get('action') == 'edit':
                    # Get form data
                    service = Service.objects.get(id=request.POST.get('service'))
                    quantity = int(request.POST.get('quantity'))
                    
                    # Calculate new total
                    total = Decimal(str(service.price)) * Decimal(str(quantity))
                    
                    # Update service usage
                    service_usage.service = service
                    service_usage.quantity = quantity
                    service_usage.total = total
                    service_usage.save()
                    
                    # Update bill if exists
                    bill = Bill.objects.filter(reservation=service_usage.reservation).first()
                    if bill:
                        amounts = calculate_total_amount(service_usage.reservation)
                        bill.total_amount = amounts['total_amount']
                        bill.save()
                    
                    messages.success(request, 'Service updated successfully')
                    return redirect('service_usage_detail', usage_id=service_usage.id)
                    
                elif request.POST.get('action') == 'delete':
                    # Get reservation from service usage
                    reservation = service_usage.reservation
                    reservation_id = reservation.id
                    
                    # Delete service usage
                    service_usage.delete()
                    
                    # Update bill total
                    bill = Bill.objects.filter(reservation=reservation).first()
                    if bill:
                        # Recalculate amounts using imported function
                        amounts = calculate_total_amount(reservation)
                        bill.total_amount = amounts['total_amount']
                        bill.save()
                    
                    messages.success(request, 'Service usage deleted successfully')
                    return redirect('service_usage_list')
                    
                else:  # Add new service
                    service = Service.objects.get(id=request.POST.get('service'))
                    quantity = int(request.POST.get('quantity'))
                    date_used = request.POST.get('date_used')
                    
                    # Calculate total
                    total = Decimal(str(service.price)) * Decimal(str(quantity))
                    
                    # Create new service usage
                    ServiceUsage.objects.create(
                        reservation=service_usage.reservation,
                        room_id=service_usage.room_id,
                        service=service,
                        quantity=quantity,
                        date_used=date_used,
                        total=total
                    )
                    
                    # Update bill if exists
                    bill = Bill.objects.filter(reservation=service_usage.reservation).first()
                    if bill:
                        amounts = calculate_total_amount(service_usage.reservation)
                        bill.total_amount = amounts['total_amount']
                        bill.save()
                    
                    messages.success(request, 'Service added successfully')
                    return redirect('service_usage_detail', usage_id=service_usage.id)
            
            # Get all services for this reservation
            service_usages = ServiceUsage.objects.filter(
                reservation=service_usage.reservation
            )
            total_amount = sum(usage.total for usage in service_usages)
            
            context = {
                'service_usage': service_usage,
                'service_usages': service_usages,
                'total_amount': total_amount,
                'action': action,
                'services': Service.objects.all(),
                'can_add_service': service_usage.reservation.status in ['confirmed', 'checked_in'],
                'reservation_rooms': service_usage.reservation.reservationroom_set.all()
            }
            
            return render(request, 'admin/service_usage_list.html', context)
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('service_usage_list')