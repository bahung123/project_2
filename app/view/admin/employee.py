from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView
from app.models import Employee, Branch, AuthUser, Guest, RoomType, Image, Room, Service
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator

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
        
        # Phân trang
        paginator = Paginator(employees, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context={
            'employees': page_obj,
            'search_query': search_query,
            'page_obj': page_obj,
        }

        return render(request, 'admin/employee_list.html', context)

    
    elif action == 'view' and pk:
        # Hiển thị chi tiết nhân viên
        employee = get_object_or_404(Employee, pk=pk)
        context['employee'] = employee
        return render(request, 'admin/employee_list.html', context)

    elif action == 'edit' and pk:
        # Get employee and branches
        employee = get_object_or_404(Employee, pk=pk)
        user = AuthUser.objects.get(pk=employee.user_id)
        branches = Branch.objects.all()
        
        if request.method == 'POST':
            full_name = request.POST.get('full_name')
            phone_number = request.POST.get('phone_number')
            email = request.POST.get('email')
            position = request.POST.get('position')
            department = request.POST.get('department')
            salary = request.POST.get('salary')
            status = request.POST.get('status')
            branch_id = request.POST.get('branch')

            # Validation checks...
            
            # Update employee
            employee.full_name = full_name
            employee.phone_number = phone_number
            employee.email = email
            employee.position = position
            employee.department = department
            employee.salary = salary
            employee.status = status
            employee.branch_id = branch_id
            employee.save()
            
            # Update user email
            user.email = email
            user.save()
            
            messages.success(request, 'Employee updated successfully')
            return redirect('employee_list')

        context.update({
            'employee': employee,
            'branches': branches
        })
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
