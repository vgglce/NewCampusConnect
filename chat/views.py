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
def profile(request):
    profile = request.user.userprofile
    friends = Friend.objects.friends(request.user)

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

    return render(request, 'chat/profile.html', {
        'profile': profile,
        'friends': friends
    })


@login_required
def chat_room(request, room_name):
    room = get_object_or_404(ChatRoom, name=room_name)
    messages = Message.objects.filter(room=room)
    return render(request, 'chat/room.html', {
        'room': room,
        'messages': messages
    })

@login_required
def direct_message_room(request, user_id):
    # Get the target user (the friend) or return 404 if not found
    target_user = get_object_or_404(User, id=user_id)

    # Ensure the target user is a friend of the current user (optional but recommended for DMs)
    # You might want to check this here if only friends should be able to DM each other
    # from friendship.models import Friend
    # if not Friend.objects.are_friends(request.user, target_user):
    #     messages.error(request, f"You are not friends with {target_user.username}.")
    #     return redirect('profile') # Or redirect to a user list page

    # Create a unique room name for direct messages
    # Use sorted user IDs to ensure the room name is the same regardless of who initiates the chat
    user_ids = sorted([request.user.id, target_user.id])
    room_name = f'dm_{user_ids[0]}_{user_ids[1]}'

    # For direct messages, we don't necessarily need a ChatRoom model instance
    # We can directly use the generated room_name for the WebSocket connection
    # However, if you want to store direct messages like group chat messages
    # and potentially list past DM conversations, you might create/get a ChatRoom instance here.
    # For now, let's just pass the room_name and target_user to the template.

    # Fetch existing messages for this DM room if you are storing them in the Message model
    # Assuming Message model has a 'room' field which we could potentially use to store DM room names
    # Or you might need a different model/approach for DMs vs group chats
    # Let's adapt the existing structure to use room_name directly for fetching messages if possible
    # (Requires changes in Message model or consumer logic to handle DM room names)
    # For simplicity now, let's just render the template with the room name and target user.

    # You might reuse the existing chat room template or create a new one for DMs
    # Using the existing one for now:
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'target_user': target_user, # Pass target user info to display name etc.
        'room': None, # Explicitly pass room as None for DMs
        # 'messages': [] # You might load past messages here
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
        # Değişiklik: Friend.objects.friends bir QuerySet döndürmediği için ID'leri listeden alıyoruz
        friends_list = Friend.objects.friends(request.user)
        friends_ids = [friend.id for friend in friends_list]
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
    messages.success(request, 'Friend request accepted!')
    return redirect('user_list')

@login_required
def reject_friend_request(request, request_id):
    friend_request = FriendshipRequest.objects.get(id=request_id)
    friend_request.reject()
    messages.info(request, 'Friend request rejected.')
    return redirect('user_list')

@login_required
def follow_user(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)
    profile = request.user.userprofile
    profile.following.add(user_to_follow.userprofile)
    messages.success(request, f'You are now following {user_to_follow.username}!')
    return redirect('user_list')

@login_required
def remove_friend(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    Friend.objects.remove_friend(request.user, other_user)
    messages.success(request, f'{other_user.username} is no longer your friend.')
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
