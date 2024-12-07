from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView
from .models import Employee, Branch, AuthUser , Guest , RoomType , Image
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.db.models import Q
from django.db import transaction


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
        # Hiển thị danh sách loại phòng
        if search_query:
            room_types = RoomType.objects.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        else:
            room_types = RoomType.objects.all()
        for room_type in room_types:
            room_type.images = Image.objects.filter(room_type_id=room_type.id)  # Lấy danh sách ảnh liên quan
        context['room_types'] = room_types
        return render(request, 'admin/room_type_list.html', context)

    elif action == 'view' and pk:
        # Hiển thị chi tiết loại phòng
        room_type = get_object_or_404(RoomType, pk=pk)
        room_type.images = Image.objects.filter(room_type_id=room_type.id)  # Lấy danh sách ảnh liên quan
        context['room_type'] = room_type
        return render(request, 'admin/room_type_list.html', context)
 
    if action == 'edit' and pk:
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

            









    
