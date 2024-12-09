from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView
from .models import Employee, Branch, AuthUser , Guest , RoomType , Image, Room , Service
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator


# Đảm bảo rằng chỉ người dùng đã đăng nhập mới có thể truy cập trang quản trị
@login_required
def base_admin(request):
    return render(request, 'admin/base_admin.html')

@login_required
def dashboard(request):
    context = {
        'total_revenue': 50000,
        'total_reservations': 120,
        'total_rooms': 30,
        'total_employees': 15,
        'active': 'dashboard',  # Để sidebar hiển thị đúng menu đang active
    }
    return render(request, 'admin/dashboard.html', context)

@login_required 
def employee_list(request, pk=None):
    action = request.GET.get('action', 'list')  # Lấy action từ query string (mặc định là 'list')
    search_query = request.GET.get('search', '')  # Lấy query tìm kiếm từ URL
    context = {'action': action, 'search_query': search_query}
    
    if action == 'list':
        # Hiển thị danh sách nhân viên
        if search_query:
            employees = Employee.objects.filter(
                Q(full_name__icontains=search_query) |  # Tìm kiếm theo tên đầy đủ
                Q(email__icontains=search_query)        # Tìm kiếm theo email
            )
        else:
            employees = Employee.objects.all()  # Lấy tất cả nhân viên nếu không có tìm kiếm
        context['employees'] = employees
        return render(request, 'admin/employee_list.html', context)

    
    elif action == 'view' and pk:
        # Hiển thị chi tiết nhân viên
        employee = get_object_or_404(Employee, pk=pk)
        context['employee'] = employee
        return render(request, 'admin/employee_list.html', context)

    elif action == 'edit' and pk:
        # Hiển thị form chỉnh sửa
        employee = get_object_or_404(Employee, pk=pk)
        user = AuthUser.objects.get(pk=employee.user_id)
        if request.method == 'POST':
            full_name = request.POST.get('full_name')
            phone_number = request.POST.get('phone_number')
            email = request.POST.get('email')
            position = request.POST.get('position')
            department = request.POST.get('department')
            salary = request.POST.get('salary')
            status = request.POST.get('status')

            # Kiểm tra số điện thoại có trùng với nhân viên khác không (ngoại trừ nhân viên hiện tại)
            if Employee.objects.filter(phone_number=phone_number).exclude(pk=employee.pk).exists():
                context['error'] = 'Phone number already exists for another employee'
                context['employee'] = employee
                messages.error(request, 'Phone number already exists for another employee')
                return render(request, 'admin/employee_list.html', context)
            
            # Kiểm tra email có trùng với nhân viên khác không (ngoại trừ nhân viên hiện tại)
            if Employee.objects.filter(email=email).exclude(pk=pk).exists():
                context['error'] = 'Email already exists'
                context['employee'] = employee
                messages.error(request, 'Email already exists')
                return render(request, 'admin/employee_list.html', context)
            
            #cập nhật authuser
            user.email = email
            user.save()
            # cập nhật thông tin nhân viên
            employee.full_name = full_name
            employee.phone_number = phone_number
            employee.email = email
            employee.position = position
            employee.department = department
            employee.salary = salary
            employee.status = status
            employee.save()
            messages.success(request, 'Employee updated successfully')
            return redirect('employee_list')
        context['employee'] = employee
        return render(request, 'admin/employee_list.html', context)

    elif action == 'delete' and pk:
        employee= get_object_or_404(Employee, pk=pk)
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    #kiểm tra nhân viên nếu có user_id hợp lệ
                    if employee.user_id:
                        user = AuthUser.objects.get(pk=employee.user_id)
                        user.delete()
                    #xóa nhân viên 
                    employee.delete()
                    messages.success(request, 'Employee deleted successfully')
            except Exception as e:
                messages.error(request, f"Error while deleting employee or account: {e}")

            return redirect('employee_list')
        context['employee'] = employee
        return render(request, 'admin/employee_list.html', context)
    
    if action == 'add':
        branches = Branch.objects.all()  # Lấy tất cả các chi nhánh
        context['branches'] = branches

        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            full_name = request.POST.get('full_name')
            phone_number = request.POST.get('phone_number')
            email = request.POST.get('email')
            position = request.POST.get('position')
            department = request.POST.get('department')
            salary = request.POST.get('salary')
            status = request.POST.get('status')
            branch = request.POST.get('branch')
            hire_date = request.POST.get('hire_date')

            # Kiểm tra username đã tồn tại chưa trong AuthUser
            if AuthUser.objects.filter(username=username).exists():
                context['error'] = 'Username already exists'
                messages.error(request, 'Username already exists')
                return render(request, 'admin/employee_list.html', context)

            # Kiểm tra email đã tồn tại chưa trong AuthUser
            if AuthUser.objects.filter(email=email).exists():
                context['error'] = 'Email already exists'
                messages.error(request, 'Email already exists')
                return render(request, 'admin/employee_list.html', context)

            # Kiểm tra phone_number đã tồn tại chưa trong Employee
            if Employee.objects.filter(phone_number=phone_number).exists():
                context['error'] = 'Phone number already exists'
                messages.error(request, 'Phone number already exists')
                return render(request, 'admin/employee_list.html', context)

            # Kiểm tra mật khẩu
            if password != confirm_password:
                context['error'] = 'Password does not match'
                messages.error(request, 'Password does not match')
                return render(request, 'admin/employee_list.html', context)

            # Tạo tài khoản AuthUser
            user = AuthUser.objects.create(
                username=username,
                password=make_password(password),  # Mã hóa mật khẩu
                first_name='',
                last_name='',
                email=email,
                is_staff=1,  # Đặt giá trị is_staff
                is_superuser=0,
                is_active=1,
                date_joined=timezone.now()
            )

            # Tạo nhân viên và liên kết với user
            employee = Employee(
                user=user,  # Liên kết với AuthUser
                branch_id=branch,
                full_name=full_name,
                phone_number=phone_number,
                email=email,
                position=position,
                department=department,
                salary=salary,
                hire_date=hire_date,
                status=status
            )
            employee.save()

            messages.success(request, 'Employee added successfully')
            return redirect('employee_list')
        
    return render(request, 'admin/employee_list.html', context)

