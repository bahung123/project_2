from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, F, Sum
from django.contrib import messages
from django.utils.timezone import now
from app.models import Reservation, Bill, ServiceUsage, Branch , Employee
from datetime import datetime, time
from decimal import Decimal

# Define fee rules as constants
CHECK_IN_RULES = {
    (time(5, 0), time(9, 0)): 0.5,  # 5:00 - 9:00: 50%
    (time(9, 0), time(14, 0)): 0.3  # 9:00 - 14:00: 30%
}

CHECK_OUT_RULES = {
    (time(12, 0), time(15, 0)): 0.3,  # 12:00 - 15:00: 30%
    (time(15, 0), time(18, 0)): 0.5,  # 15:00 - 18:00: 50%
    (time(18, 0), time(23, 59)): 1.0  # After 18:00: 100%
}

@login_required
def reservation_list(request):
    try:
        # Get search and filter parameters
        search_query = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '').strip()
        
        # Initialize variables
        selected_branch = None
        branches = None

        # Handle user permissions and branch access
        if request.user.is_superuser:
            # Superuser can see all branches
            branches = Branch.objects.all()
            selected_branch = request.GET.get('branch', '').strip()
        else:
            # Get employee record for non-superuser
            try:
                current_employee = Employee.objects.get(user_id=request.user.id)
                branches = Branch.objects.filter(id=current_employee.branch.id)
                selected_branch = str(current_employee.branch.id)
            except Employee.DoesNotExist:
                messages.error(request, 'No employee record found for this user.')
                return redirect('login')

        # Base queryset with newest reservations first
        reservations = Reservation.objects.all().order_by('-book_date', '-id')

        # Apply filters
        if search_query:
            reservations = reservations.filter(
                Q(guest__full_name__icontains=search_query) |
                Q(guest__email__icontains=search_query) |
                Q(guest__phone_number__icontains=search_query) |
                Q(reservationroom__room__room_number__icontains=search_query)
            ).distinct()

        if status_filter:
            reservations = reservations.filter(status=status_filter)

        if selected_branch:
            reservations = reservations.filter(
                reservationroom__room__branch_id=selected_branch
            ).distinct()

        # Pagination
        paginator = Paginator(reservations, 10)
        page = request.GET.get('page')
        reservations = paginator.get_page(page)

        context = {
            'reservations': reservations,
            'search_query': search_query,
            'status': status_filter,
            'branches': branches,
            'selected_branch': selected_branch,
            'is_admin': request.user.is_superuser,
            'status_choices': [
                ('pending', 'Pending'),
                ('confirmed', 'Confirmed'),
                ('cancelled', 'Cancelled'),
                ('checked_in', 'Checked In'),
                ('checked_out', 'Checked Out'),
            ],
            'active': 'reservations',
        }

        return render(request, 'admin/reservation_list.html', context)

    except Exception as e:
        messages.error(request, f'Error loading reservations: {str(e)}')
        return render(request, 'admin/reservation_list.html', {'error': str(e)})

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
            check_in_time = request.POST.get('check_in_time')
            check_out_time = request.POST.get('check_out_time')
            auto_update_status = False

            if check_in_time:
                try:
                    reservation.check_in_time = datetime.strptime(check_in_time, '%H:%M').time()
                    reservation.status = 'checked_in'
                    auto_update_status = True
                # Cập nhật trạng thái các phòng liên quan thành Occupied
                    for room in reservation.reservationroom_set.all():
                        room.room.status = 'occupied'
                        room.room.save()
                except ValueError:
                    messages.error(request, 'Invalid check-in time format')
                    return redirect('reservation_list')

            if check_out_time:
                try:
                    print(f"Raw check_out_time: {check_out_time}")  # Debug giá trị nhận được
                    
                    # Bỏ validation thừa vì HTML input type="time" đã validate
                    reservation.check_out_time = datetime.strptime(check_out_time, '%H:%M').time()
                    
                    # Tạo bill nếu chưa tồn tại
                    if not Bill.objects.filter(reservation=reservation).exists():
                        amounts = calculate_total_amount(reservation)
                        bill = Bill.objects.create(
                            reservation=reservation,
                            deposit_amount=amounts['deposit_amount'],
                            early_checkin_fee=amounts['early_checkin_fee'],
                            late_checkout_fee=amounts['late_checkout_fee'],
                            total_amount=amounts['total_amount'],
                            date_issued=now(),
                            paid_status='pending'
                        )
                        messages.success(request, 'Bill created successfully.')
                    else:
                        messages.warning(request, 'Bill already exists for this reservation.')
                    
                    reservation.status = 'checked_out'
                    auto_update_status = True

                    # Cập nhật trạng thái các phòng liên quan thành Available
                    for room in reservation.reservationroom_set.all():
                        room.room.status = 'available'
                        room.room.save()
                    
                except ValueError as e:
                    print(f"Error parsing time: {e}")  # Debug lỗi
                    messages.error(request, 'Error updating check-out time')
                    return redirect('reservation_list')

            if not auto_update_status and new_status:
                reservation.status = new_status

            reservation.save()
            messages.success(request, 'Reservation updated successfully.')
            
        else:
            messages.error(request, 'Invalid request method.')
            
    except Exception as e:
        messages.error(request, f'Error updating reservation: {str(e)}')
    
    return redirect('reservation_list')

