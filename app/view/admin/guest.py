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
def guest_list(request, pk=None):
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
        
        # Phân trang
        paginator = Paginator(guests, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
        'guests': page_obj,
        'search_query': search_query,
        'page_obj': page_obj,
    }
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

            # Kiểm tra số điện thoại trùng lặp
            if Guest.objects.filter(phone_number=phone_number).exclude(pk=guest.pk).exists():
                messages.error(request, 'Phone number already exists for another guest')
                context['guest'] = guest
                return render(request, 'admin/guest_list.html', context)

            # Kiểm tra email trùng lặp
            if Guest.objects.filter(email=email).exclude(pk=pk).exists():
                messages.error(request, 'Email already exists')
                context['guest'] = guest
                return render(request, 'admin/guest_list.html', context)

            # Kiểm tra id_card trùng lặp
            if Guest.objects.filter(id_card=id_card).exclude(pk=pk).exists():
                messages.error(request, 'Id card already exists')
                context['guest'] = guest
                return render(request, 'admin/guest_list.html', context)

            # Cập nhật AuthUser và Guest
            user.email = email
            user.save()

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
        # Xóa khách hàng và AuthUser liên kết
        guest = get_object_or_404(Guest, pk=pk)
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    if guest.user_id:
                        user = AuthUser.objects.get(pk=guest.user_id)
                        user.delete()
                    guest.delete()
                    messages.success(request, 'Guest deleted successfully')
            except Exception as e:
                messages.error(request, f"Error while deleting guest or account: {e}")
            return redirect('guest_list')

        context['guest'] = guest
        return render(request, 'admin/guest_list.html', context)

    elif action == 'add':
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            full_name = request.POST.get('full_name')
            phone_number = request.POST.get('phone_number')
            email = request.POST.get('email')
            address = request.POST.get('address')
            id_card = request.POST.get('id_card')

            # Kiểm tra trùng lặp
            if AuthUser.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
                return render(request, 'admin/guest_list.html', context)
            if Guest.objects.filter(phone_number=phone_number).exists():
                messages.error(request, 'Phone number already exists')
                return render(request, 'admin/guest_list.html', context)
            if Guest.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
                return render(request, 'admin/guest_list.html', context)
            if Guest.objects.filter(id_card=id_card).exists():
                messages.error(request, 'Id card already exists')
                return render(request, 'admin/guest_list.html', context)
            if password != confirm_password:
                messages.error(request, 'Password does not match')
                return render(request, 'admin/guest_list.html', context)

            try:
                with transaction.atomic():
                    user = AuthUser.objects.create(
                        username=username,
                        password=make_password(password),
                        email=email,
                        is_staff=0,
                        is_superuser=0,
                        is_active=1,
                        date_joined=timezone.now()
                    )
                    guest = Guest(
                        user_id=user.pk,
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
            except Exception as e:
                messages.error(request, f"Error while adding guest: {e}")
                return render(request, 'admin/guest_list.html', context)
        return render(request, 'admin/guest_list.html', context)

    # Thêm nhánh else cho action không hợp lệ
    else:
        messages.error(request, 'Invalid action')
        return redirect('guest_list')

