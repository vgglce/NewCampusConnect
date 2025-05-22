import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ChatRoom, Message
import logging

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        logger.info(f'Yeni bağlantı isteği: {self.room_name}')
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f'Bağlantı kabul edildi: {self.room_name}')
    
    async def disconnect(self, close_code):
        logger.info(f'Bağlantı kapandı: {self.room_name}, kod: {close_code}')
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            logger.info(f'Mesaj alındı: {text_data}')
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            
            # Save message to database
            saved_message = await self.save_message(message)
            logger.info(f'Mesaj veritabanına kaydedildi: {message}')
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': self.scope['user'].id,
                    'sender_username': self.scope['user'].username,
                    'sender_full_name': self.scope['user'].get_full_name(),
                    'timestamp': saved_message.timestamp.isoformat()
                }
            )
            logger.info(f'Mesaj gruba gönderildi: {message}')
        except Exception as e:
            logger.error(f'Mesaj işlenirken hata oluştu: {str(e)}')
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Mesaj gönderilemedi.'
            }))
    
    async def chat_message(self, event):
        try:
            # Send message to WebSocket
            logger.info(f'Mesaj WebSocket\'e gönderiliyor: {event}')
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'message': event['message'],
                'user': {
                    'id': event['sender_id'],
                    'username': event['sender_username'],
                    'full_name': event['sender_full_name']
                },
                'timestamp': event['timestamp']
            }))
            logger.info('Mesaj başarıyla gönderildi')
        except Exception as e:
            logger.error(f'Mesaj gönderilirken hata oluştu: {str(e)}')
    
    @database_sync_to_async
    def save_message(self, message):
        # Check if it's a direct message room
        if self.room_name.startswith('dm_'):
            # For direct messages, we might not save to the ChatRoom model directly
            # or we might need a different saving mechanism.
            # For now, skip saving DMs to the database via this method.
            logger.info(f'Skipping database save for direct message room: {self.room_name}')
            # Return a dummy object with a timestamp for the consumer to use
            class DummyMessage:
                def __init__(self, timestamp):
                    self.timestamp = timestamp
            return DummyMessage(timezone.now())

        # Existing logic for group chat rooms
        try:
            room = ChatRoom.objects.get(name=self.room_name)
            saved_message = Message.objects.create(
                room=room,
                sender=self.scope['user'],
                content=message,
                timestamp=timezone.now(),
                is_read=False
            )
            logger.info(f'Group message saved to database for room {self.room_name}')
            return saved_message
        except ChatRoom.DoesNotExist:
            logger.error(f'ChatRoom not found for room name: {self.room_name}')
            # Handle the case where a ChatRoom is expected but not found
            # This might happen if a user tries to send a message to a non-existent group room
            return None # Indicate that saving failed

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['user'].id
        self.group_name = f'notifications_{self.user_id}'

        print(f"Notification WebSocket connecting for user: {self.user_id}, group: {self.group_name}")
        # Abone olunan gruba katıl
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Gruptan ayrıl
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"Notification WebSocket disconnected for user: {self.user_id}, code: {close_code}")

    # Gruptan gelen mesajları işle
    async def friend_request_notification(self, event):
        print(f"Received friend request notification event: {event}")
        # Bildirimi WebSocket üzerinden gönder
        await self.send(text_data=json.dumps({
            'type': 'friend_request',
            'message': event['message'],
            'from_user_id': event['from_user_id'],
            'from_user_username': event['from_user_username'],
        }))
        print("Friend request notification sent to WebSocket") 