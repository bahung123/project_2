from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Max
from django.contrib.auth.decorators import login_required
from app.models import ServiceUsage, Reservation, Room, Service
from decimal import Decimal

@login_required
def service_usage_list(request):
    search_query = request.GET.get('search', '')
    
    # Get unique reservations with their latest service usage
    if search_query:
        service_usages = ServiceUsage.objects.select_related(
            'reservation__guest', 'service', 'reservation'
        ).filter(
            Q(reservation__id__icontains=search_query) |
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
        'service_usages': service_usages,
        'search_query': search_query,
        'action': 'list'
    }
    return render(request, 'admin/service_usage_list.html', context)

@login_required 
def service_usage_detail(request, usage_id):
    action = request.GET.get('action', 'view')
    
    if usage_id == 0:
        # Get all confirmed reservations that don't have service usage
        available_reservations = Reservation.objects.filter(
        ).exclude(
            id__in=ServiceUsage.objects.values_list('reservation_id', flat=True)
        ).select_related('guest').order_by('-id')

        context = {
            'action': 'add',
            'available_reservations': available_reservations, # Changed variable name
            'services': Service.objects.all()
        }
        
        if request.method == 'POST':
            try:
                reservation = Reservation.objects.get(id=request.POST.get('reservation'))
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
                
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
                return render(request, 'admin/service_usage_list.html', context)
        
        return render(request, 'admin/service_usage_list.html', context)
    else:
        try:
            service_usage = get_object_or_404(ServiceUsage, id=usage_id)
            
            if request.method == 'POST':
                if action == 'delete':
                    # Just delete the single service
                    service_usage.delete()
                    messages.success(request, 'Service deleted successfully')
                    
                    # Check remaining services
                    remaining_services = ServiceUsage.objects.filter(
                        reservation_id=service_usage.reservation.id
                    ).first()
                    
                    if remaining_services:
                        return redirect('service_usage_detail', usage_id=remaining_services.id)
                    else:
                        return redirect('service_usage_list')
                else:
                    try:
                        reservation_id = request.POST.get('reservation')
                        reservation = service_usage.reservation  # Use existing reservation
                        
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
                        messages.success(request, 'Service added successfully')
                        
                    except Exception as e:
                        messages.error(request, f'Error: {str(e)}')
            
            # Get all services and rooms for this reservation
            service_usages = ServiceUsage.objects.filter(
                reservation_id=service_usage.reservation.id
            )
            total_amount = sum(usage.total for usage in service_usages)
            
            # Get all rooms for this reservation
            reservation_rooms = service_usage.reservation.reservationroom_set.all()
            
            context = {
                'service_usage': service_usage,
                'service_usages': service_usages,
                'total_amount': total_amount,
                'reservation_rooms': reservation_rooms,
                'action': action,
                'services': Service.objects.all()
            }
            
        except ServiceUsage.DoesNotExist:
            messages.error(request, 'Service usage not found')
            return redirect('service_usage_list')
    
    return render(request, 'admin/service_usage_list.html', context)