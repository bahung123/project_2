from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from app.models import RoomType, Image, Guest, Service, Reservation, Room
from django.contrib.auth.models import User
from datetime import datetime
from django.http import HttpResponse


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
    
    if request.method == 'POST':
        # Lấy thông tin từ form
        guest_name = request.POST.get('guest_name')
        guest_email = request.POST.get('guest_email')
        guest_phone = request.POST.get('guest_phone')
        guest_id_card = request.POST.get('guest_id_card')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        room_type_id = request.POST.get('room_type')
        
        # Kiểm tra xem check_in và check_out có giá trị hợp lệ không
        if not check_in or not check_out:
            return HttpResponse("Ngày nhận phòng và ngày trả phòng không được để trống.", status=400)
        
        # Tính toán số đêm
        try:
            num_nights = (datetime.strptime(check_out, '%Y-%m-%d') - datetime.strptime(check_in, '%Y-%m-%d')).days
            if num_nights < 1:
                return HttpResponse("Ngày trả phòng phải sau ngày nhận phòng.", status=400)
        except ValueError:
            return HttpResponse("Ngày tháng không hợp lệ. Vui lòng kiểm tra lại.", status=400)

        # Lấy loại phòng và tính tổng tiền
        room_type = RoomType.objects.get(id=room_type_id)
        total_amount = room_type.base_price * num_nights
        
        # Lấy tất cả các phòng còn trống của loại phòng đã chọn
        rooms = Room.objects.filter(room_type_id=room_type_id, status='available')
        
        # Lưu thông tin khách hàng vào bảng guest nếu chưa có tài khoản
        guest, created = Guest.objects.get_or_create(email=guest_email, defaults={
            'full_name': guest_name,
            'phone_number': guest_phone,
            'id_card': guest_id_card
        })

        # Lưu thông tin đặt phòng vào bảng reservation
        reservation = Reservation.objects.create(
            guest=guest,
            branch_id=rooms[0].branch_id,  # Lấy chi nhánh từ phòng đầu tiên
            check_in_date=check_in,
            check_out_date=check_out,
            status='confirmed'
        )

        # Đánh dấu phòng là đã được đặt
        for room in rooms:
            room.status = 'booked'
            room.save()

        # Chuyển hướng đến trang xác nhận hoặc trang hóa đơn
        return redirect('reservation_detail', reservation_id=reservation.id)

    else:  # Nếu là GET request
        # Kiểm tra nếu người dùng đã đăng nhập
        if request.user.is_authenticated:
            guest = Guest.objects.filter(user_id=request.user.id).first()
            if guest:
                guest_name = guest.full_name
                guest_email = guest.email
                guest_phone = guest.phone_number
                guest_id_card = guest.id_card

    # Trả về form với các loại phòng và phòng trống, điền sẵn thông tin khách hàng nếu đã đăng nhập
    context = {
        'room_types': room_types,
        'rooms': rooms,
        'guest_name': guest_name,
        'guest_email': guest_email,
        'guest_phone': guest_phone,
        'guest_id_card': guest_id_card,
        'check_in': check_in,  # Thêm check_in vào context
        'check_out': check_out,  # Thêm check_out vào context
        'room_type_id': room_type_id,  # Thêm room_type_id vào context
        'total_amount': total_amount,  # Thêm total_amount vào context
    }
    
    return render(request, 'booking.html', context)





def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')


from .models import Service, Image

def service(request):
    services = Service.objects.all()
    
    # Lấy hình ảnh đầu tiên cho từng dịch vụ
    for service in services:
        service.image = Image.objects.filter(service_id=service.id).first()  # service_id tương ứng với id của Service
    
    return render(request, 'service.html', {'services': services})


