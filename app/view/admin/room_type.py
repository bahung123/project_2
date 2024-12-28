from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView
from app.models import RoomType, Image
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator
from urllib.parse import urlencode

@login_required 
def room_type_list(request, pk=None):
    action = request.GET.get('action', 'list')
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', '1')

    # Base context that will be used in all actions
    context = {
        'active': 'room_types',
        'action': action,
        'search_query': search_query,
        'current_page': page
    }

    if action == 'list':
        # List logic remains same
        if search_query:
            room_types = RoomType.objects.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        else:
            room_types = RoomType.objects.all()

        paginator = Paginator(room_types, 6)
        page_obj = paginator.get_page(page)

        for room_type in page_obj:
            room_type.images = Image.objects.filter(room_type_id=room_type.id)
        
        context['page_obj'] = page_obj
        return render(request, 'admin/room_type_list.html', context)

    elif action == 'add':
        if request.method == 'POST':
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            base_price = request.POST.get('base_price', '').strip()
            min_area = request.POST.get('min_area', '').strip()
            max_area = request.POST.get('max_area', '').strip()
            num_beds = request.POST.get('num_beds', '').strip()
            images = request.FILES.getlist('images')

            if not name or not base_price or not num_beds:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'admin/room_type_list.html', context)

            if RoomType.objects.filter(name=name).exists():
                messages.error(request, 'Room type name already exists.')
                return render(request, 'admin/room_type_list.html', context)

            try:
                room_type = RoomType.objects.create(
                    name=name,
                    base_price=base_price,
                    description=description,
                    min_area=min_area,
                    max_area=max_area,
                    num_beds=num_beds
                )

                for image_file in images:
                    Image.objects.create(room_type_id=room_type.id, image_file=image_file)

                messages.success(request, 'Room type added successfully.')
                # 3. Fix redirect with parameters
                base_url = reverse('room_type_list')
                params = {
                    'page': page,
                    'search': search_query or ''
                }
                url = f"{base_url}?{urlencode(params)}"
                return redirect(url)

            except Exception as e:
                messages.error(request, f'Error occurred: {str(e)}')
                return render(request, 'admin/room_type_list.html', context)

        return render(request, 'admin/room_type_list.html', context)

    elif action == 'edit' and pk:
        room_type = get_object_or_404(RoomType, pk=pk)
        room_type.images = Image.objects.filter(room_type_id=room_type.id)
        context['room_type'] = room_type

        if request.method == 'POST':
            delete_image_id = request.POST.get('delete_image_id')
            if delete_image_id:
                Image.objects.filter(id=delete_image_id, room_type_id=room_type.id).delete()
                messages.success(request, 'Image deleted successfully.')
                room_type.images = Image.objects.filter(room_type_id=room_type.id)
                return render(request, 'admin/room_type_list.html', context)

            # Update logic
            name = request.POST.get('name', '').strip()
            base_price = request.POST.get('base_price', '').strip()
            description = request.POST.get('description', '').strip()
            min_area = request.POST.get('min_area', '').strip()
            max_area = request.POST.get('max_area', '').strip()
            num_beds = request.POST.get('num_beds', '').strip()
            images = request.FILES.getlist('images')

            # Validate required fields
            if not name or not base_price or not num_beds:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'admin/room_type_list.html', context)

            try:
                # Update room type details
                room_type.name = name
                room_type.base_price = base_price
                room_type.description = description
                room_type.min_area = min_area
                room_type.max_area = max_area
                room_type.num_beds = num_beds
                room_type.save()

                # Handle new images
                for image in images:
                    Image.objects.create(room_type_id=room_type.id, image_file=image)

                messages.success(request, 'Room type updated successfully')
                # Keep current page in redirect URL
                base_url = reverse('room_type_list')
                params = {
                    'page': request.GET.get('page', '1'),  # Get page from request
                    'search': search_query,
                    'action': 'list'
                }
                url = f"{base_url}?{urlencode(params)}"
                return redirect(url)

            except Exception as e:
                messages.error(request, f'Error updating room type: {str(e)}')
                return render(request, 'admin/room_type_list.html', context)

        return render(request, 'admin/room_type_list.html', context)

    elif action == 'delete' and pk:
        room_type = get_object_or_404(RoomType, pk=pk)
        context['room_type'] = room_type
        
        if request.method == 'POST':
            # Xóa tất cả các ảnh liên quan
            images = Image.objects.filter(room_type_id=room_type.id)
            for image in images:
                if image.image_file:
                    image.image_file.delete(save=False)
                image.delete()
            room_type.delete()
            
            messages.success(request, 'Room type deleted successfully')
            base_url = reverse('room_type_list')
            params = {
                'page': page,
                'search': search_query or '',
                'action': 'list'  # Important: Set action back to list
            }
            url = f"{base_url}?{urlencode(params)}"
            return redirect(url)
        
        return render(request, 'admin/room_type_list.html', context)

    elif action == 'view' and pk:
        # Hiển thị chi tiết loại phòng
        room_type = get_object_or_404(RoomType, pk=pk)
        room_type.images = Image.objects.filter(room_type_id=room_type.id)
        context['room_type'] = room_type
        return render(request, 'admin/room_type_list.html', context)

    # Default redirect with all parameters
    base_url = reverse('room_type_list')
    params = {
        'page': page,
        'search': search_query or '',
        'action': 'list'  # Important: Set action back to list
    }
    url = f"{base_url}?{urlencode(params)}"
    return redirect(url)