@login_required
def guest_list(request , pk=None):
    action = request.GET.get('action', 'list')  # Lấy action từ query string (mặc định là 'list')
    search_query = request.GET.get('search', '')
    context = {'action': action, 'search_query': search_query}

    if action == 'list':
        # Hiển thị danh sách khách hàng
        if search_query:
            guests = Guest.objects.filter(
                Q(full_name__icontains=search_query) |  # Tìm kiếm theo tên đầy đủ
                Q(email__icontains=search_query)        # Tìm kiếm theo email
            )
        else:
            guests = Guest.objects.all()
        context['guests'] = guests
        return render(request, 'admin/guest_list.html', context)
    
    elif action == 'view' and pk:
        # Hiển thị chi tiết khách hàng
        guest = get_object_or_404(Guest, pk=pk)
        context['guest'] = guest
        return render(request, 'admin/guest_list.html', context)
    
    elif action == 'edit' and pk:
        # Hiển thị form chỉnh sửa
        guest = get_object_or_404(Guest, pk=pk)
        user = AuthUser.objects.get(pk=guest.user_id)
        if request.method == 'POST':
            full_name = request.POST.get('full_name')
            phone_number = request.POST.get('phone_number')
            email = request.POST.get('email')
            address = request.POST.get('address')
            id_card = request.POST.get('id_card')

            # Kiểm tra số điện thoại có trùng với khách hàng khác không (ngoại trừ khách hàng hiện tại)
            if Guest.objects.filter(phone_number=phone_number).exclude(pk=guest.pk).exists():
                context['error'] = 'Phone number already exists for another guest'
                context['guest'] = guest
                messages.error(request, 'Phone number already exists for another guest')
                return render(request, 'admin/guest_list.html', context)
            
            # Kiểm tra email có trùng với khách hàng khác không (ngoại trừ khách hàng hiện tại)
            if Guest.objects.filter(email=email).exclude(pk=pk).exists():
                context['error'] = 'Email already exists'
                context['guest'] = guest
                messages.error(request, 'Email already exists')
                return render(request, 'admin/guest_list.html', context)
            #kiểm tra id_card có trùng với khách hàng khác không (ngoại trừ khách hàng hiện tại)
            if Guest.objects.filter(id_card=id_card).exclude(pk=pk).exists():
                context['error'] = 'Id card already exists'
                context['guest'] = guest
                messages.error(request, 'Id card already exists')
                return render(request, 'admin/guest_list.html', context)
            
            #cập nhật authuser
            user.email = email
            user.save()
            # cập nhật thông tin khách hàng
            guest.full_name = full_name
            guest.phone_number = phone_number
            guest.email = email
            guest.address = address
            guest.id_card = id_card
            guest.save()
            messages.success(request, 'Guest updated successfully')
            return redirect('guest_list')
        context['guest'] = guest
        return render(request, 'admin/guest_list.html', context)
    
    elif action == 'delete' and pk:
        # Xóa khách hàng và tài khoản AuthUser liên kết nếu có
        guest = get_object_or_404(Guest, pk=pk)
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    #kiểm tra khách hàng nếu có user_id hợp lệ
                    if guest.user_id:
                        user = AuthUser.objects.get(pk=guest.user_id)
                        user.delete()
                    #xóa khách hàng
                    guest.delete()
                    messages.success(request, 'Guest deleted successfully')
            except Exception as e:
                messages.error(request, f"Error while deleting guest or account: {e}")

            return redirect('guest_list')
        context['guest'] = guest
        return render(request, 'admin/guest_list.html', context)

    if action == 'add':
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            full_name = request.POST.get('full_name')
            phone_number = request.POST.get('phone_number')
            email = request.POST.get('email')
            address = request.POST.get('address')
            id_card = request.POST.get('id_card')

            # Kiểm tra username đã tồn tại chưa trong AuthUser
            if AuthUser.objects.filter(username=username).exists():
                context['error'] = 'Username already exists'
                messages.error(request, 'Username already exists')
                return render(request, 'admin/guest_list.html', context)

            # Kiểm tra phone_number đã tồn tại chưa trong Guest
            if Guest.objects.filter(phone_number=phone_number).exists():
                context['error'] = 'Phone number already exists'
                messages.error(request, 'Phone number already exists')
                return render(request, 'admin/guest_list.html', context)

            # Kiểm tra email đã tồn tại chưa trong Guest
            if Guest.objects.filter(email=email).exists():
                context['error'] = 'Email already exists'
                messages.error(request, 'Email already exists')
                return render(request, 'admin/guest_list.html', context)

            # Kiểm tra id_card đã tồn tại chưa trong Guest
            if Guest.objects.filter(id_card=id_card).exists():
                context['error'] = 'Id card already exists'
                messages.error(request, 'Id card already exists')
                return render(request, 'admin/guest_list.html', context)
            
            # Kiểm tra mật khẩu
            if password != confirm_password:
                context['error'] = 'Password does not match'
                messages.error(request, 'Password does not match')
                return render(request, 'admin/guest_list.html', context)
            
            #tạo tài khoản AuthUser
            user = AuthUser.objects.create(
                username=username,
                password=make_password(password),  # Mã hóa mật khẩu
                first_name='',
                last_name='',
                email=email,
                is_staff=0,  # Đặt giá trị is_staff
                is_superuser=0,
                is_active=1,
                date_joined=timezone.now()
            )
            
            # Tạo khách hàng và liên kết với user
            guest = Guest(
                full_name=full_name,
                phone_number=phone_number,
                email=email,
                address=address,
                has_account=1,
                id_card=id_card
            )
            guest.save()
            messages.success(request, 'Guest added successfully')
            return redirect('guest_list')
    return render(request, 'admin/guest_list.html', context)

