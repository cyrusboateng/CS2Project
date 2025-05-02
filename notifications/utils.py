from django.core.mail import send_mail
from django.conf import settings
from asgiref.sync import async_to_sync
from .models import Notification

def create_notification(recipient, title, message, link=None):
    """Create a notification in the database"""
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        link=link
    )
    return notification

def send_notification(user, title, message, notification_type='info'):
    """Send a notification to a user"""
    notification = create_notification(
        recipient=user,
        title=title,
        message=message
    )
    
    # Send email for critical notifications
    if notification_type == 'critical' and user.email:
        try:
            send_mail(
                subject=title,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True
            )
        except Exception as e:
            print(f"Failed to send email: {e}")
    
    return notification
