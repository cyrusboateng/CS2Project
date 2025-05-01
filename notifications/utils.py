from django.core.mail import send_mail
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from twilio.rest import Client
from .models import Notification

def send_notification(user, notification_type, title, message, content_object=None):
    """
    Send notification through multiple channels:
    1. Create database notification
    2. Send WebSocket notification
    3. Send email notification
    4. Send SMS notification (if phone number available)
    """
    # Create database notification
    notification = Notification.objects.create(
        recipient=user,
        notification_type=notification_type,
        title=title,
        message=message,
        content_object=content_object
    )

    # Prepare notification data
    notification_data = {
        'id': notification.id,
        'type': notification_type,
        'title': title,
        'message': message,
        'created_at': notification.created_at.isoformat()
    }

    # Send WebSocket notification
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "notify",
            "notification": notification_data
        }
    )

    # Send email notification
    if notification_type == 'critical':
        send_mail(
            subject=title,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=True
        )

        # Send SMS if phone number is available and Twilio is configured
        if hasattr(user, 'phone_number') and settings.TWILIO_ACCOUNT_SID:
            try:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                client.messages.create(
                    body=f"{title}\n{message}",
                    from_=settings.TWILIO_FROM_NUMBER,
                    to=user.phone_number
                )
            except Exception as e:
                print(f"Failed to send SMS: {e}")

    return notification
