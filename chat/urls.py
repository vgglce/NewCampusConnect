from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', LogoutView.as_view(next_page='/accounts/login/'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('chat/<str:room_name>/', views.chat_room, name='chat_room'),
    path('create-room/', views.create_room, name='create_room'),
    path('users/', views.user_list, name='user_list'),
    path('send-friend-request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('accept-friend-request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('follow/<int:user_id>/', views.follow_user, name='follow_user'),
    path('register/', views.register, name='register'),
    path('join-room/<str:room_name>/', views.join_room, name='join_room'),
] 