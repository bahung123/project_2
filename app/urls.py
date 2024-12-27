from django.urls import path
from .view.user.index import index 
from .view.user.login import login, logout_view
from .view.user.register import register
from .view.user.room import room
from .view.user.booking import booking, search_rooms
from .view.user.about import about
from .view.user.contact import contact
from .view.user.service import service
from .view.user.account_info import account_info, update_account_info, change_password
from .view.user.booking_history import booking_history
from .view.user.room_detail import room_detail_user
from .view.user.feedback import feedback_view

# Import admin views
from .view.admin import (
    dashboard, employee, guest, room_type, 
    room as admin_room, service as admin_service, 
    base_admin, reservation, bill, branch, service_usage, feedback
)

urlpatterns = [
    # User URLs
    path('', index, name='index'),
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('room/', room, name='room'),
    path('booking/', booking, name='booking'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('service/', service, name='service'),
    path('logout/', logout_view, name='logout'),
    path('account_info/', account_info, name='account_info'),
    path('update_account_info/', update_account_info, name='update_account_info'),
    path('change_password/', change_password, name='change_password'),
    path('search-rooms/', search_rooms, name='search_rooms'),
    path('booking-history/', booking_history, name='booking_history'),
    path('room-detail-user/<int:room_type_id>/', room_detail_user, name='room_detail_user'),
    path('feedback/<int:reservation_id>/', feedback_view, name='feedback'),

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

    # Bill URLs
    path('base_admin/bill/', bill.bill_list, name='bill_list'),
    path('base_admin/bill/<int:bill_id>/edit/', bill.bill_edit, name='bill_edit'),
    path('base_admin/bill/<int:bill_id>/delete/', bill.bill_delete, name='bill_delete'),
    path('base_admin/bill/<int:bill_id>/export/', bill.export_bill_pdf, name='bill_export'),

    # Reservation URLs
    path('base_admin/reservation/', reservation.reservation_list, name='reservation_list'),
    path('base_admin/reservation/<int:reservation_id>/', reservation.reservation_detail, name='reservation_detail'),
    path('base_admin/reservation/<int:reservation_id>/edit/', reservation.reservation_edit, name='reservation_edit'),
    path('base_admin/reservation/<int:reservation_id>/delete/', reservation.reservation_delete, name='reservation_delete'),

    # Branch URLs
    path('base_admin/branch/', branch.branch_list, name='branch_list'),
    path('base_admin/branch/<int:branch_id>/', branch.branch_detail, name='branch_detail'),

    # Service Usage URLs
    path('base_admin/service_usage/', service_usage.service_usage_list, name='service_usage_list'),
    path('base_admin/service_usage/<int:usage_id>/', service_usage.service_usage_detail, name='service_usage_detail'),

    # Feedback URLs
    path('base_admin/feedbacks/', feedback.feedback_list, name='admin_feedback_list'),
]
