from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from app.models import RoomType, Image, Guest, Service, Reservation, Room, ReservationRoom
from django.contrib.auth.models import User
from datetime import datetime
from django.http import HttpResponse
from django.db.models import Q


def index(request):
    room_types = RoomType.objects.all()
    for room_type in room_types:
        room_type.image = Image.objects.filter(room_type_id=room_type.id).first()
    return render(request, 'index.html', {'room_types': room_types})

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')


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
            return render(request, 'register.html', {'error': 'Passwords do not match'})

        # Kiểm tra xem username đã tồn tại chưa
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists'})

        # Kiểm tra xem email đã tồn tại chưa
        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'Email already exists'})

        # Lưu người dùng mới vào bảng auth_user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # Lưu thông tin khách hàng vào bảng Guest với id_card
        guest = Guest(full_name=full_name, phone_number=phone_number, email=email, address=address, id_card=id_card, user_id=user.id)
        guest.save()

        # Chuyển hướng về trang login (hoặc bất kỳ trang nào khác)
        messages.success(request, 'Account created successfully. Please login!')
        return redirect('login')

    return render(request, 'register.html')



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
    return render(request, 'room.html', {'room_types': room_types})


def room_detail(request):
    return render(request, 'room_detail.html')
def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')

def service(request):
    services = Service.objects.all()
    
    # Lấy hình ảnh đầu tiên cho từng dịch vụ
    for service in services:
        service.image = Image.objects.filter(service_id=service.id).first()  # service_id tương ứng với id của Service
    
    return render(request, 'service.html', {'services': services})


def booking(request):
    room_types = RoomType.objects.all()
    rooms = []
    guest_name = ''
    guest_email = ''
    guest_phone = ''
    guest_id_card = ''
    check_in = ''
    check_out = ''
    room_type_id = ''
    total_amount = 0

    # Nếu người dùng đã đăng nhập, lấy thông tin khách hàng
    if request.user.is_authenticated:
        guest = Guest.objects.filter(user_id=request.user.id).first()
        if guest:
            guest_name = guest.full_name
            guest_email = guest.email
            guest_phone = guest.phone_number
            guest_id_card = guest.id_card

    if request.method == 'POST':
        # Lấy thông tin từ form
        guest_name = request.POST.get('guest_name', '').strip()
        guest_email = request.POST.get('guest_email', '').strip()
        guest_phone = request.POST.get('guest_phone', '').strip()
        guest_id_card = request.POST.get('guest_id_card', '').strip()
        check_in = request.POST.get('check_in', '').strip()
        check_out = request.POST.get('check_out', '').strip()
        room_type_id = request.POST.get('room_type', '').strip()

        # Kiểm tra đầu vào và xử lý
        if not guest_name or not guest_email or not guest_phone or not guest_id_card:
            messages.error(request, "Vui lòng điền đầy đủ thông tin khách hàng.")
        elif not check_in or not check_out:
            messages.error(request, "Ngày nhận phòng và ngày trả phòng không được để trống.")
        else:
            try:
                # Kiểm tra tính hợp lệ của ngày nhận và trả phòng
                check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
                check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
                num_nights = (check_out_date - check_in_date).days

                if num_nights < 1:
                    messages.error(request, "Ngày trả phòng phải sau ngày nhận phòng.")
                else:
                    # Lấy loại phòng và danh sách phòng trống
                    room_type = RoomType.objects.get(id=room_type_id)
                    total_amount = room_type.base_price * num_nights

                    # Lấy danh sách các phòng đã được đặt trong khoảng thời gian người dùng yêu cầu
                    rooms_reserved = ReservationRoom.objects.filter(
                        reservation__check_in_date__lt=check_out_date,
                        reservation__check_out_date__gt=check_in_date
                    ).values_list('room_id', flat=True)  # Lấy room_id từ bảng ReservationRoom

                    # Lọc ra các phòng trống (chưa bị đặt trong thời gian này)
                    rooms = Room.objects.filter(
                        room_type_id=room_type_id
                    ).exclude(id__in=rooms_reserved)  # Loại bỏ các phòng đã được đặt

                    if rooms.exists():
                        # Tạo đặt phòng và cập nhật trạng thái phòng nếu người dùng xác nhận
                        guest, created = Guest.objects.get_or_create(email=guest_email, defaults={
                            'full_name': guest_name,
                            'phone_number': guest_phone,
                            'id_card': guest_id_card
                        })
                        reservation = Reservation.objects.create(
                            guest=guest,
                            branch_id=rooms[0].branch_id,
                            check_in_date=check_in_date,
                            check_out_date=check_out_date,
                            status='confirmed'
                        )
                        for room in rooms:
                            room.status = 'booked'
                            room.save()
                        messages.success(request, "Đặt phòng thành công!")
                        return redirect('booking')  # Redirect to booking page to avoid resubmission
                    else:
                        messages.error(request, "Không có phòng trống phù hợp.")
            except RoomType.DoesNotExist:
                messages.error(request, "Loại phòng không hợp lệ.")
            except ValueError:
                messages.error(request, "Ngày tháng không hợp lệ. Vui lòng kiểm tra lại.")
    else:  # Xử lý GET request
        check_in = request.GET.get('check_in', '').strip()
        check_out = request.GET.get('check_out', '').strip()
        room_type_id = request.GET.get('room_type', '').strip()
        if check_in and check_out and room_type_id:
            try:
                # Tính toán danh sách phòng trống
                check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
                check_out_date = datetime.strptime(check_out, '%Y-%m-%d')

                # Lấy loại phòng
                room_type = RoomType.objects.get(id=room_type_id)
                total_amount = room_type.base_price * (
                    (check_out_date - check_in_date).days
                )

                # Lấy danh sách các phòng đã được đặt trong khoảng thời gian người dùng yêu cầu
                rooms_reserved = ReservationRoom.objects.filter(
                    reservation__check_in_date__lt=check_out_date,
                    reservation__check_out_date__gt=check_in_date
                ).values_list('room_id', flat=True)  # Lấy room_id từ bảng ReservationRoom

                # Lọc ra các phòng trống
                rooms = Room.objects.filter(
                    room_type_id=room_type_id
                ).exclude(id__in=rooms_reserved)  # Loại bỏ các phòng đã được đặt

            except RoomType.DoesNotExist:
                messages.error(request, "Loại phòng không hợp lệ.")
            except ValueError:
                messages.error(request, "Ngày tháng không hợp lệ. Vui lòng kiểm tra lại.")

    # Truyền dữ liệu về template
    context = {
        'room_types': room_types,
        'rooms': rooms,
        'guest_name': guest_name,
        'guest_email': guest_email,
        'guest_phone': guest_phone,
        'guest_id_card': guest_id_card,
        'check_in': check_in,
        'check_out': check_out,
        'room_type_id': room_type_id,
        'total_amount': total_amount,
    }
    return render(request, 'booking.html', context)
