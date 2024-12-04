from django.contrib import admin
from django.contrib.auth.hashers import make_password
from .models import (
    AuthGroup, AuthGroupPermissions, AuthPermission, AuthUser, 
    AuthUserGroups, AuthUserUserPermissions, Bill, Branch, 
    DjangoAdminLog, DjangoContentType, DjangoMigrations, DjangoSession, 
    Employee, Feedback, Guest, Image, Payment, Reservation, Room, 
    RoomType, Service, ServiceUsage ,ReservationRoom
)

# Tạo các ModelAdmin để đăng ký vào admin

class AuthGroupAdmin(admin.ModelAdmin):
    list_display = ('name',)

class AuthGroupPermissionsAdmin(admin.ModelAdmin):
    list_display = ('group', 'permission')

class AuthPermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'content_type', 'codename')

class AuthUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined')
    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get('password') and not obj.password.startswith('pbkdf2_'):
            obj.password = make_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)

class AuthUserGroupsAdmin(admin.ModelAdmin):
    list_display = ('user', 'group')

class AuthUserUserPermissionsAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission')

class BillAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'total_amount', 'date_issued', 'paid_status')

class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'city', 'status')

class DjangoAdminLogAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'object_repr', 'action_flag', 'change_message', 'user')

class DjangoContentTypeAdmin(admin.ModelAdmin):
    list_display = ('app_label', 'model')

class DjangoMigrationsAdmin(admin.ModelAdmin):
    list_display = ('app', 'name', 'applied')

class DjangoSessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'expire_date')

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'email', 'position', 'department', 'salary', 'hire_date', 'status')

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('guest', 'reservation', 'comment', 'rating', 'created_at')

class GuestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'email', 'address', 'id_card')

class ImageAdmin(admin.ModelAdmin):
    list_display = ('room_id', 'room_type_id', 'image_file', 'description', 'service_id')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('bill', 'amount', 'payment_date', 'payment_method', 'transaction_id')

class ReservationAdmin(admin.ModelAdmin):
    list_display = ('branch', 'guest', 'check_in_date', 'check_out_date', 'status')

class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_type', 'status', 'description')

class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'description', 'min_area', 'max_area', 'num_beds')

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('branch', 'service_name', 'price', 'description')

class ServiceUsageAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'service', 'quantity', 'date_used')
class ReservationRoomAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'room')




# Đăng ký các model vào trang admin
admin.site.register(AuthGroup, AuthGroupAdmin)
admin.site.register(AuthGroupPermissions, AuthGroupPermissionsAdmin)
admin.site.register(AuthPermission, AuthPermissionAdmin)
admin.site.register(AuthUser, AuthUserAdmin)
admin.site.register(AuthUserGroups, AuthUserGroupsAdmin)
admin.site.register(AuthUserUserPermissions, AuthUserUserPermissionsAdmin)
admin.site.register(Bill, BillAdmin)
admin.site.register(Branch, BranchAdmin)
admin.site.register(DjangoAdminLog, DjangoAdminLogAdmin)
admin.site.register(DjangoContentType, DjangoContentTypeAdmin)
admin.site.register(DjangoMigrations, DjangoMigrationsAdmin)
admin.site.register(DjangoSession, DjangoSessionAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(Guest, GuestAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(RoomType, RoomTypeAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(ServiceUsage, ServiceUsageAdmin)
admin.site.register(ReservationRoom, ReservationRoomAdmin)
