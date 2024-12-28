from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from app.models import Employee, AuthUser
from django.contrib.auth.models import User  # Add this import

@login_required
def account_info_admin(request):
    user = request.user
    try:
        employee = Employee.objects.get(user_id=user.id)
    except Employee.DoesNotExist:
        employee = None

    return render(request, 'include/account_info_admin.html', {
        'user': user,
        'employee': employee,
        'active': 'account'
    })

@login_required 
def update_account_info_admin(request):
    if request.method == 'POST':
        user = AuthUser.objects.get(id=request.user.id)
        employee = Employee.objects.get(user_id=user.id)

        employee.full_name = request.POST['full_name']
        user.email = request.POST['email']
        employee.phone_number = request.POST['phone_number']
        employee.address = request.POST['address']

        user.save()
        employee.save()

        messages.success(request, 'Account information updated successfully.')
        return redirect('account_info_admin')

    return redirect('account_info_admin')

@login_required
def change_password_admin(request):
    if request.method == 'POST':
        # Use Django's User model instead of AuthUser
        user = request.user
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_new_password']

        # Use Django's authentication system to check password
        if user.check_password(old_password):
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password changed successfully.')
                return redirect('login')
            else:
                messages.error(request, 'New passwords do not match.')
        else:
            messages.error(request, 'Incorrect old password.')
    
    return redirect('account_info_admin')