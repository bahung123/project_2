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