def calculate_fee(actual_time, base_date, rules, room_price):
    """Calculate early check-in or late check-out fees based on rules."""
    try:
        check_time = actual_time.time()
        room_price = float(room_price)  # Convert Decimal to float
        
        for (start, end), rate in rules.items():
            if start <= check_time <= end:
                return float(room_price) * float(rate)
        return 0
    except Exception as e:
        print(f"Error in calculate_fee: {str(e)}")
        return 0

def calculate_total_amount(reservation):
    try:
        # Calculate room total using Decimal
        room_total = Decimal('0')
        for room in reservation.reservationroom_set.all():
            days = (reservation.check_out_date - reservation.check_in_date).days
            room_total += Decimal(str(room.room.room_type.base_price)) * Decimal(str(days))

        # Convert fees to Decimal with safe defaults
        early_checkin_fee = Decimal(str(getattr(reservation, 'early_checkin_fee', '0') or '0'))
        late_checkout_fee = Decimal(str(getattr(reservation, 'late_checkout_fee', '0') or '0'))

        # Calculate service charges using Decimal
        service_charges = ServiceUsage.objects.filter(
            reservation=reservation
        ).aggregate(
            total=Sum('total')
        )['total'] or Decimal('0')

        # Calculate total amount with Decimal
        total_amount = room_total + early_checkin_fee + late_checkout_fee + service_charges

        return {
            'room_total': room_total,
            'early_checkin_fee': early_checkin_fee,
            'late_checkout_fee': late_checkout_fee,
            'service_charges': service_charges,
            'total_amount': total_amount,
            'deposit_amount': Decimal(str(getattr(reservation, 'deposit_amount', '0') or '0'))
        }
    except Exception as e:
        print(f"Error calculating bill: {str(e)}")
        raise ValueError(f"Error calculating bill: {str(e)}")

@login_required 
def create_bill_view(request, reservation_id):
    """Handle bill creation and update reservation status."""
    try:
        reservation = get_object_or_404(Reservation, id=reservation_id)
        
        # Check if bill already exists
        if Bill.objects.filter(reservation=reservation).exists():
            messages.error(request, 'Bill already exists for this reservation')
            return redirect('reservation_list')
            
        # Calculate amounts
        amounts = calculate_total_amount(reservation)
        
        # Create bill
        bill = Bill.objects.create(
            reservation=reservation,
            deposit_amount=amounts['deposit_amount'],
            early_checkin_fee=amounts['early_checkin_fee'],
            late_checkout_fee=amounts['late_checkout_fee'],
            total_amount=amounts['total_amount'],
            date_issued=now(),
            paid_status='pending'
        )
        
        # Update reservation status
        reservation.status = 'checked_out'
        reservation.save()
        
        messages.success(request, 'Bill created successfully')
        return redirect('bill_list')
        
    except Exception as e:
        messages.error(request, f'Error creating bill: {str(e)}')
        return redirect('reservation_list')

@login_required
def reservation_detail(request, reservation_id):
    try:
        reservation = get_object_or_404(Reservation, id=reservation_id)
        amounts = calculate_total_amount(reservation)
        
        context = {
            'reservation': reservation,
            'amounts': amounts,
            'active': 'reservations',
            'status_choices': [
                ('pending', 'Pending'),
                ('confirmed', 'Confirmed'),
                ('cancelled', 'Cancelled'),
                ('checked_in', 'Checked In'),
                ('checked_out', 'Checked Out'),
            ]
        }
        return render(request, 'admin/reservation_detail.html', context)

    except Exception as e:
        messages.error(request, f'Error loading reservation details: {str(e)}')
        return redirect('reservation_list')
