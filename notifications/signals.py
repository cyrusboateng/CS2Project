from django.db.models.signals import post_save
from django.dispatch import receiver
from technician.models import Patient
from django.contrib.auth import get_user_model
from .utils import send_notification

User = get_user_model()

@receiver(post_save, sender=Patient)
def notify_on_critical_patient_event(sender, instance, created, **kwargs):
    """
    Send notifications when a patient's condition becomes critical
    """
    if not created and instance.is_critical():  # You'll need to implement is_critical() method in Patient model
        # Notify all neurologists
        neurologists = User.objects.filter(groups__name='Neurologist')
        for neurologist in neurologists:
            send_notification(
                user=neurologist,
                notification_type='critical',
                title='Critical Patient Event',
                message=f'Patient {instance.first_name} {instance.last_name} requires immediate attention.',
                content_object=instance
            )
        
        # Notify assigned technician
        if instance.technician:
            send_notification(
                user=instance.technician,
                notification_type='critical',
                title='Critical Patient Event',
                message=f'Your patient {instance.first_name} {instance.last_name} requires immediate attention.',
                content_object=instance
            )
