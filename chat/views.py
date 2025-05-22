from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .models import ChatRoom, Message, UserProfile
from .forms import UserProfileForm, ChatRoomForm, UserRegistrationForm
from django.db.models import Q
from friendship.models import Friend, FriendshipRequest
from django.utils import timezone
from friendship.exceptions import AlreadyExistsError 

@login_required
def home(request):
    user_chat_rooms = ChatRoom.objects.filter(
        Q(created_by=request.user) | Q(members=request.user)
    ).distinct()
    all_chat_rooms = ChatRoom.objects.all()
    return render(request, 'chat/home.html', {
        'chat_rooms': user_chat_rooms,
        'all_chat_rooms': all_chat_rooms
    })

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            messages.success(request, 'Registration successful! You are now logged in.')
            login(request, user)  # Kullanıcıyı otomatik giriş yaptır
            return redirect('home')
        else:
            # Hataları sadece logla, kullanıcıya genel hata göster
            print('Register form errors:', form.errors)
            messages.error(request, 'Registration failed. Please check your information.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
@login_required
def profile(request):
    profile = request.user.userprofile

    if request.method == 'POST':
        profile.birth_date = request.POST.get('birth_date')
        profile.description = request.POST.get('description')
        profile.university = request.POST.get('university')
        profile.department = request.POST.get('department')
        profile.birthplace = request.POST.get('birthplace')
        profile.favorite_band = request.POST.get('favorite_band')
        profile.gender = request.POST.get('gender')
        profile.zodiac_sign = request.POST.get('zodiac_sign')

        if 'profile_photo' in request.FILES:
            profile.profile_photo = request.FILES['profile_photo']

        profile.save()
        messages.success(request, 'Profil başarıyla güncellendi.')
        return redirect('profile')

    return render(request, 'chat/profile.html')


@login_required
def chat_room(request, room_name):
    room = get_object_or_404(ChatRoom, name=room_name)
    messages = Message.objects.filter(room=room)
    return render(request, 'chat/room.html', {
        'room': room,
        'messages': messages
    })

@login_required
def create_room(request):
    if request.method == 'POST':
        form = ChatRoomForm(request.POST, user=request.user)
        if form.is_valid():
            room = form.save(commit=False)
            room.created_by = request.user
            room.save()
            
            # Add creator to members
            room.members.add(request.user)
            
            # Add selected members
            if form.cleaned_data['is_private'] and form.cleaned_data['members']:
                room.members.add(*form.cleaned_data['members'])
            
            messages.success(request, f'Chat room "{room.name}" created successfully!')
            return redirect('chat_room', room_name=room.name)
    else:
        form = ChatRoomForm(user=request.user)
    
    return render(request, 'chat/create_room.html', {'form': form})

@login_required
def user_list(request):
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')
    
    # Base queryset
    users = User.objects.exclude(id=request.user.id)
    
    # Apply search filter
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Apply user type filter
    if filter_type == 'friends':
        friends_ids = Friend.objects.friends(request.user).values_list('id', flat=True)
        users = users.filter(id__in=friends_ids)
    elif filter_type == 'following':
        following_ids = request.user.userprofile.following.values_list('user__id', flat=True)
        users = users.filter(id__in=following_ids)
    elif filter_type == 'followers':
        follower_ids = request.user.userprofile.followers.values_list('user__id', flat=True)
        users = users.filter(id__in=follower_ids)
    
    # Get friend requests and friends list
    friend_requests = Friend.objects.unread_requests(user=request.user)
    friends = Friend.objects.friends(request.user)
    
    return render(request, 'chat/user_list.html', {
        'users': users,
        'friend_requests': friend_requests,
        'friends': friends,
        'search_query': search_query,
        'filter_type': filter_type
    })

@login_required
def send_friend_request(request, user_id):
    to_user = User.objects.get(id=user_id)
    try:
        Friend.objects.add_friend(request.user, to_user)
        messages.success(request, f'Friend request sent to {to_user.username}!')
    except AlreadyExistsError:
        messages.warning(request, f'Friend request already sent to {to_user.username} or you are already friends.')
    return redirect('user_list')

@login_required
def accept_friend_request(request, request_id):
    friend_request = FriendshipRequest.objects.get(id=request_id)
    friend_request.accept()
    return redirect('user_list')

@login_required
def follow_user(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)
    profile = request.user.userprofile
    profile.following.add(user_to_follow.userprofile)
    return redirect('user_list')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Giriş denemesi - Kullanıcı adı: {username}")  # Güvenlik için şifreyi loglamıyoruz
        
        # Manuel olarak kullanıcıyı doğrulayalım
        user = authenticate(request, username=username, password=password)
        print(f"Authenticate sonucu: {user}")
        
        if user is not None:
            if user.is_active:
                login(request, user)
                print(f"Başarılı giriş: {username}")
                messages.success(request, f'Hoş geldiniz, {username}!')
                return redirect('home')
            else:
                print(f"Hesap aktif değil: {username}")
                messages.error(request, 'Hesabınız aktif değil.')
        else:
            print(f"Kullanıcı doğrulanamadı: {username}")
            messages.error(request, 'Geçersiz kullanıcı adı veya şifre.')
            
        # Form hatalarını görelim
        form = AuthenticationForm(request, data=request.POST)
        if not form.is_valid():
            print(f"Form hataları: {form.errors}")
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})

@login_required
def join_room(request, room_name):
    room = get_object_or_404(ChatRoom, name=room_name)
    if request.method == 'POST':
        room.members.add(request.user)
        messages.success(request, f'You have joined the room "{room.name}"!')
        return redirect('chat_room', room_name=room.name)
    return redirect('home')
