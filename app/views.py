from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from app.models import RoomType, Image, Guest, Service, Reservation, Room, ReservationRoom,Employee,Branch
from django.contrib.auth.models import User
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.db import transaction
from django.views.decorators.csrf import csrf_protect
from django.utils.timezone import now


def index(request):
    room_types = RoomType.objects.all()
    for room_type in room_types:
        room_type.image = Image.objects.filter(room_type_id=room_type.id).first()
    return render(request, 'user/index.html', {'room_types': room_types})

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Xác thực người dùng
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)

            # Kiểm tra nếu người dùng là admin (is_superuser)
            if user.is_superuser:
                role = 'Admin'
            # Kiểm tra nếu người dùng là employee (is_staff) nhưng không phải admin
            elif user.is_staff:
                role = 'Employee'
            else:
                # Kiểm tra nếu người dùng là khách hàng trong bảng Guest dựa vào user_id
                guest = Guest.objects.filter(user_id=user.id).first()  # Dùng user_id thay vì email
                if guest:
                    role = 'Guest'
                else:
                    role = 'Unknown'  # Nếu không phải là employee hay guest

            # Lưu thông tin role vào session
            request.session['role'] = role
            print(f"User {user.username} logged in as {role}")

            # Redirect người dùng đến trang phù hợp tùy theo role
            if role in ['Admin', 'Employee']:
                return redirect('base_admin')  # Trang base_admin dành cho admin và employee
            else:
                return redirect('index')  # Trang index dành cho guest

        else:
            print(f"DEBUG: User {username} authentication failed.")
            messages.error(request, 'Invalid username or password')

    return render(request, 'user/login.html')





def logout_view(request):
    logout(request)
    return redirect('login')


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        full_name = request.POST.get('full_name', '')
        phone_number = request.POST.get('phone_number', '')
        address = request.POST.get('address', '')
        id_card = request.POST.get('id_card', '')  # Lấy giá trị id_card

        # Kiểm tra mật khẩu
        if password != confirm_password:
            return render(request, 'user/register.html', {'error': 'Passwords do not match'})

        # Kiểm tra xem username đã tồn tại chưa
        if User.objects.filter(username=username).exists():
            return render(request, 'user/register.html', {'error': 'Username already exists'})

        # Kiểm tra xem email đã tồn tại chưa
        if User.objects.filter(email=email).exists():
            return render(request, 'user/register.html', {'error': 'Email already exists'})

        # Lưu người dùng mới vào bảng auth_user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # Lưu thông tin khách hàng vào bảng Guest với id_card
        guest = Guest(full_name=full_name, phone_number=phone_number, email=email, address=address, id_card=id_card, user_id=user.id)
        guest.save()

        # Chuyển hướng về trang login (hoặc bất kỳ trang nào khác)
        messages.success(request, 'Account created successfully. Please login!')
        return redirect('login')

    return render(request, 'user/register.html')



@login_required
def account_info(request):
    user = request.user
    try:
        guest = Guest.objects.get(user_id=user.id)
    except Guest.DoesNotExist:
        guest = None

    return render(request, 'include/account_info.html', {
        'user': user,
        'guest': guest,
    })


@login_required
def update_account_info(request):
    if request.method == 'POST':
        user = request.user
        guest = Guest.objects.get(user_id=user.id)

        # Cập nhật thông tin của người dùng
        guest.full_name = request.POST['full_name']
        user.email = request.POST['email']
        guest.phone_number = request.POST['phone_number']
        guest.address = request.POST['address']
        guest.id_card = request.POST['id_card']  # Cập nhật id_card từ form

        # Lưu thông tin
        user.save()
        guest.save()

        messages.success(request, 'Your account information has been updated successfully.')
        return redirect('account_info')

    return render(request, 'account_info.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        user = request.user
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_new_password = request.POST['confirm_new_password']

        if user.check_password(old_password):
            if new_password == confirm_new_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Your password has been changed successfully.')
                return redirect('login')
            else:
                messages.error(request, 'New passwords do not match.')
        else:
            messages.error(request, 'Incorrect old password.')
    return redirect('account_info')


def room(request):
    room_types = RoomType.objects.all()
    for room_type in room_types:
        room_type.image = Image.objects.filter(room_type_id=room_type.id).first()
    return render(request, 'user/room.html', {'room_types': room_types})


def room_detail(request):
    return render(request, 'user/room_detail.html')

def about(request):
    return render(request, 'user/about.html')


def contact(request):
    return render(request, 'user/contact.html')

def service(request):
    services = Service.objects.all()
    
    # Lấy hình ảnh đầu tiên cho từng dịch vụ
    for service in services:
        service.image = Image.objects.filter(service_id=service.id).first()  # service_id tương ứng với id của Service
    
    return render(request, 'user/service.html', {'services': services})

@csrf_protect
def booking(request):
    if request.method == 'POST':
        try:
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
            with transaction.atomic():
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
                    ReservationRoom.objects.create(
                        reservation=reservation,
                        room_id=room_id
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

        # Get available rooms
        rooms = Room.objects.filter(
            room_type_id=room_type_id,
            branch_id=branch_id
        ).exclude(id__in=rooms_reserved)

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