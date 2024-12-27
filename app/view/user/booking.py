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

@csrf_protect
def booking(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Lấy thông tin từ form
                selected_rooms = request.POST.getlist('selected_rooms')
                check_in = request.POST.get('check_in')
                check_out = request.POST.get('check_out')
                guest_name = request.POST.get('guest_name')
                guest_email = request.POST.get('guest_email')
                guest_phone = request.POST.get('guest_phone')
                guest_id_card = request.POST.get('guest_id_card')
                guest_address = request.POST.get('guest_address', '') 
                deposit_amount = request.POST.get('deposit_amount', 0)

                # Debug information
                print("DEBUG: Form data received:")
                print(f"Selected rooms: {selected_rooms}")
                print(f"Check in: {check_in}")
                print(f"Check out: {check_out}")
                print(f"Guest info: {guest_name}, {guest_email}, {guest_phone}, {guest_address}, {guest_id_card}")

                # Validate dates
                check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
                check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()

                # Tạo hoặc lấy thông tin Guest
                guest, created = Guest.objects.get_or_create(
                    email=guest_email,
                    defaults={
                        'full_name': guest_name,
                        'phone_number': guest_phone,
                        'address': guest_address or '',  # Ensure address is saved even if empty
                        'id_card': guest_id_card,
                        'has_account': 1 if request.user.is_authenticated else 0,
                        'user_id': request.user.id if request.user.is_authenticated else None
                    }
                )

                # Lấy branch từ room đầu tiên được chọn
                first_room = Room.objects.get(id=selected_rooms[0])
                branch = first_room.branch

                # Tạo reservation
                reservation = Reservation.objects.create(
                    guest=guest,
                    book_date=datetime.now(),
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                    deposit_amount=deposit_amount,
                    status='pending'  # hoặc trạng thái phù hợp
                )

                # Tạo reservation rooms
                for room_id in selected_rooms:
                    room = Room.objects.get(id=room_id)
                    room.status = 'booked'  
                    room.save()
                    
                    # Create reservation room record
                    ReservationRoom.objects.create(
                        reservation=reservation,
                        room=room
                    )

            messages.success(request, 'Booking successful! Thank you for choosing our service.')
            return redirect('booking')

        except Exception as e:
            import traceback
            print("ERROR in booking:")
            print(traceback.format_exc())
            messages.error(request, f'Booking error: {str(e)}')
            return redirect('booking')

    # GET request
    room_types = RoomType.objects.all()
    branches = Branch.objects.all()  # Lấy tất cả các branch
    
    # Lấy thông tin khách hàng từ user đã đăng nhập
    context = {
        'room_types': room_types,
        'branches': branches,
        'today': datetime.now().date(),
    }
    
    if request.user.is_authenticated:
        try:
            # Lấy thông tin từ Guest model
            guest = Guest.objects.get(user_id=request.user.id)
            context.update({
                'guest_name': guest.full_name,
                'guest_email': guest.email,
                'guest_phone': guest.phone_number,
                'guest_address': guest.address,
                'guest_id_card': guest.id_card,
                
            })
        except Guest.DoesNotExist:
            # Nếu không tìm thấy Guest, sử dụng thông tin cơ bản từ User
            context.update({
                'guest_name': request.user.get_full_name() or request.user.username,
                'guest_email': request.user.email,
                'guest_phone': '',
                'guest_address': '',
                'guest_id_card': '',
            })
    else:
        # Nếu chưa đăng nhập, lấy từ GET parameters
        context.update({
            'guest_name': request.GET.get('guest_name', ''),
            'guest_email': request.GET.get('guest_email', ''),
            'guest_phone': request.GET.get('guest_phone', ''),
            'guest_address': request.GET.get('guest_address', ''),
            'guest_id_card': request.GET.get('guest_id_card', ''),
        })

    # Thêm các thông tin khác vào context
    context.update({
        'room_type_id': request.GET.get('room_type', ''),
        'check_in': request.GET.get('check_in', ''),
        'check_out': request.GET.get('check_out', ''),
        'branch_id': request.GET.get('branch', ''),
    })

    return render(request, 'user/booking.html', context)

def search_rooms(request):
    try:
        # Validate input
        check_in = request.GET.get('check_in', '').strip()
        check_out = request.GET.get('check_out', '').strip()
        room_type_id = request.GET.get('room_type', '').strip()
        branch_id = request.GET.get('branch', '').strip()

        if not all([check_in, check_out, room_type_id, branch_id]):
            return JsonResponse({'error': 'Please fill in all required fields'})

        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'})

        # Validate dates
        if check_in_date >= check_out_date:
            return JsonResponse({'error': 'Check-out date must be after check-in date'})
        
        if check_in_date < datetime.now().date():
            return JsonResponse({'error': 'Check-in date cannot be in the past'})

        number_of_nights = (check_out_date - check_in_date).days

        # Get room type and branch
        try:
            room_type = RoomType.objects.get(id=room_type_id)
        except RoomType.DoesNotExist:
            return JsonResponse({'error': 'Invalid room type selected'})

        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            return JsonResponse({'error': 'Invalid branch selected'})

        price_per_night = float(room_type.base_price)

        # Get reserved rooms
        rooms_reserved = ReservationRoom.objects.filter(
            reservation__check_in_date__lt=check_out_date,
            reservation__check_out_date__gt=check_in_date
        ).values_list('room_id', flat=True)

        # Get available rooms (excluding those in "maintenance" state)
        rooms = Room.objects.filter(
            room_type_id=room_type_id,
            branch_id=branch_id
        ).exclude(id__in=rooms_reserved).exclude(status='maintenance')  # Exclude rooms in maintenance

        if not rooms.exists():
            return JsonResponse({'error': 'No rooms available for the selected dates and branch'})

        # Convert rooms to dict
        rooms_data = [{
            'id': room.id,
            'room_number': room.room_number,
            'room_type_name': room.room_type.name,
            'price': price_per_night,
            'branch_address': branch.address  # Thêm địa chỉ chi nhánh vào kết quả trả về
        } for room in rooms]

        total_price = price_per_night * number_of_nights
        deposit_amount = total_price * 0.3  # Calculate 30% deposit

        return JsonResponse({
            'rooms': rooms_data,
            'numberOfNights': number_of_nights,
            'pricePerNight': price_per_night,
            'depositAmount': deposit_amount,
            'branch_address': branch.address  # Thêm địa chỉ chi nhánh vào kết quả trả về
        })

    except Exception as e:
        import traceback
        print("An error occurred while searching for rooms:")  # In thông báo lỗi
        print(traceback.format_exc())  # In chi tiết lỗi ra console/log
        return JsonResponse({'error': f'An error occurred: {str(e)}'})