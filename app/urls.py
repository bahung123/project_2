from django.urls import path
# my_app/urls.py
from .views import (
    index, login, register, room as user_room, 
    room_detail, booking, about, contact, 
    service as user_service, logout_view, 
    account_info, update_account_info, 
    change_password, search_rooms
)
from .view.admin import (
    dashboard, employee, guest, room_type, 
    room as admin_room, service as admin_service, 
    base_admin
)

urlpatterns = [
    # User URLs
    path('', index, name='index'),
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('room/', user_room, name='room'),
    path('room_detail/', room_detail, name='room_detail'),
    path('booking/', booking, name='booking'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('service/', user_service, name='service'),
    path('logout/', logout_view, name='logout'),
    path('account_info/', account_info, name='account_info'),
    path('update_account_info/', update_account_info, name='update_account_info'),
    path('change_password/', change_password, name='change_password'),
    path('search-rooms/', search_rooms, name='search_rooms'),

    # Admin URLs
    path('base_admin/', base_admin.base_admin, name='base_admin'),
    path('base_admin/dashboard/', dashboard.dashboard, name='dashboard'),
    path('base_admin/employee/', employee.employee_list, name='employee_list'),
    path('base_admin/employee/<int:pk>/', employee.employee_list, name='employee_detail'),
    path('base_admin/guest/', guest.guest_list, name='guest_list'),
    path('base_admin/guest/<int:pk>/', guest.guest_list, name='guest_detail'),
    path('base_admin/room_type/', room_type.room_type_list, name='room_type_list'),
    path('base_admin/room_type/<int:pk>/', room_type.room_type_list, name='room_type_detail'),
    path('base_admin/room/', admin_room.room_list, name='room_list'),
    path('base_admin/room/<int:pk>/', admin_room.room_list, name='room_detail'),
    path('base_admin/service/', admin_service.service_list, name='service_list'),
    path('base_admin/service/<int:pk>/', admin_service.service_list, name='service_detail'),
]
