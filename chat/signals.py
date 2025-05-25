from django.dispatch import receiver
from friendship.signals import friendship_request_created
from django.contrib.auth.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

@receiver(friendship_request_created)
def send_friend_request_notification(
    sender, instance, created, **kwargs
):
    print("Friendship request created signal received.")
    # 'instance' here is the FriendshipRequest object
    friendship_request = instance
    from_user = friendship_request.from_user
    to_user = friendship_request.to_user

    channel_layer = get_channel_layer()
    # We need to send the notification to the 'to_user'
    # Assuming you have a way to map a User to a channel name, e.g., user's ID
    # For simplicity, let's use a group name based on user ID
    group_name = f'notifications_{to_user.id}'

    print(f"Sending friend request notification to group: {group_name} from {from_user.username} to {to_user.username}")
    async_to_sync(channel_layer.groupsend)(
        group_name,
        {
            'type': 'friend_request_notification',
            'message': f'{from_user.username} sent you a friend request.',
            'from_user_id': from_user.id,
            'from_user_username': from_user.username,
        }
    ) 