import json
import logging
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.apps import apps  # Используем для получения модели после загрузки приложений
from .serializers import MessageSerializer

# Message = apps.get_model('account', 'Message')

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        logger.info(f'User connected: {self.room_name}')
        # Присоединение к группе
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()


    async def disconnect(self, close_code):
        logger.info(f"User disconnected from {self.room_group_name}")
        # Отключение от группы
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']
        logger.info(f"Received message: {message_content}")

        # Здесь мы сохраняем сообщение в базу данных
        message = await self.create_message(message_content)

        # Сериализуем сообщение
        message_data = MessageSerializer(message).data

        # Отправляем сообщение в группу
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_data
            }
        )

    async def chat_message(self, event):
        message = event['message']

        logger.info(f"Sending message to WebSocket: {message}")


        # Отправляем сообщение обратно на WebSocket
        await self.send(text_data=json.dumps({"message": message}))

    async def create_message(self, content):
        if self.scope['user'].is_anonymous:
            logger.error("Anonymous user tried to send a message.")
            return None
        try:
            # Загружаем модель Message здесь, чтобы избежать проблем с инициализацией
            Message = apps.get_model('account', 'Message')
            # Сохраняем сообщение в базу данных
            return await database_sync_to_async(Message.objects.create)(
                user=self.scope['user'],
                room_name=self.room_name,
                content=content
            )
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            await self.send(text_data=json.dumps({"error": "Failed to create message."}))
            return None
