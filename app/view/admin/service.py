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

  