import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, ChatMessage

class WordWolfConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'game_{self.room_id}'

        await self.accept()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        # 接続した瞬間に過去ログを取得して、このユーザーだけに送る
        messages = await self.get_past_messages()
        await self.send(text_data=json.dumps({
            'type': 'chat_log',
            'messages': messages
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data['type'] == 'chat':
            message = data.get('message')
            user = self.scope["user"]
            if message:
                await self.save_chat_message(user, message)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_broadcast',
                        'message': message,
                        'sender_name': user.username
                    }
                )
    async def chat_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_name': event['sender_name']
        }))
    @database_sync_to_async
    def save_chat_message(self, user, message):
        try:
            room = Room.objects.get(id=self.room_id)
            ChatMessage.objects.create(
                room=room,
                user=user,
                message=message
            )
        except Room.DoesNotExist:
            print(f"Error: Room {self.room_id} not found.")
    
    @database_sync_to_async
    def get_past_messages(self):
        msgs = ChatMessage.objects.filter(room_id=self.room_id).order_by('timestamp')
        return [
            {
                'sender_name': m.user.username if m.user else "システム",
                'message': m.message,
                'is_system': m.is_system
            } for m in msgs
        ]