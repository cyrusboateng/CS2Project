from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Notification

class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            await self.channel_layer.group_add(
                f"user_{self.scope['user'].id}",
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        if not self.scope["user"].is_anonymous:
            await self.channel_layer.group_discard(
                f"user_{self.scope['user'].id}",
                self.channel_name
            )

    async def notify(self, event):
        """Send notification to WebSocket."""
        await self.send_json({
            "type": "notification",
            "notification": event["notification"]
        })

    async def receive_json(self, content, **kwargs):
        notification_type = content.get("type", None)
        if notification_type == "read":
            notification_id = content.get("notification_id")
            if notification_id:
                await self.mark_as_read(notification_id)

    async def mark_as_read(self, notification_id):
        await database_sync_to_async(Notification.objects.filter(id=notification_id, recipient=self.scope['user']).update)(is_read=True)
