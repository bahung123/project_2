from django.db import models
from django.contrib.auth.models import User as AuthUser


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField(blank=True, null=True)
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class Bill(models.Model):
    reservation = models.ForeignKey('Reservation', models.DO_NOTHING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_issued = models.DateTimeField()
    paid_status = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'bill'


class Branch(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    status = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'branch'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Employee(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    branch = models.ForeignKey(Branch, models.DO_NOTHING)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(unique=True, max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True, null=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    hire_date = models.DateField()
    status = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'employee'


class Feedback(models.Model):
    guest = models.ForeignKey('Guest', models.DO_NOTHING)
    reservation = models.ForeignKey('Reservation', models.DO_NOTHING)
    comment = models.TextField()
    rating = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'feedback'


class Guest(models.Model):
    user_id = models.IntegerField(blank=True, null=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    has_account = models.IntegerField(blank=True, null=True)
    id_card = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'guest'


class Image(models.Model):
    room_id = models.IntegerField(blank=True, null=True)
    room_type_id = models.IntegerField(blank=True, null=True)
    image_file = models.ImageField(upload_to='images/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    service_id = models.IntegerField(blank=True, null=True)
    

    class Meta:
        managed = False
        db_table = 'image'


class Payment(models.Model):
    bill = models.ForeignKey(Bill, models.DO_NOTHING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField()
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'payment'

class Reservation(models.Model):
    guest = models.ForeignKey(Guest, models.DO_NOTHING)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'reservation'


class ReservationRoom(models.Model):
    reservation = models.ForeignKey(Reservation, models.DO_NOTHING)
    room = models.ForeignKey('Room', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'reservation_room'


class Room(models.Model):
    branch = models.ForeignKey(Branch, models.DO_NOTHING)
    room_number = models.CharField(unique=True, max_length=10)
    room_type = models.ForeignKey('RoomType', models.DO_NOTHING, blank=True, null=True)
    status = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'room'
        unique_together = ('room_number', 'branch')


class RoomType(models.Model):
    name = models.CharField(max_length=50)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    min_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    num_beds = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'room_type'


class Service(models.Model):
    service_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'service'


class ServiceUsage(models.Model):
    reservation = models.ForeignKey(Reservation, models.DO_NOTHING)
    service = models.ForeignKey(Service, models.DO_NOTHING, blank=True, null=True)
    quantity = models.IntegerField()
    date_used = models.DateField()

    class Meta:
        managed = False
        db_table = 'service_usage'