@login_required
def room_type_list(request, pk=None):
    action = request.GET.get('action', 'list')
    search_query = request.GET.get('search', '')
    context = {'action': action, 'search_query': search_query}

    if action == 'list':
        # Hiển thị danh sách loại phòng với phân trang
        if search_query:
            room_types = RoomType.objects.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        else:
            room_types = RoomType.objects.all()

        # Phân trang
        paginator = Paginator(room_types, 6)  # Hiển thị 6 loại phòng mỗi trang
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Lấy danh sách ảnh liên quan cho mỗi loại phòng
        for room_type in page_obj:
            room_type.images = Image.objects.filter(room_type_id=room_type.id)
        
        context['page_obj'] = page_obj
        return render(request, 'admin/room_type_list.html', context)

    elif action == 'view' and pk:
        # Hiển thị chi tiết loại phòng
        room_type = get_object_or_404(RoomType, pk=pk)
        room_type.images = Image.objects.filter(room_type_id=room_type.id)
        context['room_type'] = room_type
        return render(request, 'admin/room_type_list.html', context)
 
    elif action == 'edit' and pk:
        # Lấy dữ liệu loại phòng và hình ảnh liên quan
        room_type = get_object_or_404(RoomType, pk=pk)
        room_type.images = Image.objects.filter(room_type_id=room_type.id)

        context = {
            'action': 'edit',
            'room_type': room_type
        }

        if request.method == 'POST':
            # Lấy dữ liệu từ form
            name = request.POST.get('name')
            description = request.POST.get('description')
            base_price = request.POST.get('base_price')
            min_area = request.POST.get('min_area')
            max_area = request.POST.get('max_area')
            num_beds = request.POST.get('num_beds')
            images = request.FILES.getlist('images')
            delete_image_id = request.POST.get('delete_image_id')

            # Kiểm tra nếu có tên loại phòng trùng với loại phòng khác ngoại trừ loại phòng hiện tại
            if RoomType.objects.filter(name=name).exclude(pk=pk).exists():
                messages.error(request, 'Room type name already exists.')
                return render(request, 'admin/room_type_list.html', context)

            # Cập nhật thông tin loại phòng
            room_type.name = name
            room_type.description = description
            room_type.base_price = base_price
            room_type.min_area = min_area
            room_type.max_area = max_area
            room_type.num_beds = num_beds
            room_type.save()

            # Xóa ảnh nếu có
            if delete_image_id:
                try:
                    image_to_delete = Image.objects.get(id=delete_image_id)
                    image_to_delete.delete()
                except Image.DoesNotExist:
                    messages.error(request, 'Image to delete not found.')
                    return render(request, 'admin/room_type_list.html', context)

            # Lưu ảnh mới nếu có
            if images:
                for image_file in images:
                    Image.objects.create(room_type_id=room_type.id, image_file=image_file)

            messages.success(request, 'Room type updated successfully.')
            return redirect('room_type_list')

        return render(request, 'admin/room_type_list.html', context)

    elif action == 'delete' and pk:
        # Xóa loại phòng
        room_type = get_object_or_404(RoomType, pk=pk)
        if request.method == 'POST':
            # Xóa tất cả các ảnh liên quan đến loại phòng
            images = Image.objects.filter(room_type_id=room_type.id)
            for image in images:
                if image.image_file:
                    # Xóa ảnh khỏi hệ thống file
                    image.image_file.delete(save=False)
                image.delete()

            # Xóa loại phòng
            room_type.delete()
            
            messages.success(request, 'Room type and associated images deleted successfully')
            return redirect('room_type_list')
        
        context['room_type'] = room_type
        return render(request, 'admin/room_type_list.html', context)

    elif action == 'add':
        if request.method == 'POST':
            name = request.POST.get('name', '').strip()  # Gán giá trị mặc định
            description = request.POST.get('description', '').strip()
            base_price = request.POST.get('base_price', '').strip()
            min_area = request.POST.get('min_area', '').strip()
            max_area = request.POST.get('max_area', '').strip()
            num_beds = request.POST.get('num_beds', '').strip()
            images = request.FILES.getlist('images')

            # Kiểm tra dữ liệu nhập vào
            if not name or not base_price or not num_beds:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'admin/room_type_list.html', context)

            # Kiểm tra tên loại phòng đã tồn tại chưa
            if RoomType.objects.filter(name=name).exists():
                messages.error(request, 'Room type name already exists.')
                return render(request, 'admin/room_type_list.html', context)

            # Tạo loại phòng mới
            try:
                room_type = RoomType.objects.create(
                    name=name,
                    base_price=base_price,
                    description=description,
                    min_area=min_area,
                    max_area=max_area,
                    num_beds=num_beds,
                )

                # Lưu ảnh liên quan
                for image_file in images:
                    Image.objects.create(room_type_id=room_type.id, image_file=image_file)

                messages.success(request, 'Room type added successfully.')
                return redirect('room_type_list')

            except Exception as e:
                messages.error(request, f'Error occurred: {e}')
                return render(request, 'admin/room_type_list.html', context)

        return render(request, 'admin/room_type_list.html', context)
