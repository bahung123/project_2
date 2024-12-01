from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('room/', views.room, name='room'),
    path('room_detail/', views.room_detail, name='room_detail'),
    path('booking/', views.booking, name='booking'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('service/', views.service, name='service'),
    path('logout/', views.logout_view, name='logout'),
    path('account_info/', views.account_info, name='account_info'),
    path('update_account_info/', views.update_account_info, name='update_account_info'),
    path('change_password/', views.change_password, name='change_password'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)