@login_required
def room_list(request, pk=None):
    action = request.GET.get('action', 'list')
    search_query = request.GET.get('search', '')
    branch_id = request.GET.get('branch')  # Nhận giá trị chi nhánh từ URL
    context = {'action': action, 'search_query': search_query}

    # Lấy danh sách chi nhánh để hiển thị bộ lọc
    branches = Branch.objects.all()
    context['branches'] = branches
    context['selected_branch_id'] = branch_id  # Giữ giá trị chi nhánh được chọn

    # Lọc danh sách phòng theo chi nhánh
    branch = None
    if branch_id and branch_id != 'None':  # Kiểm tra nếu branch_id có giá trị hợp lệ
        branch = get_object_or_404(Branch, pk=branch_id)
        context['branch'] = branch

    if action == 'list':
        # Hiển thị danh sách phòng
        rooms = Room.objects.all()

        if search_query:
            rooms = rooms.filter(
                Q(room_number__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(room_type__name__icontains=search_query)
            )

        if branch:
            rooms = rooms.filter(branch=branch)

        # Phân trang kết quả
        paginator = Paginator(rooms, 6)  # Hiển thị 6 phòng mỗi trang
        page_number = request.GET.get('page')  # Nhận số trang từ URL
        page_obj = paginator.get_page(page_number)

        # Gắn thêm danh sách ảnh liên quan cho từng phòng
        for room in page_obj:
            room.images = Image.objects.filter(room_id=room.id)

        context['page_obj'] = page_obj  # Truyền page_obj vào context để hiển thị phân trang
        return render(request, 'admin/room_list.html', context)

    elif action == 'view' and pk:
        # Hiển thị chi tiết phòng
        room = get_object_or_404(Room, pk=pk)
        room.images = Image.objects.filter(room_id=room.id)
        context['room'] = room
        return render(request, 'admin/room_list.html', context)

    elif action == 'edit' and pk:
        # Lấy dữ liệu phòng và hình ảnh liên quan
        room = get_object_or_404(Room, pk=pk)
        room.images = Image.objects.filter(room_id=room.id)
        room_types = RoomType.objects.all()  # Lấy tất cả các loại phòng

        context = {
            'action': 'edit',
            'room': room,
            'room_types': room_types,
        }

        if request.method == 'POST':
            # Lấy dữ liệu từ form
            room_number = request.POST.get('room_number')
            description = request.POST.get('description')
            status = request.POST.get('status')
            room_type_id = request.POST.get('room_type')
            images = request.FILES.getlist('images')
            delete_image_id = request.POST.get('delete_image_id')

            # Kiểm tra nếu số phòng trống
            if not room_number:
                messages.error(request, 'Room number cannot be empty.')
                return render(request, 'admin/room_list.html', context)

            # Kiểm tra nếu số phòng đã tồn tại trong cùng chi nhánh
            if Room.objects.filter(room_number=room_number, branch=room.branch).exclude(pk=pk).exists():
                messages.error(request, 'Room number already exists in the same branch.')
                return render(request, 'admin/room_list.html', context)

            # Cập nhật thông tin phòng
            room.room_number = room_number
            room.description = description
            room.status = status
            room.room_type_id = room_type_id
            room.save()

            # Xóa ảnh nếu có
            if delete_image_id:
                try:
                    image_to_delete = Image.objects.get(id=delete_image_id)
                    image_to_delete.delete()
                except Image.DoesNotExist:
                    messages.error(request, 'Image to delete not found.')
                    return render(request, 'admin/room_list.html', context)

            # Lưu ảnh mới nếu có
            if images:
                for image_file in images:
                    Image.objects.create(room_id=room.id, image_file=image_file)

            messages.success(request, 'Room updated successfully.')
            return redirect('room_list')

        return render(request, 'admin/room_list.html', context)

    elif action == 'delete' and pk:
        # Xóa phòng
        room = get_object_or_404(Room, pk=pk)
        if branch and room.branch != branch:
            messages.error(request, 'The room does not belong to the selected branch.')
            return redirect('room_list')

        if request.method == 'POST':
            # Xóa tất cả các ảnh liên quan đến phòng
            images = Image.objects.filter(room_id=room.id)
            for image in images:
                if image.image_file:
                    # Xóa ảnh khỏi hệ thống file
                    image.image_file.delete(save=False)
                image.delete()
            room.delete()
            messages.success(request, 'Room deleted successfully.')
            return redirect('room_list')

        context['room'] = room
        return render(request, 'admin/room_list.html', context)

    elif action == 'add':
        # Thêm phòng mới
        if request.method == 'POST':
            room_number = request.POST.get('room_number')
            description = request.POST.get('description')
            status = request.POST.get('status')
            branch_id = request.POST.get('branch')
            room_type_id = request.POST.get('room_type')
            images = request.FILES.getlist('images')

            # Kiểm tra các trường bắt buộc
            if not room_number or not branch_id or not room_type_id:
                messages.error(request, 'Please fill in all required fields.')
                context['room_types'] = RoomType.objects.all()
                context['branches'] = Branch.objects.all()
                return render(request, 'admin/room_list.html', context)

            # Kiểm tra trùng số phòng trong cùng chi nhánh
            if Room.objects.filter(room_number=room_number, branch_id=branch_id).exists():
                messages.error(request, 'Room number already exists in the same branch.')
                context['room_types'] = RoomType.objects.all()
                context['branches'] = Branch.objects.all()
                return render(request, 'admin/room_list.html', context)

            # Lấy đối tượng Branch và RoomType
            branch = get_object_or_404(Branch, pk=branch_id)
            room_type = get_object_or_404(RoomType, pk=room_type_id)

            # Tạo mới phòng
            room = Room.objects.create(
                room_number=room_number,
                description=description,
                status=status,
                branch=branch,
                room_type=room_type
            )

            # Lưu ảnh nếu có
            for image_file in images:
                Image.objects.create(room_id=room.id, image_file=image_file)  # Sửa ở đây

            messages.success(request, 'Room added successfully.')
            return redirect('room_list')

        # Nếu không phải POST, hiển thị form thêm phòng
        context['room_types'] = RoomType.objects.all()
        context['branches'] = Branch.objects.all()
        return render(request, 'admin/room_list.html', context)

    return redirect('room_list')

def service_list(request, pk=None):
    action = request.GET.get('action', 'list')
    search_query = request.GET.get('search', '')
    context = {'action': action, 'search_query': search_query}

    if action == 'list':
        # Hiển thị danh sách dịch vụ với phân trang
        if search_query:
            services = Service.objects.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        else:
            services = Service.objects.all()

        paginator = Paginator(services, 6)  # Hiển thị 6 dịch vụ mỗi trang
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Lấy danh sách ảnh liên quan cho mỗi dịch vụ
        for service in page_obj:
            service.images = Image.objects.filter(service_id=service.id)
        context['page_obj'] = page_obj
        return render(request, 'admin/service_list.html', context)

    elif action == 'view' and pk:
        # Hiển thị chi tiết dịch vụ
        service = get_object_or_404(Service, pk=pk)
        service.images = Image.objects.filter(service_id=service.id)
        context['service'] = service
        return render(request, 'admin/service_list.html', context)

    elif action == 'edit' and pk:
        # Lấy dữ liệu dịch vụ và hình ảnh liên quan
        service = get_object_or_404(Service, pk=pk)
        service.images = Image.objects.filter(service_id=service.id)
        context = {
            'action': 'edit',
            'service': service
        }

        if request.method == 'POST':
            # Cập nhật thông tin dịch vụ
            service_name = request.POST.get('service_name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            images = request.FILES.getlist('images')
            delete_image_id = request.POST.get('delete_image_id')

            # Kiểm tra trùng tên dịch vụ
            if Service.objects.filter(service_name=service_name).exclude(pk=pk).exists():
                messages.error(request, 'Service name already exists.')
                context['service'] = service
                return render(request, 'admin/service_list.html', context)

            # Cập nhật thông tin dịch vụ
            service.service_name = service_name
            service.description = description
            service.price = price
            service.save()

            # Xóa ảnh nếu có
            if delete_image_id:
                try:
                    image_to_delete = Image.objects.get(id=delete_image_id)
                    image_to_delete.delete()
                except Image.DoesNotExist:
                    messages.error(request, 'Image to delete not found.')
                    return render(request, 'admin/service_list.html', context)
            
            # Lưu ảnh mới nếu có
            if images:
                for image_file in images:
                    Image.objects.create(service_id=service.id, image_file=image_file)
            
            messages.success(request, 'Service updated successfully.')
            return redirect('service_list')

        return render(request, 'admin/service_list.html', context)


    elif action == 'delete' and pk:
        # Xóa dịch vụ
        service = get_object_or_404(Service, pk=pk)
        if request.method == 'POST':
            # Xóa tất cả các ảnh liên quan đến dịch vụ
            images = Image.objects.filter(service_id=service.id)
            for image in images:
                if image.image_file:
                    # Xóa ảnh khỏi hệ thống file
                    image.image_file.delete(save=False)
                image.delete()
            #xóa dịch vụ
            service.delete()

            messages.success(request, 'Service deleted successfully.')
            return redirect('service_list')

        context['service'] = service
        return render(request, 'admin/service_list.html', context)

    elif action == 'add':
        if request.method == 'POST':
            service_name = request.POST.get('service_name', '').strip()
            description = request.POST.get('description', '').strip()
            price = request.POST.get('price', '').strip()
            images = request.FILES.getlist('images')

            # Kiểm tra dữ liệu nhập
            if not service_name or not price:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'admin/service_list.html', context)

            # Kiểm tra tên dịch vụ trùng
            if Service.objects.filter(service_name=service_name).exists():
                messages.error(request, 'Service name already exists.')
                return render(request, 'admin/service_list.html', context)

            # Tạo mới dịch vụ
            try:
                service = Service.objects.create(
                    service_name=service_name,
                    description=description,
                    price=price
                )

                # Lưu ảnh nếu có
                for image_file in images:
                    Image.objects.create(service_id=service.id, image_file=image_file)

                messages.success(request, 'Service added successfully.')
                return redirect('service_list')
            except Exception as e:
                messages.error(request, f'Error occurred: {e}')
                return render(request, 'admin/service_list.html', context)

        return render(request, 'admin/service_list.html', context)

  